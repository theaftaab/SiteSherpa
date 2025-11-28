from dataclasses import dataclass
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

@dataclass
class FormSchema:
    form_id: str
    action_url: str
    method: str
    fields: List[FormField]