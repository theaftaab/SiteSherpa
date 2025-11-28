import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.scraper.web_scraper import WebScraper
import asyncio
async def main():
    scraper = WebScraper(max_depth=1)
    data = await scraper.crawl("https://www.jotform.com/build/253311722138449")

    for page in data:
        print(page.title)
        print(len(page.text), "chars scraped")
        print(page.text)
        print(page.forms)

asyncio.run(main())