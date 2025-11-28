from src.core.scraper.web_scraper import WebScraper
import asyncio
async def main():
    scraper = WebScraper(max_depth=1)
    data = await scraper.crawl("https://quotes.toscrape.com/tag/love/")

    for page in data:
        print(page.title)
        print(len(page.text), "chars scraped")
        print(page.text)

asyncio.run(main())