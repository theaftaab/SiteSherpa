from bs4 import BeautifulSoup
from .page_scraper import PageScraper
from .form_scraper import FormScraper
from .models.page_content import PageContent
from ..knowledgebase.kb_core import KnowledgeBase
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from playwright.async_api import async_playwright
from pathlib import PurePosixPath
import asyncio

class WebScraper:
    def __init__(self, max_depth=3, stay_in_path=False):
        self.max_depth = max_depth
        self.stay_in_path = stay_in_path
        self.visited = set()
        self.page_scraper = PageScraper()
        self.form_scraper = FormScraper()
        self.kb = KnowledgeBase()

    async def crawl(self, start_url: str) -> list[PageContent]:
        parsed_start = urlparse(start_url)
        scheme_domain = f"{parsed_start.scheme}://{parsed_start.netloc}"

        # Build the allowed prefix for path restriction
        allowed_path_prefix = parsed_start.path
        if not allowed_path_prefix.endswith("/"):
            allowed_path_prefix += "/"

        
        queue = deque([(start_url, 0)])
        results = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True,slow_mo=250)
            page = await browser.new_page()

            while queue:
                url, depth = queue.popleft()

                # Normalize fragment-less URL
                url, _ = urldefrag(url)

                if depth > self.max_depth:
                    continue
                if url in self.visited:
                    continue

                parsed_url = urlparse(url)

                # Restrict domain + scheme
                if f"{parsed_url.scheme}://{parsed_url.netloc}" != scheme_domain:
                    continue

                # Restrict to starting subpath only
                if self.stay_in_path:
                    start_path = parsed_start.path.rstrip("/") + "/"
                    current_path = parsed_url.path.rstrip("/") + "/"

                    if not current_path.startswith(start_path):
                        continue


                try:
                    print(f"Scraping: {url}")
                    page_content = await self.scrape_page(page, url)
                    results.append(page_content)
                    self.visited.add(url)

                    self.kb.add_page_content(page_content)

                    links = self.extract_links(page_content.raw_html, url)

                    for link in links:
                        link, _ = urldefrag(link)
                        parsed = urlparse(link)
                        if f"{parsed.scheme}://{parsed.netloc}" != scheme_domain:
                            continue
                        if self.stay_in_path:
                            start_path = parsed_start.path.rstrip("/") + "/"
                            current_path = parsed.path.rstrip("/") + "/"
                            if not current_path.startswith(start_path):
                                continue

                        if link not in self.visited:
                            queue.append((link, depth + 1))

                except Exception as e:
                    print(f"Failed to scrape {url}: {e}")

            await browser.close()

        return results

    async def scrape_page(self, page, url: str) -> PageContent:
        await page.goto(url, wait_until="domcontentloaded")

        html = await page.content()
        title = self.page_scraper.extract_title(html)
        text = self.page_scraper.extract_text(html)
        metadata = self.page_scraper.extract_metadata(html)

        forms = self.form_scraper.extract_fields(html,base_url=url)

        return PageContent(
            url=url,
            title=title,
            text=text,
            metadata=metadata,
            raw_html=html,
            forms=forms
        )

    def extract_links(self, html: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        links = []

        for tag in soup.find_all("a", href=True):
            url = urljoin(base_url, tag["href"])
            if url.startswith("http"):
                url, _ = urldefrag(url)  # remove fragments
                links.append(url)

        return links