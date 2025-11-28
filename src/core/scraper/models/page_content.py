from dataclasses import dataclass
from typing import Dict,Optional, List

@dataclass
class PageContent:
    url: str
    title: str
    text: str
    metadata: Dict
    raw_html: str
    forms : Optional[List] = None

    def to_dict(self):
        return {
            "url": self.url,
            "title": self.title,
            "text" : self.text,
            "metadata" : self.metadata,
            "raw_html": self.raw_html,
            "forms" : [f.to_dict() for f in self.forms] if self.forms else []
        } 