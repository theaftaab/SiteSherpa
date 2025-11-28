from bs4 import BeautifulSoup
from .page_scraper import PageScraper
from .models.page_content import PageContent
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from playwright.async_api import async_playwright

class WebScraper:
    def __init__(self, max_depth=3, stay_in_path=False):
        self.max_depth = max_depth
        self.stay_in_path = stay_in_path
        self.visited = set()
        self.page_scraper = PageScraper()

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
            browser = await p.chromium.launch(headless=True)
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
                    # Ensure all crawled URLs remain inside the start path
                    if not parsed_url.path.startswith(allowed_path_prefix):
                        continue

                try:
                    print(f"Scraping: {url}")
                    page_content = await self.scrape_page(page, url)
                    results.append(page_content)
                    self.visited.add(url)

                    links = self.extract_links(page_content.raw_html, url)

                    for link in links:
                        link, _ = urldefrag(link)
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

        return PageContent(
            url=url,
            title=title,
            text=text,
            metadata=metadata,
            raw_html=html,
            forms=None
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
