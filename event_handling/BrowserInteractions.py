from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.common.exceptions import NoSuchWindowException
from time import sleep


class BrowserInteractions:
    @classmethod
    def open_page(cls, browser: Chrome, url: str):
        browser.get(url)
        cls.wait_for_page_load(browser)
        return browser.current_url

    @classmethod
    def wait_for_page_load(cls, browser: Chrome) -> None:
        load_state = browser.execute_script("return document.readyState")
        while load_state != "complete":
            load_state = browser.execute_script("return document.readyState")
        cls.wait(2)

    @classmethod
    def scroll_to_top(cls, browser: Chrome):
        browser.execute_script("window.scrollTo(0, 0)")
        cls.wait(1)

    @classmethod
    def close_extraneous_tabs(cls, browser: Chrome, limit: int):
        if len(browser.window_handles) < limit:
            return
        else:
            try:
                original_handle = browser.current_window_handle
                for handle in browser.window_handles:
                    if handle != original_handle:
                        browser.switch_to.window(handle)
                        browser.close()
                browser.switch_to.window(original_handle)
            except NoSuchWindowException:
                print("Window already closed")

    @classmethod
    def screenshot(cls, browser: Chrome, file_name: str):
        cls.wait(5)
        browser.save_screenshot(file_name)

    @staticmethod
    def wait(seconds: int) -> None:
        sleep(seconds)