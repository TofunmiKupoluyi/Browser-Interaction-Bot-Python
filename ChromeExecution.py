from selenium import webdriver
from selenium.webdriver import ChromeOptions
from collections import deque
from event_handling.BrowserInteractions import BrowserInteractions
from HTMLDocumentUtil import HTMLDocumentUtil
from event_handling.EventHandler import EventHandler
from event_handling.Event import Event
from event_handling.exceptions.InteractionBotException import InteractionBotException

class ChromeExecution:
    def __init__(self, url: str, event_handler: EventHandler, output_file_directory: str = None, proxy_url: str = None):
        self.url = url
        self.output_file_directory = "screenshots"
        self.screenshot_count = 0
        self.event_handler = event_handler
        self.chrome_options = ChromeOptions()
        self.set_default_chrome_options()

        if proxy_url:
            self.chrome_options.add_argument("--proxy-server="+proxy_url)
        if output_file_directory:
            self.output_file_directory = output_file_directory

        self.browser = webdriver.Chrome(chrome_options=self.chrome_options)
        self.event_handler.set_browser(self.browser)

    def set_default_chrome_options(self) -> None:
        # self.chrome_options.add_experimental_option("profile.default_content_setting_values.notifications", 2)
        self.chrome_options.add_argument("--ignore-certificate-errors")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-popup-blocking")

    def screenshot(self) -> None:
        self.screenshot_count += 1
        BrowserInteractions.screenshot(self.browser, self.output_file_directory + "/" + str(self.screenshot_count))

    def close_tools(self) -> None:
        self.browser.close()

    def execute(self) -> Event:
        self.url = BrowserInteractions.open_page(self.browser, self.url)
        html_document_util = HTMLDocumentUtil(self.browser)
        event_list = html_document_util.event_list
        print("No of events:", len(event_list))
        base_event = Event("baseEvent", "/html/body")
        event_queue = deque()
        event_queue.append(base_event)

        while event_queue:
            BrowserInteractions.open_page(self.browser, self.url)
            BrowserInteractions.scroll_to_top(self.browser)
            parent_event = event_queue.popleft()

            self.event_handler.trigger_event(parent_event)
            self.screenshot()

            if self.browser.current_url != self.url:
                BrowserInteractions.open_page(self.browser, self.url)
                continue

            i = len(event_list) - 1
            while i >= 0:
                event = event_list[i]
                print("{} {}".format(event.event_type, event.xpath))
                try:
                    self.event_handler.trigger_event(event)
                    parent_event.add_child(event)
                    event_queue.append(event)
                    del event_list[i]
                    BrowserInteractions.open_page(self.browser, self.url)
                    self.event_handler.trigger_event(parent_event)

                except InteractionBotException:
                    BrowserInteractions.open_page(self.browser, self.url)
                    if self.browser.current_url != self.url:
                        self.event_handler.trigger_event(parent_event)

                finally:
                    i -= 1

        for event in event_list:
            print("{} {}".format(event.event_type, event.xpath))

        print("Complete")
        self.close_tools()
        return base_event





