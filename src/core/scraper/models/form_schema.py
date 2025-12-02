from dataclasses import dataclass, asdict
from typing import List

@dataclass
class FormField:
    name: str
    type: str
    label: str
    required: str
    options : List[str] | None = None
    pattern: str | None = None
    placeholder : str | None = None

    def to_dict(self):
        return asdict(self)

@dataclass
class FormSchema:
    form_id: str
    action_url: str
    method: str
    fields: List[FormField]
    
    def to_dict(self):
        return {
            "form_id": self.form_id,
            "action_url": self.action_url,
            "method": self.method,
            "fields": [f.to_dict() for f in self.fields]
        }