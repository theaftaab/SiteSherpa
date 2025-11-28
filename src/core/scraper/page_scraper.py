from bs4 import BeautifulSoup
import re
class PageScraper:
    def extract_text(self,html: str) -> str:
        soup = BeautifulSoup(html,"lxml")
        for tag in soup(["script","style","nav","footer","header","noscript"]):
            tag.extract()
        text = soup.get_text(separator=" ",strip=True)
        return self.clean_text(text)

    def extract_title(self,html: str) -> str:
        soup = BeautifulSoup(html,"lxml")
        if soup.title:
            return soup.title.string.strip()
        h1 = soup.find("h1")
        return h1.get_text(strp=True) if h1 else "Untitled Page"
    
    def extract_metadata(self,html:str) -> dict:
        soup = BeautifulSoup(html,"lxml")
        meta = {}
        for tag in soup.find_all("meta"):
            if tag.get("name") and tag.get("content"):
                meta[tag["name"]] = tag["content"]
        return meta

    def clean_text(self,text:str) -> str:
        text = re.sub(r"\s+"," ",text)
        text = re.sub(r"\\n"," ",text)
        return text.strip()