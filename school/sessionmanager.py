import html
import os
import threading
import time

import requests

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
            session=SessionManager.session,
            progress_callback=ProgressManager.progress.add_progress,
            skip_same_size=True,
        )[0]


class SessionManager:
    zoom_login_mutex = threading.Lock()
    session = requests.Session()

    @staticmethod
    def get(url, *args, timeout=10, **kwargs):
        return SessionManager.session.get(url, *args, **kwargs, timeout=timeout)

    @staticmethod
    def startup():
        cookies = Path.cookies().load()  # otherwise api content changes as well
        SessionManager.session.cookies.update(cookies)
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/85.0.4183.83 Safari/537.36"
        )
        # better safe than sorry
        SessionManager.session.headers = {"User-Agent": user_agent}
        try:
            SessionManager.check_login()
        except requests.RequestException:
            cli.run('kdialog --title School --error "No internet"')
            os._exit(0)

    @staticmethod
    def check_login():
        check_url = "https://ufora.ugent.be/d2l/api/lp/1.30/users/whoami"
        logged_in = SessionManager.get(check_url, timeout=2).status_code == 200
        if not logged_in:
            SessionManager.login()

    @staticmethod
    def login():
        ProgressManager.progress.add_message("Logging in")
        ProgressManager.progress.auto_add_value = 0.0009
        ProgressManager.progress.auto_max = 1
        ProgressManager.progress.do_auto_add = True
        ProgressManager.progress.amount = 1

        SessionManager.start_login()

        ProgressManager.progress.pop_message()
        ProgressManager.progress.auto_add_value = 0
        ProgressManager.progress.auto_progress = 0
        ProgressManager.progress.set_progress(0)
        ProgressManager.progress.amount = 0

    @staticmethod
    def start_login():
        from .loginmanager import LoginManager  # cyclic dependency

        # more lightweight to visit than root url
        login_url = "https://ufora.ugent.be/d2l/lp/auth/saml/login?target=%2fd2l%2fep%2f6606%2fdashboard%2findex"
        cookies = LoginManager.login_to_url(login_url)
        SessionManager.session.cookies.update(cookies)
        cookies_save = {
            k: cookies.get(k) for k in ["d2lSecureSessionVal", "d2lSessionVal"]
        }
        Path.cookies().save(cookies_save)

    @staticmethod
    def login_zoom():
        with SessionManager.zoom_login_mutex:
            cookies = Path.cookies("zoom").load()
            SessionManager.session.cookies.update(cookies)

            logged_in = (
                SessionManager.session.head(
                    "https://ugent-be.zoom.us/profile"
                ).status_code
                == 200
            )
            if not logged_in:
                new_cookies = SessionManager._login_zoom()
                Path.cookies("zoom").save(new_cookies)
                SessionManager.session.cookies.update(new_cookies)

    @staticmethod
    def _login_zoom():
        def callback(browser):
            time.sleep(2)
            browser.find_element_by_id("onetrust-accept-btn-handler").click()
            browser.click_link_by_name("Continue")
            LoginManager.click_and_wait(browser, "yesbutton", "yesbutton")

        login_url = "https://ugent-be.zoom.us/web/sso/login?en=signin"
        return LoginManager.login_to_url(login_url, callback)

    @staticmethod
    def post_form(form):
        form = Parser.between(form, b"<form", b"form>")
        post_url = Parser.between(form, b'action="', b'"').decode()

        data = {}
        while b"input" in form:
            form = form[form.find(b"input") + 1 :]
            name = html.unescape(Parser.between(form, b'name="', b'"').decode())
            value = html.unescape(Parser.between(form, b'value="', b'"').decode())
            data[name] = value

        return SessionManager.session.post(post_url, data=data).content, post_url


SessionManager.startup()
