import json
import time
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
from http.cookies import SimpleCookie

from libs.browser import Browser
from libs.parser import Parser

from . import constants
from .progressmanager import ProgressManager
from .path import Path


class LoginManager:
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
        domain = browser.current_url.replace("https://", "").split("/")[0]
        name = domain.replace(".", "_")
        browser_cookies = Path.cookies(name).load()
        for cookie in browser_cookies:
            if domain in cookie["domain"]:
                browser.add_cookie(cookie)

    @staticmethod
    def save_login_cookies(browser):
        name = browser.current_url.replace("https://", "").split("/")[0].replace(".", "_")
        browser_cookies = browser.get_cookies()
        Path.cookies(name).save(browser_cookies)

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
        inputs = {
            "i0116": constants.email,
            "i0118": constants.pw,
            "idSIButton9": ""
        }
        authenticate_id = "idDiv_SAOTCAS_Title"
        authenticate_expired_id = "idA_SAASTO_Resend"
        account_id = "tilesHolder"
        account_x_path = '//*[@id="tilesHolder"]/div[1]/div'
        authenticated = False

        while login_message not in browser.page_source:
            time.sleep(0.5)
            if "Authentication source error" in browser.page_source:
                LoginManager.login(browser)
                return

            # Select first account
            if LoginManager.is_present(browser, account_id):
                try:
                    browser.find_element_by_xpath(account_x_path).click()
                except NoSuchElementException:
                    pass

            # input email, password, submit button
            for id, value in inputs.items():
                if LoginManager.is_present(browser, id):
                    try:
                        input_element = browser.find_element_by_id(id)
                        if value:
                            if not input_element.get_property("value"): # don't fill in twice
                                input_element.send_keys(value)
                        else:
                            input_element.click()
                    except (ElementNotInteractableException, StaleElementReferenceException, NoSuchElementException):
                        pass

            # microsoft authenticator
            if LoginManager.is_present(browser, authenticate_id):
                ProgressManager.progress.add_message("Awaiting authenticator")
                authenticated = True

                while LoginManager.is_present(browser, authenticate_id):
                    if LoginManager.is_present(browser, authenticate_expired_id):
                        browser.quit()
                        browser = Browser(headless=True)
                        browser.get("https://login.ugent.be")
                        LoginManager.login(browser)

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
            json.loads(
                l["message"]
            )["message"]
                .get("params",{})
                .get("headers", {})
                .get("Set-Cookie", {})
            for l in logs if "Received" in l["message"]
        ]

        cookies = {}
        for info in cookies_info:
            if info:
                domain = Parser.between(info, 'domain=', ";")
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
            return True
        except NoSuchElementException:
            return False

    @staticmethod
    # used for callbacks
    def click_and_wait(driver, id_click, id_wait):
        while True:
            try:
                driver.find_element_by_id(id_click).click()
                try:
                    driver.find_element_by_id(id_wait)
                except:
                    return
            except:
                time.sleep(0.2)
