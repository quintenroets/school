import json
import time
from http.cookies import SimpleCookie

from retry import retry
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoSuchElementException,
                                        StaleElementReferenceException)

from libs.browser import Browser
from libs.parser import Parser

from . import constants
from .path import Path
from .progressmanager import ProgressManager


class LoginManager:
    @staticmethod
    def login_ufora():
        ProgressManager.progress.add_message("Logging in")
        ProgressManager.progress.auto_add_value = 0.0009
        ProgressManager.progress.auto_max = 1
        ProgressManager.progress.do_auto_add = True
        ProgressManager.progress.amount = 1

        cookies = LoginManager.login_to_url(
            "https://ufora.ugent.be/d2l/lp/auth/saml/login?target=%2fd2l%2fep%2f6606%2fdashboard%2findex"
        )

        ProgressManager.progress.pop_message()
        ProgressManager.progress.auto_add_value = 0
        ProgressManager.progress.auto_progress = 0
        ProgressManager.progress.set_progress(0)
        ProgressManager.progress.amount = 0

        return cookies

    @staticmethod
    def login_zoom():
        def callback(browser):
            time.sleep(2)
            browser.find_element_by_id("onetrust-accept-btn-handler").click()
            browser.click_link_by_name("Continue")
            LoginManager.click_and_wait(browser, "yesbutton", "yesbutton")

        login_url = "https://ugent-be.zoom.us/web/sso/login?en=signin"
        return LoginManager.login_to_url(login_url, callback)

    @staticmethod
    def login_to_url(url, callback=None):
        with Browser(logging=True) as browser:
            browser.get("https://login.ugent.be")
            LoginManager.set_login_cookies(browser)
            LoginManager.login(browser)

            if url.startswith("/"):
                url = "https://login.ugent.be" + url

            browser.get(url)
            if callback:
                callback(browser)

            cookies = {c["name"]: c["value"] for c in browser.get_cookies()}
            return cookies

    @staticmethod
    def set_login_cookies(browser):
        domain = browser.domain
        cookies = Path.cookies(browser.domain_name).content
        for cookie in cookies:
            if domain in cookie["domain"]:
                browser.add_cookie(cookie)

    @staticmethod
    def save_login_cookies(browser):
        Path.cookies(browser.domain_name).content = browser.get_cookies()

    @staticmethod
    def login(browser):
        # go to login page
        browser.get("https://login.ugent.be/login?&authMethod=password")

        LoginManager.set_login_cookies(browser)
        microsoft_cookies = Path.cookies("microsoft").load()
        for k, v in microsoft_cookies.items():
            browser.add_cookie({"name": k, "value": v})

        browser.get("https://login.ugent.be/login?&authMethod=password")

        login_message = "Log In Successful"
        inputs = {"i0116": constants.email, "i0118": constants.pw, "idSIButton9": None}
        authenticate_id = "idDiv_SAOTCAS_Title"
        authenticate_expired_id = "idA_SAASTO_Resend"
        account_id = "tilesHolder"
        account_x_path = '//*[@id="tilesHolder"]/div[1]/div'
        authenticated = False

        while login_message not in browser.page_source:
            time.sleep(0.5)
            if "Authentication source error" in browser.page_source:
                return LoginManager.login(browser)

            # Select first account
            if LoginManager.is_present(browser, account_id):
                try:
                    browser.find_element_by_xpath(account_x_path).click()
                except NoSuchElementException:
                    pass

            # input email, password, submit button
            for id_, value in inputs.items():
                try:
                    input_element = browser.find_element_by_id(id_)
                    if value is None:
                        input_element.click()
                    elif not input_element.get_property("value"):  # don't fill in twice
                        input_element.send_keys(value)
                except (
                    ElementNotInteractableException,
                    StaleElementReferenceException,
                    NoSuchElementException,
                ):
                    pass

            # microsoft authenticator
            if LoginManager.is_present(browser, authenticate_id):
                ProgressManager.progress.add_message("Awaiting authenticator")
                authenticated = True

                while LoginManager.is_present(browser, authenticate_id):
                    if LoginManager.is_present(browser, authenticate_expired_id):
                        return LoginManager.login(browser)

                    time.sleep(2)

                ProgressManager.progress.pop_message()

        # save ugent login cookies
        LoginManager.save_login_cookies(browser)

        if authenticated:
            cookies = LoginManager.get_cookies(browser, ".login.microsoftonline.com")
            Path.cookies("microsoft").save(cookies)

    @staticmethod
    def get_cookies(browser, url):
        logs = browser.get_log("performance")
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

    @staticmethod
    def is_present(browser, id):
        try:
            browser.find_element_by_id(id)
        except NoSuchElementException:
            present = False
        else:
            present = True
        return present

    @staticmethod
    @retry(AssertionError, delay=0.2)
    # used for callbacks
    def click_and_wait(driver, id_click, id_wait):
        driver.find_element_by_id(id_click).click()
        assert not LoginManager.is_present(driver, id_click)
