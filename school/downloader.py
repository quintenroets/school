from datetime import datetime
import downloader
import json
import m3u8
import requests
import threading
from tqdm import tqdm
import urllib

from libs.threading import Threads
from libs.parser import Parser

from . import constants
from .contentmanager import Item, Section
from .downloadmanager import DownloadManager
from .downloadprogress import DownloadProgress
from .sessionmanager import SessionManager
from .zoomapi import ZoomApi

from .path import Path
from . import timeparser

PARALLEL_SECTIONS = 5
PARALLEL_DOWNLOADS = 10


class Downloader:
    section_semaphore = threading.Semaphore(PARALLEL_SECTIONS)
    semaphore = threading.Semaphore(PARALLEL_DOWNLOADS)

    def __init__(self, section: Section):
        self.section = section

    def download_section(self):
        self.section.downloadprogress = DownloadProgress(self.section)
        with Downloader.section_semaphore:
            self.start_download()
            self.section.downloadprogress.enable_show()

    def start_download(self):
        if self.section.announ:
            self.download_announ()
        else:
            self.section.downloadprogress.add_amount(len(self.section.items))
            Threads(self.download_item, self.section.items).join()

        DownloadManager.process_downloads(self.section)

    def download_announ(self, item=None):
        if item:
            html = item.html
        else:
            content_list = []
            for it in self.section.coursemanager.contentmanager.content:
                title = it["Title"]
                time = timeparser.parse(it['StartDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
                time_string = timeparser.to_string(time)
                html = it['Body']['Html']
                content_list.append(f"<h3><strong>{title}</strong><small>&ensp;&ensp;{time_string}</small></h3>{html}")
            
            html = "<br><hr>".join(content_list)

        style = f'<link href="file:///{Path.templates}/announ.css" rel="stylesheet" />'

        url = constants.root_url
        if item:
            if hasattr(item, "Url"):
                url += item.Url
            elif hasattr(item, "DefaultPath"):
                url += item.DefaultPath

        base = f'<base href="{url}">'
        title = f'<br><h1>{self.section.coursemanager.course.name}</h1><hr>'

        content = base + title + html + style
        if item:
            dest = item.dest
        else:
            self.section.dest = self.section.dest.with_suffix(".html")
            dest = self.section.dest
        Path(dest).write(content)  # encoding="utf-8" if this does not work

    def download_item(self, item):
        if item.html:
            self.download_announ(item)
        elif self.section.zoom:
            self.download_zoom_api(item)
        elif item.TypeIdentifier == "File":
            self.download_stream(item, constants.root_url + item.Url)
        elif "zoom" in item.Url:
            self.download_zoom(item)
        elif "quickLink" in item.Url:
            self.download_external(item)
        else:
            self.download_as_url(item)

    def download_external(self, item):
        url = item.Url
        url = url.replace("http://ictooce.ugent.be/engage/ui/view.html", "https://opencast.ugent.be/paella/ui/watch.html")
        if not url.startswith("http"):
            url = constants.root_url + url
        content = SessionManager.get(url).content
        ugent_urls = [b"https://opencast.ugent.be", b"https://vidlib.ugent.be"]
        url = None
        if b"<form" in content:
            for u in ugent_urls:
                if u in content:
                    url = u
        if url:
            self.download_opencast(item, content, url)
        else:
            self.download_as_url(item)

    def download_as_url(self, item):
        url = constants.root_url + item.Url if item.Url.startswith("/") else item.Url
        item.dest = item.dest.with_suffix(".html")
        content = f"<script>window.location.href = '{url}';</script>"
        item.dest.write(content)

    def download_zoom(self, item):
        item.dest = item.dest.with_suffix(".mp4")

        SessionManager.login_zoom()
        zoom_page = SessionManager.session.get(item.Url).text

        if "Passcode Required" in zoom_page:
            item.dest = None
            return

        time_string = Parser.between(zoom_page, "clipStartTime: ", ",")
        if time_string:
            item.LastModifiedDate = timeparser.parse(time_string[:-3])

        content_list = zoom_page.split("'")
        urls = [u for u in content_list if ".mp4" in u]
        headers = {"Referer": "https://ugent-be.zoom.us/"}

        self.download_urls(item, urls, headers=headers)

    def download_opencast(self, item, content, base_url=None):
        item.dest = item.dest.with_suffix(".mp4")

        if base_url is None:
            base_url = b"https://opencast.ugent.be"

        video_id = Parser.between(content, b'custom_tool" value="', b'"').decode().split("/")[-1]
        SessionManager.post_form(content) # log in to paella

        url = f"{base_url.decode()}/search/episode.json?id=" + video_id
        r = SessionManager.get(url)
        content = r.content
        parsed_content = r.json()

        time = parsed_content["search-results"]["result"]["mediapackage"]["start"]
        item.LastModifiedDate = timeparser.parse(time, "%Y-%m-%dT%H:%M:%SZ")

        if b"COMPOSITION.mp4" in content:
            urls = ["http" + Parser.rbetween(content, b"http", b"COMPOSITION.mp4").decode() + "COMPOSIION.mp4"]
        else:
            tracks = parsed_content["search-results"]["result"]["mediapackage"]["media"]["track"]
            new_tracks = {}
            for t in tracks:
                key = t["type"].split("/")[0]
                if key not in new_tracks:
                    new_tracks[key] = t
            
            if "composite" in new_tracks:
                tracks = [new_tracks["composite"]]
            else:
                tracks = list(new_tracks.values())
            
            urls = [track["url"] for track in tracks]

        if urls:
            self.download_urls(item, urls)

    def download_urls(self, item: Item, urls, **kwargs):
        if len(urls) == 1:
            self.download_stream(item, urls[0], **kwargs)
        else:
            dests = [item.dest.with_stem(item.dest.stem + f"_view{i+1}") for i in range(len(urls))]
            self.section.downloadprogress.amount += len(urls) - 1
            Threads(self.download_chunked, dests, urls, **kwargs).join()

    def download_zoom_api(self, item):

        info = ZoomApi.tokens[self.section.coursemanager.course.id]
        url = (
            "https://applications.zoom.us/api/v1/lti/rich/recording/file?meetingId="
            f"{urllib.parse.quote(item.meetingId, safe='')}"
            "&lti_scid={info['scid']"
        )
        r = requests.get(url, headers=info["headers"])
        recordings = json.loads(r.content)["result"]["recordingFiles"]
        recordings = [r for r in recordings if r["fileType"] == "MP4"]
        for r in recordings:
            mtime = r.get("recordingStart")
            r["time"] = timeparser.parse(mtime, "%Y-%m-%d %H:%M:%S")
        recordings = sorted(recordings, key=lambda r: r["time"])

        extra_items = [item.__copy__() for i in range(len(recordings) - 1)]
        self.section.items += extra_items
        items = [item] + extra_items

        for item, recording in zip(items, recordings):
            item.Url = recording["playUrl"]
            item.time = recording["time"]

        if len(items) > 1:
            for i, item in enumerate(items):
                item.dest += f" - Part {i + 1}"

        for item in items:
            self.download_zoom(item)

    def download_stream(self, item, url, headers=None, **kwargs):
        self.download_chunked(item.dest, url, headers, **kwargs)

        if item.dest.suffix == ".zip":
            item.dest = item.dest.with_suffix("")
            DownloadManager.extract_zip(item.dest.with_suffix(".zip"), item.dest, remove_zip=True)

        if item.dest.suffix == ".html":
            item.html = item.dest.read_text()
            self.download_announ(item)

    def download_chunked(self, dest, url, headers=None, **kwargs):
        dest = Path(dest)
        if constants.overwrite_downloads or not dest.exists():
            with Downloader.semaphore:
                if url.endswith(".m3u8"):
                    self.download_m3u8(dest, url, headers=headers, **kwargs)
                else:
                    def callback(p):
                        self.section.downloadprogress.add_progress(0.95 * p)
                    downloader.download(
                        url, dest, headers=headers, session=SessionManager.session, progress_callback=callback, **kwargs
                        )

    def download_m3u8(self, dest, url, headers=None, **kwargs):
        if headers is None:
            headers = {}
        playlist = m3u8.load(url, headers=headers)
        playlist = m3u8.load(playlist.playlists[0].absolute_uri, headers=headers)

        progress = tqdm(
            desc=f"Downloading {dest.name}",
            unit="B",
            unit_scale=True,
            leave=False,
            unit_divisor=1024,
            dynamic_ncols=True,
            bar_format='{l_bar}{bar}| {n_fmt}B/{total_fmt}B [{elapsed}<{remaining}, ' '{rate_fmt}{postfix}]'
        )

        with progress:
            with dest.open("wb") as fp:
                for segment in playlist.segments:
                    content = SessionManager.session.get(segment.absolute_uri, headers=headers).content
                    progress.update(len(content))
                    fp.write(content)
                    self.section.downloadprogress.add_progress(0.95 / len(playlist.segments))
                    if progress.total is None:
                        progress.total = len(content) * len(playlist.segments)
