import json
from http.cookies import SimpleCookie

from retry import retry

from libs.browser import Browser as BaseBrowser
from libs.parser import Parser
from school.utils.path import Path


class Browser(BaseBrowser):
    def __init__(self):
        super().__init__(headless=True, logging=True)

    def set_login_cookies(self):
        domain = self.domain
        cookies = Path.cookies(self.domain_name).content
        for cookie in cookies:
            if domain in cookie["domain"]:
                self.add_cookie(cookie)

    def save_login_cookies(self):
        Path.cookies(self.domain_name).content = self.get_cookies()

    def get_logged_cookies(self, url):
        logs = self.get_log("performance")
        cookies_info = [
            json.loads(l["message"])["message"]
            .get("params", {})
            .get("headers", {})
            .get("Set-Cookie", {})
            for l in logs
            if "Received" in l["message"]
        ]

        cookies = {}
        for info in cookies_info:
            if info:
                domain = Parser.between(info, "domain=", ";")
                if domain == url:
                    cookie = SimpleCookie()
                    cookie.load(info)

                    for k, morsel in cookie.items():
                        cookies[k] = morsel.value

        return cookies

    @retry(AssertionError, delay=0.2)
    # used for callbacks
    def click_and_wait(self, id_click, id_wait):
        self.find_element_by_id(id_click).click()
        assert not self.is_present(id_click)
