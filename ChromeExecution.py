from os import makedirs, path
from seleniumwire import webdriver
from selenium.webdriver import ChromeOptions
from collections import deque
from event_handling.BrowserInteractions import BrowserInteractions
from HTMLDocumentUtil import HTMLDocumentUtil
from event_handling.EventHandler import EventHandler
from event_handling.Event import Event
from event_handling.exceptions.InteractionBotException import InteractionBotException
from DOTFileBuilder import DOTFileBuilder


class ChromeExecution:
    def __init__(self, url: str, event_handler: EventHandler, output_file_directory: str = None, proxy_url: str = None, solution: str = "original"):
        self.url = url
        self.output_file_directory = "screenshots"
        self.solution = solution
        self.screenshot_count = 0
        self.event_handler = event_handler
        self.chrome_options = ChromeOptions()
        self.dot_file_builder = DOTFileBuilder(self.output_file_directory)
        self.set_default_chrome_options()

        if proxy_url:
            self.chrome_options.add_argument("--proxy-server="+proxy_url)
        if output_file_directory:
            self.output_file_directory = output_file_directory

        self.browser = webdriver.Chrome(chrome_options=self.chrome_options)
        self.browser.request_interceptor = self.interceptor
        self.event_handler.set_browser(self.browser)
        self.create_directory(self.output_file_directory)
        self.trace_file = open(self.output_file_directory + "/" + "trace", "w")

    def set_default_chrome_options(self) -> None:
        # self.chrome_options.add_experimental_option("profile.default_content_setting_values.notifications", 2)
        self.chrome_options.add_argument("--ignore-certificate-errors")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-popup-blocking")

    def create_directory(self, output_directory: str) -> None:
        if not path.exists(output_directory):
            makedirs(output_directory)

    def interceptor(self, request):
        request.headers['init_url'] = self.url
        request.headers['solution'] = self.solution

    def screenshot(self) -> None:
        self.screenshot_count += 1
        BrowserInteractions.screenshot(self.browser, self.output_file_directory + "/" + str(self.screenshot_count))

    def write_to_trace_file(self, full_event_trace: list) -> None:
        self.trace_file.write(str(full_event_trace)+"\n")
        self.trace_file.flush()

    def close_tools(self) -> None:
        self.browser.close()
        self.dot_file_builder.close()
        self.trace_file.close()

    def execute(self) -> Event:
        self.url = BrowserInteractions.open_page(self.browser, self.url)
        # BrowserInteractions.scroll_to_bottom(self.browser)
        html_document_util = HTMLDocumentUtil(self.browser)
        event_list = html_document_util.event_list
        print("No of events:", len(event_list))
        base_event = Event("baseEvent", "/html/body")
        event_queue = deque()
        event_queue.append(base_event)

        while event_queue:
            has_child = False # used for dot file
            BrowserInteractions.open_page(self.browser, self.url)
            BrowserInteractions.scroll_to_top(self.browser)
            parent_event = event_queue.popleft()

            print("Parent", parent_event.xpath, parent_event.event_type)
            self.event_handler.trigger_event(parent_event)
            self.write_to_trace_file(parent_event.serialize_full_event_trace())
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
                    has_child = True
                    BrowserInteractions.open_page(self.browser, self.url)
                    self.event_handler.trigger_event(parent_event)

                except InteractionBotException:
                    if self.browser.current_url != self.url:
                        BrowserInteractions.open_page(self.browser, self.url)
                        self.event_handler.trigger_event(parent_event)

                finally:
                    i -= 1

            if not has_child:
                self.dot_file_builder.add_node(parent_event.generate_full_dot_representation())
            print()

        for event in event_list:
            print("{} {}".format(event.event_type, event.xpath))

        print("Complete")
        self.close_tools()
        return base_event





