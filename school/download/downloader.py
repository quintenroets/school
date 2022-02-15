import re
import threading
import urllib.parse

import m3u8
import requests

import downloader
from libs.threading import Threads
from school.clients.session import session
from school.clients.zoomapi import ZoomApi
from school.content.contentmanager import Item, SectionInfo
from school.utils import constants, timeparser
from school.utils.path import Path

from .downloadmanager import DownloadManager
from .downloadprogress import DownloadProgress

PARALLEL_SECTIONS = 1  # 5
PARALLEL_DOWNLOADS = 1  # 10


class Downloader:
    section_semaphore = threading.Semaphore(PARALLEL_SECTIONS)
    semaphore = threading.Semaphore(PARALLEL_DOWNLOADS)

    def __init__(self, section: SectionInfo):
        self.section: SectionInfo = section

    def download_section(self):
        self.section.downloadprogress = DownloadProgress(self.section)
        with Downloader.section_semaphore:
            self.start_download()
            self.section.downloadprogress.enable_show()

    def start_download(self):
        if self.section.announ:
            self.download_html(self.section.items[0])
        else:
            self.section.downloadprogress.add_amount(len(self.section.items))
            Threads(self.download_item, args=(self.section.items,)).start().join()

        DownloadManager.process_downloads(self.section)

    def download_html(self, item: Item):
        style = f'<link href="file:///{Path.templates}/announ.css" rel="stylesheet" />'

        url = constants.root_url

        base = f'<base href="{url}">'
        title = f"<br><h1>{self.section.coursemanager.course.name}</h1><hr>"

        content = style + base + title + item.html_content
        dest = item.dest if not self.section.announ else self.section.dest
        dest.text = content  # encoding="utf-8" if this does not work

    def download_item(self, item: Item):
        if item.html_content is not None:
            self.download_html(item)
        elif self.section.zoom:
            self.download_zoom_api(item)
        elif item.toc_info and item.toc_info.TypeIdentifier == "File":
            self.download_stream(item, constants.root_url + item.url)
        elif "zoom" in item.url:
            self.download_zoom(item)
        elif "quickLink" in item.url or "ictooce" in item.url:
            self.download_external(item)
        else:
            self.download_as_url(item)

    def download_external(self, item):
        url = item.url
        url = url.replace(
            "http://ictooce.ugent.be/engage/ui/view.html",
            "https://opencast.ugent.be/paella/ui/watch.html",
        )
        if not url.startswith("http"):
            url = constants.root_url + url

        content = session.get(url).content
        ugent_urls = [b"https://opencast.ugent.be", b"https://vidlib.ugent.be"]
        url = None
        if b"<form" in content:
            for u in ugent_urls:
                if u in content:
                    url = u.decode()
        if url:
            self.download_opencast(item, content, url)
        elif "ictooce" in item.url and False:
            self.download_opencast(item, content, item.url)
        else:
            self.download_as_url(item)

    def download_as_url(self, item):
        url = constants.root_url + item.url if item.url.startswith("/") else item.url
        item.dest = item.dest.with_suffix(".html")
        content = f"<script>window.location.href = '{url}';</script>"
        item.dest.write(content)

    def download_zoom(self, item: Item):
        item.dest = item.dest.with_suffix(".mp4")

        session.login_zoom()
        zoom_page = session.get(item.url).text

        if "Passcode Required" in zoom_page:
            item.title = None
            return

        match = re.search("clipStartTime: (.*),", zoom_page)
        if match:
            time_str = match.group(1)
            if len(time_str) > 3:
                item.mtime = int(time_str[:-3])

        content_list = zoom_page.split("'")
        urls = [u for u in content_list if ".mp4" in u]
        headers = {"Referer": "https://ugent-be.zoom.us/"}

        self.download_urls(item, urls, headers=headers)

    def download_opencast(self, item, content, base_url: str = None):
        item.dest = item.dest.with_suffix(".mp4")

        if base_url is None:
            base_url = b"https://opencast.ugent.be"

        if "ictooce" not in base_url:
            video_id = (
                re.search('custom_tool" value="(.*)"', content).group(1).split("/")[-1]
            )
            session.post_form(content)  # log in to paella
        else:
            video_id = re.search("id=(.*)", item.url).group(1)

        url = f"{base_url}/search/episode.json?id=" + video_id
        response = session.get(url)
        parsed_content = response.json()

        time = parsed_content["search-results"]["result"]["mediapackage"]["start"]
        item.time = timeparser.parse(time, "%Y-%m-%dT%H:%M:%SZ")

        match = re.search("http.*COMPOSITION.mp4", response.text)
        if match:
            urls = [match.group()]
        else:
            tracks = parsed_content["search-results"]["result"]["mediapackage"][
                "media"
            ]["track"]
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
            dests = [
                item.dest.with_stem(item.dest.stem + f"_view{i+1}")
                for i in range(len(urls))
            ]
            self.section.downloadprogress.amount += len(urls) - 1
            Threads(
                self.download_chunked, args=(dests, urls), kwargs=kwargs
            ).start().join()

    def download_zoom_api(self, item: Item):
        info = ZoomApi.tokens[self.section.coursemanager.course.id]
        url = (
            "https://applications.zoom.us/api/v1/lti/rich/recording/file?meetingId="
            f"{urllib.parse.quote(item.recording_info.meetingId, safe='')}"
            f"&lti_scid={info['scid']}"
        )

        response = requests.get(url, headers=info["headers"]).json()
        recordings = response["result"]["recordingFiles"]
        recordings = [r for r in recordings if r["fileType"] == "MP4"]

        for r in recordings:
            mtime = r.get("recordingStart")
            r["time"] = timeparser.parse(mtime, "%Y-%m-%d %H:%M:%S")
        recordings = sorted(recordings, key=lambda r: r["time"])

        if len(recordings) > 1:

            items = []
            for i, r in enumerate(recordings):
                new_item = Item(
                    order=item.order,
                    mtime=r["time"],
                    title=item.title + f" - Part {i + 1}",
                    url=r["playUrl"],
                )
                items.append(new_item)
            self.section.items.remove(item)
            self.section.items += items

        else:
            r = recordings[0]
            item.mtime = r["time"]
            item.url = r["playUrl"]
            items = [item]

        for item in items:
            self.download_zoom(item)

    def download_stream(self, item: Item, url, headers=None, **kwargs):
        self.download_chunked(item.dest, url, headers, **kwargs)

        if item.dest.suffix == ".html":
            item.html_content = item.dest.text
            self.download_html(item)

    def progress_callback(self, value):
        self.section.downloadprogress.add_progress(0.95 * value)

    def download_chunked(self, dest, url, headers=None, **kwargs):
        dest = Path(dest)
        if constants.overwrite_downloads or not dest.exists():
            with Downloader.semaphore:

                if url.endswith(".m3u8"):
                    self.download_m3u8(dest, url, headers=headers, **kwargs)
                else:
                    downloader.download(
                        url,
                        dest,
                        headers=headers,
                        session=session,
                        progress_callback=self.progress_callback,
                        **kwargs,
                    )

    def download_m3u8(self, dest, url, headers=None, callback=None, **kwargs):
        headers = headers or {}
        playlist = m3u8.load(url, headers=headers)
        playlist = m3u8.load(playlist.playlists[0].absolute_uri, headers=headers)

        from downloader.progress import UIProgress

        progress = UIProgress(
            dest.name, total=len(playlist.segments) * 2 ** 20
        )  # assume 1 MB per chunk

        with progress:
            with dest.open("wb") as fp:
                for segment in playlist.segments:
                    content = session.get(segment.absolute_uri, headers=headers).content

                    progress.advance(2 ** 20)
                    fp.write(content)
                    self.progress_callback(1 / len(playlist.segments))

        # run: ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4
        # manually afterward to be able to play it in the browser
