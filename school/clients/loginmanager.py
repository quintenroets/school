import time

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
)

from school.ui.progressmanager import ProgressManager
from school.utils import constants
from school.utils.path import Path

from .browser import Browser


class LoginManager:
    @staticmethod
    def login_ufora():
        progress = ProgressManager.progress

        progress.add_message("Logging in")
        progress.auto_add_value = 0.0009
        progress.auto_max = 1
        progress.do_auto_add = True
        progress.amount = 1

        cookies = LoginManager.login_to_url(
            "https://ufora.ugent.be/d2l/lp/auth/saml/login?target=%2fd2l%2fep%2f6606%2fdashboard%2findex"
        )

        progress.pop_message()
        progress.auto_add_value = 0
        progress.auto_progress = 0
        progress.progress = 0
        progress.amount = 0

        return cookies

    @staticmethod
    def login_zoom():
        def callback(browser):
            time.sleep(2)
            browser.find_element_by_id("onetrust-accept-btn-handler").click()
            browser.click_link_by_name("Continue")
            browser.click_and_wait("yesbutton", "yesbutton")

        login_url = "https://ugent-be.zoom.us/web/sso/login?en=signin"
        return LoginManager.login_to_url(login_url, callback)

    @staticmethod
    def login_to_url(url, callback=None):
        with Browser() as browser:
            browser.get("https://login.ugent.be")
            browser.set_login_cookies()
            LoginManager.login(browser)
            print("klaar")

            if url.startswith("/"):
                url = "https://login.ugent.be" + url

            browser.get(url)
            if callback:
                callback(browser)

            cookies = {c["name"]: c["value"] for c in browser.get_cookies()}
            return cookies

    @staticmethod
    def login(browser: Browser):
        # go to login page
        browser.get("https://login.ugent.be/login?&authMethod=password")
        browser.set_login_cookies()

        microsoft_cookies = Path.cookies("microsoft").load()
        for k, v in microsoft_cookies.items():
            browser.add_cookie({"name": k, "value": v})

        browser.get("https://login.ugent.be/login?&authMethod=password")

        login_message = "Log In Successful"
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
            if browser.is_present(account_id):
                try:
                    browser.find_element_by_xpath(account_x_path).click()
                except NoSuchElementException:
                    pass
            else:
                LoginManager.input_credentials(browser)

            # microsoft authenticator
            if browser.is_present(authenticate_id):
                ProgressManager.progress.add_message("Awaiting authenticator")
                authenticated = True

                while browser.is_present(authenticate_id):
                    if browser.is_present(authenticate_expired_id):
                        return LoginManager.login(browser)

                    time.sleep(2)

                ProgressManager.progress.pop_message()

        # save ugent login cookies
        browser.save_login_cookies()

        if authenticated:
            cookies = browser.get_logged_cookies(".login.microsoftonline.com")
            Path.cookies("microsoft").save(cookies)

    @staticmethod
    def input_credentials(browser: Browser):
        # input email, password, submit button
        inputs = {"i0116": constants.email, "i0118": constants.pw, "idSIButton9": None}

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
