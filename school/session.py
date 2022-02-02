import html
import os
import threading

import requests
from retry import retry

import cli
import downloader
from libs.parser import Parser

from . import constants
from .loginmanager import LoginManager
from .path import Path
from .progressmanager import ProgressManager


class D2LApi:
    def __init__(self, course):
        self.api_url = f"{constants.root_url}d2l/api/le/1.50/{course.id}/"

    def get(self, path):
        return downloader.get(
            self.api_url + path,
            session=session,
            progress_callback=ProgressManager.progress.add_progress,
            skip_same_size=True,
        )[0]


class Session(requests.Session):
    def __init__(self):
        super().__init__()
        browser = (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/85.0.4183.83 Safari/537.36"
        )
        headers = {"user-agent": browser}

        self.headers.update(headers)
        self.cookies.update(Path.cookies().content)
        self.check_login()

        self.zoom_logged_in = False
        self.zoom_login_mutex = threading.Lock()

    def save_cookies(self):
        Path.cookies().content = {
            k: self.cookies.get_dict().get(k)
            for k in ["d2lSecureSessionVal", "d2lSessionVal"]
        }

    @retry(requests.exceptions.RequestException, tries=3)
    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", 10)
        return super().request(method, url, **kwargs)

    def check_login(self):
        try:
            self._check_login()
        except requests.RequestException:
            cli.run('kdialog --title School --error "No internet"')
            os._exit(0)

    def _check_login(self):
        check_url = "https://ufora.ugent.be/d2l/api/lp/1.30/users/whoami"
        logged_in = self.get(check_url, timeout=2).status_code == 200
        if not logged_in:
            cookies = LoginManager.login_ufora()

            self.cookies.update(cookies)
            self.save_cookies()

    def login_zoom(self):
        with self.zoom_login_mutex:
            if not self.zoom_logged_in:
                cookies = Path.cookies("zoom").load()
                self.cookies.update(cookies)

                logged_in = (
                    session.head("https://ugent-be.zoom.us/profile").status_code == 200
                )

                if not logged_in:
                    new_cookies = LoginManager.login_zoom()
                    Path.cookies("zoom").save(new_cookies)
                    session.cookies.update(new_cookies)

    def post_form(self, form):
        form = Parser.between(form, b"<form", b"form>")
        post_url = Parser.between(form, b'action="', b'"').decode()

        data = {}
        while b"input" in form:
            form = form[form.find(b"input") + 1 :]
            name = html.unescape(Parser.between(form, b'name="', b'"').decode())
            value = html.unescape(Parser.between(form, b'value="', b'"').decode())
            data[name] = value

        return self.post(post_url, data=data).content, post_url


session = Session()
