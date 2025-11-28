from .models.form_schema import FormSchema,FormField
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import uuid

class FormScraper:
    def extract_fields(self,html: str, base_url: str) -> list[FormSchema]:
        soup = BeautifulSoup(html,"lxml")
        form_tags = soup.find_all("form")

        forms = []
        for form_tag in form_tags:
            schema = self._parse_form(form_tag,base_url,soup)
            if schema and len(schema.fields) > 0:
                forms.append(schema)
        
        return forms
    
    async def extract_fields_from_url(self, url: str) -> list[FormSchema]:
        """Extract form fields from a URL using Playwright to handle JavaScript-rendered content"""
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="networkidle")
            
            # Get the rendered HTML
            html = await page.content()
            await browser.close()
            
            # Parse the HTML
            return self.extract_fields(html, url)
    
    def _find_label(self,field_tag,soup:BeautifulSoup) :
        field_id = field_tag.get("id")
        if field_id:
            label_tag = soup.find("label",attrs={"for":field_id})
            if label_tag:
                return label_tag.text.strip()
        
        parent_label = field_tag.find_parent("label")
        if parent_label:
            return parent_label.text.strip()
        
        return None
    
    def _parse_form(self,form_tag,base_url:str, soup:BeautifulSoup) -> FormSchema:
        action = form_tag.get("action","") or ""
        method = form_tag.get("method","") or ""
        action_url = urljoin(base_url,action)
        fields = []
        
        # Get all form elements in order
        all_elements = form_tag.find_all(["input", "textarea", "select"])
        
        # Track which grouped fields we've already processed
        processed_groups = set()
        grouped_inputs = {}
        
        # First pass: identify and group radio/checkbox inputs
        for elem in all_elements:
            if elem.name == "input":
                field_type = elem.get("type", "text").lower()
                name = elem.get("name")
                
                if name and field_type in ["radio", "checkbox"]:
                    if name not in grouped_inputs:
                        grouped_inputs[name] = {"type": field_type, "inputs": [], "first_elem": elem}
                    grouped_inputs[name]["inputs"].append(elem)
        
        # Second pass: process elements in order
        for elem in all_elements:
            if elem.name == "input":
                field_type = elem.get("type", "text").lower()
                name = elem.get("name")
                
                if not name:
                    continue
                
                # Handle grouped inputs (radio/checkbox)
                if field_type in ["radio", "checkbox"]:
                    # Only process the group once when we encounter the first element
                    if name not in processed_groups and name in grouped_inputs and grouped_inputs[name]["first_elem"] == elem:
                        field = self._parse_grouped_input_field(name, field_type, grouped_inputs[name]["inputs"], soup)
                        if field:
                            fields.append(field)
                        processed_groups.add(name)
                else:
                    # Regular input
                    field = self._parse_input_field(elem, soup)
                    if field:
                        fields.append(field)
            
            elif elem.name == "textarea":
                field = self._parse_textarea_field(elem, soup)
                if field:
                    fields.append(field)
            
            elif elem.name == "select":
                field = self._parse_select_field(elem, soup)
                if field:
                    fields.append(field)
        
        form_id = form_tag.get("id") or f"form_{uuid.uuid4().hex[:8]}"
        return FormSchema(
            form_id=form_id,
            action_url = action_url,
            method=method,
            fields=fields
        )

    def _parse_grouped_input_field(self, name: str, field_type: str, inputs: list, soup: BeautifulSoup) -> FormField:
        """Parse grouped radio or checkbox inputs into a single field with options"""
        options = []
        required = False
        label = None
        
        for inp in inputs:
            # Get the label for this specific option
            option_label = self._find_label(inp, soup)
            if option_label:
                options.append(option_label)
            else:
                # Fallback to value if no label found
                value = inp.get("value", "")
                if value:
                    options.append(value)
            
            # Check if any of the inputs are required
            if inp.get("required"):
                required = True
        
        # Try to find a group label (usually the text before the first input)
        if inputs:
            first_input = inputs[0]
            parent = first_input.find_parent()
            if parent:
                # Look for a label element that's a sibling or in the parent
                prev_sibling = parent.find_previous_sibling("label")
                if prev_sibling and not prev_sibling.find("input"):
                    label = prev_sibling.get_text(strip=True)
        
        return FormField(
            name=name,
            type=field_type,
            label=label,
            required=required,
            options=options
        )
    
    def _parse_input_field(self,input_field,soup:BeautifulSoup) -> FormField:
        field_type = input_field.get("type","text").lower()
        
        # Skip hidden fields
        if field_type == "hidden":
            return None
            
        name = input_field.get("name")
        if not name: return None
        label = self._find_label(input_field,soup)
        required = bool(input_field.get("required"))
        pattern = input_field.get("pattern")
        placeholder = input_field.get("placeholder")

        return FormField(
            name = name,
            type= field_type,
            label=label,
            required=required,
            pattern=pattern,
            placeholder=placeholder
        )

    def _parse_select_field(self,tag,soup:BeautifulSoup) -> FormField:
        name = tag.get("name")
        if not name:
            return None
        label = self._find_label(tag,soup)
        required = bool(tag.get("required"))
        options = []
        for option in tag.find_all("option"):
            if option.text.strip():
                options.append(option.text.strip())
        
        return FormField(
            name=name,
            type="select",
            label=label,
            required=required,
            options=options
        )
    
    def _parse_textarea_field(self,tag,soup:BeautifulSoup) -> FormField:
        name = tag.get("name")
        if not name:
            return None

        label = self._find_label(tag, soup)
        required = bool(tag.get("required"))
        placeholder = tag.get("placeholder")

        return FormField(
            name=name,
            type="textarea",
            label=label,
            required=required,
            placeholder=placeholder
        )
    

