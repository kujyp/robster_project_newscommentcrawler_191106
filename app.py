import atexit
import os
import queue
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from crawler import download_driver
from crawler.utils import console
from crawler.utils.fileio import save_as_json


def open_browser(driver_path):
    # type: (str) -> WebDriver
    console.info()
    target_directory = os.path.dirname(driver_path)
    download_driver.install_driver_if_not_installed(target_directory)

    driver = webdriver.Chrome(driver_path)
    return driver


def retrieve(driver, url, dynamic_table):
    # type: (WebDriver, str, DynamicTable) -> None

    driver.get(url)
    console.info(f"Crawl path [{url}]...")
    console.info(f"url_target_queue.qsize() [{dynamic_table.url_target_queue.qsize()}]...")

    a_tags = driver.find_elements_by_tag_name("a")
    # each_a_tag = a_tags[10]
    for each_a_tag in a_tags:
        href = each_a_tag.get_property("href")
        if not href:
            continue

        parsed = urlparse(href)
        url_path = parsed.netloc + parsed.path

        if url_path in dynamic_table.parsed:
            # console.info(f"Skip parsed path [{url_path}]")
            continue

        dynamic_table.parsed.add(url_path)

        if url_path.startswith("v.media.daum.net/v/"):
            console.info(f"Add found path [{url_path}]...")
            dynamic_table.url.add(url_path)
        elif (url_path not in dynamic_table.parsed) \
                and url_path.startswith("media.daum.net/issue/") \
                or url_path.startswith("media.daum.net/series/") \
                or url_path.startswith("media.daum.net/ranking/age/") \
                or url_path.startswith("media.daum.net/ranking/bestreply/") \
                or url_path.startswith("media.daum.net/breakingnews/"):
            dynamic_table.url_target_queue.put(url_path)

    if dynamic_table.url_target_queue.empty():
        return

    url_target = dynamic_table.url_target_queue.get_nowait()
    retrieve(driver, "https://" + url_target, dynamic_table)


class DynamicTable:
    def __init__(self):
        super().__init__()
        self.url = set()
        self.parsed = set()
        self.url_target_queue = queue.Queue()


if __name__ == '__main__':
    driver_path = os.path.join("driver", "chromedriver")
    driver = open_browser(driver_path)
    atexit.register(lambda: driver.quit())

    dynamic_table = DynamicTable()
    seed_url = "https://media.daum.net/politics/"
    retrieve(driver, seed_url, dynamic_table)

    for url in dynamic_table.url:
        filepath = os.path.join("data", "daum", "articles", url)
        if os.path.exists(filepath):
            console.error(f"File already exists. [{filepath}]")
            continue
        save_as_json(filepath, {
            "url": url,
        })
