import html
import os
import threading

import cli
import downloader
import requests
from libs.parser import Parser
from retry import retry

from school.ui.progressmanager import ProgressManager
from school.utils import constants
from school.utils.path import Path

from . import loginmanager


class D2LApi:
    def __init__(self, course):
        self.api_url = f"{constants.root_url}d2l/api/le/1.50/{course.id}/"

    def get(self, path):
        return downloader.get(
            self.api_url + path,
            session=session,
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

    @retry(requests.RequestException, tries=3)
    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", 10)
        return super().request(method, url, **kwargs)

    @retry(requests.RequestException, delay=2 * 60**2)
    def check_login(self):
        try:
            self._check_login()
        except requests.RequestException as e:
            if ProgressManager.interactive_mode:
                self.show_error()
            else:
                raise e

    @classmethod
    def show_error(cls):
        cli.run('kdialog --title School --error "No internet"')
        os._exit(0)

    def _check_login(self):
        check_url = "https://ufora.ugent.be/d2l/api/lp/1.30/users/whoami"
        logged_in = self.get(check_url, timeout=2).status_code == 200
        if not logged_in:
            cookies = loginmanager.login_ufora()

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
                    new_cookies = loginmanager.login_zoom()
                    Path.cookies("zoom").save(new_cookies)
                    session.cookies.update(new_cookies)

    def post_form(self, form: str):
        form = Parser.between(form, "<form", "form>")
        post_url = Parser.between(form, 'action="', '"')

        data = {}
        while "input" in form:
            form = form[form.find("input") + 1 :]
            name = html.unescape(Parser.between(form, 'name="', '"'))
            value = html.unescape(Parser.between(form, 'value="', '"'))
            data[name] = value

        return self.post(post_url, data=data).content, post_url


session = Session()
