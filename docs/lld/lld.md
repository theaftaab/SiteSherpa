## WebScraper Class
**Purpose** : A recursive, domain bounded crawler that extracts all pages and their HTML
```python
class WebScrapper:
    - page_scrapper : PageScrapper
    - form_scrapper : FormScrapper
    - visited_urls : set[str]
    - max_depth : int
    - allowed_domain : str
    - queue : deque[str]

    + crawl(start_url:str) -> list[PageContent] : ## Recusrive crawler with domain filtering and depth limiting
    + scrape_page(url: str) -> PageContent : ## Downloads raw HTML -> Uses PageScraper & FormScraper
    + extract_links(html : str, base_url : str) -> list[str] : ## Extracts links and normalizes them
    + normalize_url(link: str,base_url: str) -> str
    + should_visit(url: str) -> bool : ## Checks if the domain is already visited or not, or not any media file or has the same domain

```
---
## PageScraper Class:

**Purpose** : Extract clean text,title and metadata from HTML

```python
class PageScraper:
    + extract_text(html: str) -> str : ## Removes navbars, footers ads and extracts visible text from <p> , <h1> , <li>
    + extract_title(html: str) -> str : ## Extracts title from the page or takes the largest <h1>
    + extract_metadata(html: str) -> dict 
    ## Returns
    ```json
    {
        "description": "....",
        "keywords" : "....",
        "generator" : ".....",
        "language": "en"
    }
    ```
    + clean_text(text:str) -> str ## Removes HTML Entites, Extra Spaces, JS/CSS fragments
```

## Supporting DTO: PageContent
```python
class PageContent:
    - url : str
    - title: str
    - text : str
    - metadata: dict
    - forms : list[FormSchema]

    + to_dict(self)

```
---

## FormScraper Class:

* **Purpose** : To extract and build structured schema for forms present in the website

```python
class FormField:
    name: str
    type: str
    label: str | None
    required: bool
    options: list[str] | None = None
    pattern: str | None = None
    placeholder: str | None = None

class FormSchema:
    form_id: str
    action_url: str
    method: str
    fields: list[FormField]
```