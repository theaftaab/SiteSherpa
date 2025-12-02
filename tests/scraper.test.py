import sys
from pathlib import Path
import asyncio
import json

# Add project root
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.core.scraper.web_scraper import WebScraper

START_URL = "http://localhost:3000/"

async def main():
    scraper = WebScraper(max_depth=2, stay_in_path=True)

    print("\n=== Starting Crawl ===\n")
    data = await scraper.crawl(START_URL)

    print("\n=== Pages Crawled ===\n")
    for page in data:
        print(f"URL: {page.url}")
        print(f"TITLE: {page.title}")
        print(f"TEXT LENGTH: {len(page.text)} chars\n")

    # Use the start URL here
    kb_file = scraper.kb._get_site_file(START_URL)

    print("\n=== KB Saved Files ===\n")
    print("KB File:", kb_file.name)

    if not kb_file.exists():
        print("ERROR: KB file not created.")
        return

    # Read using utf-8 to match how KB files are written
    kb_data = json.loads(kb_file.read_text(encoding='utf-8'))

    print("\n=== KB Summary ===")
    print("Total Pages:", len(kb_data["pages"]))

    print("\n=== First 3 Pages ===")
    for path, page in list(kb_data["pages"].items())[:3]:
        print("-", path)
        print("  title:", page["title"])
        print("  text length:", len(page["text"]))

asyncio.run(main())
