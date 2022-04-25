import time
from typing import Callable, Dict

from selenium.common import exceptions

from school.ui.progressmanager import ProgressManager
from school.utils import constants
from school.utils.path import Path

from .browser import Browser

login_root = "https://login.ugent.be"


def login_ufora():
    progress = ProgressManager.progress

    progress.add_message("Logging in")
    progress.auto_add_value = 0.0009
    progress.auto_max = 1
    progress.do_auto_add = True
    progress.amount = 1

    cookies = login_to_url(
        "https://ufora.ugent.be/d2l/lp/auth/saml/login?target=%2fd2l%2fep%2f6606%2fdashboard%2findex"
    )

    progress.pop_message()
    progress.auto_add_value = 0
    progress.auto_progress = 0
    progress.progress = 0
    progress.amount = 0

    return cookies


def login_zoom():
    def callback(browser):
        time.sleep(2)
        browser.find_element_by_id("onetrust-accept-btn-handler").click()
        browser.click_link_by_name("Continue")
        browser.click_and_wait("yesbutton", "yesbutton")

    login_url = "https://ugent-be.zoom.us/web/sso/login?en=signin"
    return login_to_url(login_url, callback)


def login_to_url(url: str, callback: Callable=None) -> Dict:
    with Browser() as browser:
        browser.get(login_root)
        browser.set_login_cookies()
        login(browser)

        if url.startswith("/"):
            url = login_root + url

        browser.get(url)
        if callback:
            callback(browser)

        cookies = {c["name"]: c["value"] for c in browser.get_cookies()}
        return cookies


def login(browser: Browser):
    # go to login page
    login_url = f"{login_root}/login?&authMethod=password"
    browser.get(login_url)
    browser.set_login_cookies()

    microsoft_cookies = Path.cookies("microsoft").load()
    for k, v in microsoft_cookies.items():
        browser.add_cookie({"name": k, "value": v})

    browser.get(login_url)

    login_message = "Log In Successful"
    authenticate_id = "idDiv_SAOTCAS_Title"
    authenticate_expired_id = "idA_SAASTO_Resend"
    account_id = "tilesHolder"
    account_x_path = '//*[@id="tilesHolder"]/div[1]/div'
    authenticated = False

    while login_message not in browser.page_source:
        time.sleep(0.5)
        if "Authentication source error" in browser.page_source:
            return login(browser)

        # Select first account
        if browser.is_present(account_id):
            try:
                browser.find_element_by_xpath(account_x_path).click()
            except exceptions.NoSuchElementException:
                pass
        else:
            input_credentials(browser)

        # microsoft authenticator
        if browser.is_present(authenticate_id):
            ProgressManager.progress.add_message("Awaiting authenticator")
            authenticated = True

            while browser.is_present(authenticate_id):
                if browser.is_present(authenticate_expired_id):
                    return login(browser)

                time.sleep(2)

            ProgressManager.progress.pop_message()

    # save ugent login cookies
    browser.save_login_cookies()

    if authenticated:
        cookies = browser.get_logged_cookies(".login.microsoftonline.com")
        Path.cookies("microsoft").save(cookies)


def input_credentials(browser: Browser):
    # input email, password, submit button
    inputs = {"i0116": constants.email, "i0118": constants.pw, "idSIButton9": None}
    ignored_exceptions = (
        exceptions.ElementNotInteractableException,
        exceptions.StaleElementReferenceException,
        exceptions.NoSuchElementException,
    )
    browser.fill_in(inputs, add_enter=False, ignored_exceptions=ignored_exceptions)
