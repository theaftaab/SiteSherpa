import sys
from pathlib import Path
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.scraper.form_scraper import FormScraper
import json

async def main():
    url = "https://formspree.io/library/application/simple-job-application-form/?tech=html"
    
    scraper = FormScraper()
    forms = await scraper.extract_fields_from_url(url)
    
    print(f"Number of forms found: {len(forms)}")
    
    # Pretty print as JSON
    def to_dict(obj):
        """Recursively convert objects to dictionaries"""
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):
            return {k: to_dict(v) for k, v in obj.__dict__.items()}
        elif isinstance(obj, list):
            return [to_dict(item) for item in obj]
        else:
            return obj
    
    forms_dict = [to_dict(form) for form in forms]
    print(json.dumps(forms_dict, indent=2))

asyncio.run(main())