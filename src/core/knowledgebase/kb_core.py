import json
from pathlib import Path
from urllib.parse import urlparse
from ..scraper.models.form_schema import FormSchema
from ..scraper.models.page_content import PageContent
import re

class KnowledgeBase:
    def __init__(self, kb_dir="kb"):
        self.kb_dir = Path(kb_dir)
        self.sites_dir = self.kb_dir / "sites"
        self.sites_dir.mkdir(parents=True, exist_ok=True)
        
        # in-memory cache so we don’t reload file each time
        self.cache = {}  

    def _get_site_file(self, url: str) -> Path:
        parsed = urlparse(url)
        # Use scheme + sanitized netloc to avoid invalid filename chars (e.g. ':' on Windows)
        domain = parsed.netloc.replace("www.", "")
        # replace any character that's not alnum, dot, dash, or underscore
        safe_domain = re.sub(r"[^A-Za-z0-9._-]", "_", domain)
        filename = f"{parsed.scheme}_{safe_domain}.json"
        target = self.sites_dir / filename

        # If an old-style file exists (unsanitized), try to migrate it to the new name.
        old_name = f"{domain}.json"
        old_file = self.sites_dir / old_name
        if old_file.exists() and not target.exists():
            try:
                # copy contents then remove old file if possible
                content = old_file.read_bytes()
                target.write_bytes(content)
                try:
                    old_file.unlink()
                except Exception:
                    # best-effort: ignore unlink failures
                    pass
            except Exception:
                # if migration fails, just ignore and proceed (we'll use target path)
                pass

        return target

    def _load_site(self, url: str) -> dict:
        file = self._get_site_file(url)
        if file.exists():
            try:
                with open(file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Corrupted JSON file — write a .corrupt copy safely and reinitialize
                try:
                    raw = file.read_text(encoding="utf-8", errors="replace")
                    corrupt_name = f"{file.stem}.corrupt{file.suffix}"
                    corrupt_file = file.with_name(corrupt_name)
                    corrupt_file.write_text(raw, encoding="utf-8")
                    try:
                        file.unlink()
                    except Exception:
                        pass
                except Exception:
                    # best-effort: ignore failures and reinitialize
                    pass

                return {
                    "root_url": url,
                    "pages": {}
                }
        else:
            # initialize empty site structure
            return {
                "root_url": url,
                "pages": {}
            }

    def _save_site(self, url: str, data: dict):
        file = self._get_site_file(url)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_page_content(self, page: PageContent):
        site_data = self._load_site(page.url)

        parsed = urlparse(page.url)
        path_key = parsed.path or "/"

        site_data["pages"][path_key] = {
            "url": page.url,
            "title": page.title,
            "text": page.text,
            "metadata": page.metadata,
            "forms": [f.to_dict() for f in page.forms] if page.forms else []
        }

        self._save_site(page.url, site_data)

    def add_form(self, form: FormSchema, page_url: str):
        site_data = self._load_site(page_url)

        parsed = urlparse(page_url)
        path_key = parsed.path or "/"

        if path_key not in site_data["pages"]:
            site_data["pages"][path_key] = {
                "url": page_url,
                "title": None,
                "text": None,
                "metadata": {},
                "forms": []
            }

        site_data["pages"][path_key]["forms"].append(form.to_dict())

        self._save_site(page_url, site_data)
