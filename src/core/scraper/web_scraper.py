from bs4 import BeautifulSoup
from scraper.page_scraper import PageScraper
from scraper.models.page_content import PageContent
from urllib.parse import urljoin, urlparse
from collections import deque
from playwright.async_api import async_playwright

class WebScraper:
    def __init__(self,max_depth=3):
        self.max_depth = max_depth
        self.visited = set()
        self.page_scraper = PageScraper()
    
    async def crawl(self,start_url:str) -> list[PageContent]:
        domain = urlparse(start_url).netloc
        queue = deque([(start_url,0)])
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            while queue:
                url,depth = queue.popleft()
                if depth > self.max_depth:
                    continue
                if url in self.visited:
                    continue
                if urlparse(url).netloc != domain:
                    continue
                
                try:
                    print(f"Scraping: {url}")
                    page_content = await self.page_scraper(page,url)
                    results.append(page_content)
                    self.visited.add(url)

                    links = self.extract_links(page_content.raw_html,url)
                    for link in links:
                        if link not in self.visited:
                            queue.append((link,depth+1))
                except Exception as e:
                    print(f"Falied to scrape {url} : {e}")
            
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
                links.append(url)

        return links
