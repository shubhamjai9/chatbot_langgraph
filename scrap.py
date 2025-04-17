from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
from minify_html import minify
from inscriptis import get_text


def get_processed_text(
    page_source: str,
    base_url: str,
    html_parser: str = "lxml",
    keep_webpage_links: bool = True,
    remove_script_tag: bool = True,
    remove_style_tag: bool = True,
    remove_tags: list = [],
) -> str:
    """
    process html text. This helps the LLM to easily extract/scrape data especially image links and web links.

    Args:
        page_source (str): html source text
        base_url (str): url of the html source.
        html_parser (str): which beautifulsoup html parser to use, defaults to 'lxml'
        keep_webpage_links (bool): keep webpage links. if scraping job does not require links then can remove them to reduce input token count to LLM. Default True
        remove_script_tag (bool): True
        remove_style_tag (bool): =True
        remove_tags (list): = list of tags to be remove. Default []

    Returns (str):
        LLM ready input web page text
    """
    try:
        soup = BeautifulSoup(page_source, html_parser)

        # -------remove tags----------
        remove_tag = []
        if remove_script_tag:
            remove_tag.append("script")
        if remove_style_tag:
            remove_tag.append("style")
        remove_tag.extend(remove_tags)
        remove_tag = list(set(remove_tag))
        for tag in soup.find_all(remove_tag):
            try:
                tag.extract()
            except Exception as e:
                print("Error while removing tag: ", e)
                continue

        # --------process image links--------
        for image in (images := soup.find_all("img")):
            try:
                image.replace_with("")
            except Exception as e:
                print("Error while getting image link: ", e)
                continue
        for link in (urls := soup.find_all("a", href=True)):
            try:
                if not keep_webpage_links:
                    link.replace_with("")
                else:
                    link.replace_with(
                        link.text + ": " + urljoin(base_url, link["href"]) + " "
                    )
            except Exception as e:
                print("Error while getting webpage link: ", e)
                continue

        # -----------change text structure-----------
        body_content = soup.find("body")
        if body_content:
            try:
                minimized_body = minify(str(body_content))
                text = get_text(minimized_body)
            except:
                text = get_text(str(body_content))
        else:
            text = soup.get_text()
        return text

    except Exception as e:
        print("Error while getting processed text: ", e)
        return ""


def url_extract(
    url: str,
    wait: float = 2,
    user_agent: str = "Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 640 XL LTE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Mobile Safari/537.36 Edge/12.10166",
    chrome: bool = False,
) -> str:
    """
    Get html text using selenium

    Args:
      url (str): The url from which html content is to be extracted
      wait (float): time to implicitly wait for the website to load. default is 2 sec.
      user_agent (str): user agent. default "Mozilla/5.0 (Windows Phone 10.0; Android 4.2.1; Microsoft; Lumia 640 XL LTE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Mobile Safari/537.36 Edge/12.10166"

    Returns (str):
      html text
    """
    try:
        # add driver options
        options = webdriver.ChromeOptions()
        options.add_argument(f"--user-agent={user_agent}")
        options.add_argument("--disable-dev-shm-usage")
        if not chrome:
            options.add_argument("headless")
        # driver = webdriver.Chrome(options=options)
        driver = webdriver.Remote(
            "http://127.0.0.1:4444/wd/hub", DesiredCapabilities.CHROME
        )
        driver.get(url)
        driver.implicitly_wait(wait)

        return driver.page_source
    except Exception as e:
        print("Error in web scraping", str(e))
        return default_url_extract(url)
        # return {
        #     "error": "Can not extract Content from website",
        #     "status": False,
        #     "response": str(e),
        # }


def default_url_extract(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return {
                "error": "Can not extract Content from website",
                "status": False,
                "response": response.text,
            }
        content = response.text
        return content
    except Exception as e:
        return {
            "error": "Can not extract Content from website",
            "status": False,
            "response": str(e),
        }


if __name__ == "__main__":
    urls = [
        "https://huyenchip.com/2024/07/25/genai-platform.html",
        "https://lilianweng.github.io/posts/2024-07-07-hallucination/",
        "https://jina.ai/news/what-is-colbert-and-late-interaction-and-why-they-matter-in-search/",
        "https://quoraengineering.quora.com/Building-Embedding-Search-at-Quora",
    ]
    print(url_extract(urls[0]))
    print("---\n" * 5)
    print(get_processed_text(url_extract(urls[0]), urls[0]))
