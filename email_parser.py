"""
Email Parser Module
Extracts eBay listing information from emails
"""

import re
from html import unescape
from typing import Dict, Optional, List
from dataclasses import dataclass, field


@dataclass
class EbayListingInfo:
    """Data class for parsed eBay listing information."""
    item_url: str
    item_id: str
    item_title: str
    new_price: Optional[float]
    original_subject: str
    action: str  # 'update_price', 'end_and_relist', 'relist'
    quantity: Optional[int] = None  # If quantity change specified
    notes: Optional[List[str]] = None  # Special instructions (change header, etc.)
    blue_text: Optional[List[str]] = None  # Text to ADD/USE (from blue colored text)
    red_text: Optional[List[str]] = None  # Text to REMOVE (from red colored text)
    needs_review: Optional[str] = None  # Flag for odd cases that need manual review
    new_title: Optional[str] = None  # Full new title when Linda provides it

    def __str__(self):
        result = f"Item: {self.item_title}\nID: {self.item_id}\nURL: {self.item_url}"
        if self.new_price:
            result += f"\nNew Price: ${self.new_price:.2f}"
        if self.quantity:
            result += f"\nQuantity: {self.quantity}"
        if self.notes:
            result += f"\nNotes: {'; '.join(self.notes)}"
        if self.new_title:
            result += f"\nNEW TITLE: {self.new_title}"
        if self.blue_text:
            result += f"\nUSE (blue): {'; '.join(self.blue_text)}"
        if self.red_text:
            result += f"\nREMOVE (red): {'; '.join(self.red_text)}"
        if self.needs_review:
            result += f"\n*** NEEDS REVIEW: {self.needs_review}"
        return result


class EmailParser:
    """Parser for extracting eBay listing data from emails."""

    # Regex patterns
    EBAY_URL_PATTERN = r'https?://(?:www\.)?ebay\.com/itm/(\d+)[^\s<"\']*'
    PRICE_PATTERNS = [
        r'List\s+new\s+\$?([\d,]+\.?\d*)',  # "List new $79.50"
        r'List\s+n[ew]{1,2}\s+\$?([\d,]+\.?\d*)',  # Typos: "List ne $79.50", "List nw $79.50"
        r'New\s+price[:\s]+\$?([\d,]+\.?\d*)',  # "New price: $79.50"
        r'Price[:\s]+\$?([\d,]+\.?\d*)',  # "Price: $79.50"
        r'Raise\s+to\s+\$?([\d,]+\.?\d*)',  # "Raise to $79.50"
        r'Lower\s+to\s+\$?([\d,]+\.?\d*)',  # "Lower to $79.50"
        r'Change\s+(?:price\s+)?to\s+\$?([\d,]+\.?\d*)',  # "Change to $79.50" or "Change price to $79.50"
        r'\$\s*([\d,]+\.?\d*)',  # Just "$79.50"
    ]
    QUANTITY_PATTERNS = [
        r'quantity\s+(\d+)',  # "quantity 2"
        r'qty\s+(\d+)',  # "qty 2"
        r'list\s+(\d+)\s+(?:at|@)',  # "list 2 at $9.99"
    ]
    # Keywords that indicate special instructions
    INSTRUCTION_KEYWORDS = [
        'change header', 'change title', 'change description',
        'new header', 'new title', 'new description',
        'update header', 'update title', 'update description',
        'change the header', 'change the title', 'change the description',
        'use this', 'gallery photo', 'raise to', 'lower to',
    ]
    # Blue color variations (text to ADD/USE as new header)
    BLUE_COLORS = [
        '#0432ff', '#0000ff', '#0000FF', '#0432FF',  # Hex blues
        'blue', 'Blue', 'BLUE',
        '#00f', '#00F',  # Short hex
        'rgb(0,0,255)', 'rgb(4,50,255)', 'rgb(4, 50, 255)',  # RGB blues (with/without spaces)
    ]
    # Red color variations (text to REMOVE)
    RED_COLORS = [
        '#ff0000', '#FF0000', '#f00', '#F00',  # Hex reds
        'red', 'Red', 'RED',
        'rgb(255,0,0)',  # RGB red
    ]

    def parse_email(self, email_data: Dict) -> Optional[EbayListingInfo]:
        """
        Parse an email and extract eBay listing information.

        Args:
            email_data: Dictionary containing email fields (subject, body, etc.)

        Returns:
            EbayListingInfo if parsing successful, None otherwise
        """
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        html_body = email_data.get('html_body', '')
        combined_text = f"{subject}\n{body}"

        # Extract eBay URL and item ID
        url_match = re.search(self.EBAY_URL_PATTERN, combined_text)
        if not url_match:
            return None

        item_url = url_match.group(0)
        item_id = url_match.group(1)

        # Clean up URL (remove tracking params if needed)
        item_url = self._clean_ebay_url(item_url, item_id)

        # Extract item title from subject
        item_title = self._extract_title(subject)

        # Extract price from BODY ONLY (not subject, which may contain prices in item titles)
        new_price = self._extract_price(body)

        # Extract quantity if specified
        quantity = self._extract_quantity(body)

        # Extract special instructions/notes
        notes = self._extract_notes(body)

        # Extract full new title if Linda provides it
        new_title = self._extract_new_title(body)

        # Extract colored text from HTML (blue=use/add, red=remove)
        blue_text, red_text = self._extract_colored_text(html_body)

        # Determine action based on email content
        action = self._determine_action(combined_text)

        # Check for odd cases that need manual review
        needs_review = self._check_needs_review(body, notes, blue_text, red_text)

        return EbayListingInfo(
            item_url=item_url,
            item_id=item_id,
            item_title=item_title,
            new_price=new_price,
            original_subject=subject,
            action=action,
            quantity=quantity,
            notes=notes,
            blue_text=blue_text,
            red_text=red_text,
            needs_review=needs_review,
            new_title=new_title
        )

    def _clean_ebay_url(self, url: str, item_id: str) -> str:
        """Clean eBay URL to standard format."""
        # Return a clean, simple URL
        return f"https://www.ebay.com/itm/{item_id}"

    def _extract_title(self, subject: str) -> str:
        """Extract item title from email subject."""
        # Remove common suffixes
        title = subject
        for suffix in [' | eBay', ' - eBay', '| eBay', '- eBay']:
            if title.endswith(suffix):
                title = title[:-len(suffix)]

        return title.strip()

    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from email text."""
        for pattern in self.PRICE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    return float(price_str)
                except ValueError:
                    continue
        return None

    def _extract_quantity(self, text: str) -> Optional[int]:
        """Extract quantity from email text."""
        for pattern in self.QUANTITY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    qty = int(match.group(1))
                    if qty > 1:  # Only return if quantity > 1 (default is 1)
                        return qty
                except ValueError:
                    continue
        return None

    def _extract_notes(self, text: str) -> Optional[List[str]]:
        """Extract special instructions from email text."""
        notes = []
        text_lower = text.lower()

        # Check for instruction keywords
        for keyword in self.INSTRUCTION_KEYWORDS:
            if keyword in text_lower:
                # Find the line containing this keyword and include context
                for line in text.split('\n'):
                    if keyword in line.lower() and line.strip():
                        # Clean up the line
                        clean_line = line.strip()
                        if clean_line and clean_line not in notes:
                            notes.append(clean_line)
                        break

        # Also check for "and" followed by action words (e.g., "and change header")
        and_patterns = [
            r'and\s+(change\s+\w+)',
            r'and\s+(use\s+.{10,50})',
            r'and\s+(raise\s+to\s+\$?[\d.]+)',
        ]
        for pattern in and_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                instruction = match.group(1).strip()
                if instruction and instruction not in notes:
                    notes.append(instruction)

        return notes if notes else None

    def _extract_new_title(self, text: str) -> Optional[str]:
        """
        Extract the full new title when Linda provides it after 'add to header' or similar.
        Linda often formats it as:
            Add to header

            New Title Text Here
            More Title Text
        """
        lines = text.split('\n')

        # Look for header change indicators
        header_triggers = ['add to header', 'change header', 'new header', 'change title', 'new title']

        trigger_idx = -1
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if any(trigger in line_lower for trigger in header_triggers):
                trigger_idx = i
                break

        if trigger_idx == -1:
            return None

        # Collect non-empty lines after the trigger (the new title)
        title_lines = []
        for line in lines[trigger_idx + 1:]:
            stripped = line.strip()
            # Stop at URLs or other markers
            if stripped.startswith('http') or stripped.startswith('List ') or '$' in stripped:
                break
            if stripped and len(stripped) > 2:
                title_lines.append(stripped)
            # Usually the title is 1-2 lines
            if len(title_lines) >= 2:
                break

        if title_lines:
            return ' '.join(title_lines)
        return None

    def _extract_colored_text(self, html: str) -> tuple:
        """
        Extract colored text from HTML email.
        Blue text = text to USE/ADD (typically new header/title)
        Red text = text to REMOVE

        Returns:
            Tuple of (blue_text_list, red_text_list)
        """
        if not html:
            return None, None

        blue_texts = []
        red_texts = []

        # Pattern to match <font color="...">text</font>
        font_pattern = r'<font\s+color=["\']([^"\']+)["\']\s*[^>]*>([^<]+)</font>'

        # Pattern to match <span style="color: ...">text</span> and similar
        style_pattern = r'<(?:span|div|p|h1)[^>]*style=["\'][^"\']*color:\s*([^;"\']+)[^"\']*["\'][^>]*>([^<]+)</(?:span|div|p|h1)>'

        # Pattern for nested spans with style color (Linda sometimes uses this)
        nested_style_pattern = r'style=["\']color:\s*([^;"\']+)[;"\'][^>]*>([^<]{3,100})<'

        for pattern in [font_pattern, style_pattern, nested_style_pattern]:
            matches = re.findall(pattern, html, re.IGNORECASE | re.DOTALL)
            for color, text in matches:
                # Clean up the text
                text = unescape(text).strip()
                if not text or len(text) < 2:
                    continue

                # Normalize color for comparison
                color_lower = color.lower().strip()

                # Check if it's a blue color
                is_blue = any(
                    blue.lower() in color_lower or color_lower in blue.lower()
                    for blue in self.BLUE_COLORS
                )

                # Check if it's a red color
                is_red = any(
                    red.lower() in color_lower or color_lower in red.lower()
                    for red in self.RED_COLORS
                )

                if is_blue and text not in blue_texts:
                    blue_texts.append(text)
                elif is_red and text not in red_texts:
                    red_texts.append(text)

        return (blue_texts if blue_texts else None,
                red_texts if red_texts else None)

    def _check_needs_review(self, body: str, notes: Optional[List[str]],
                            blue_text: Optional[List[str]], red_text: Optional[List[str]]) -> Optional[str]:
        """
        Check for odd cases that need manual review.
        Returns a reason string if review needed, None otherwise.
        """
        body_lower = body.lower()
        reasons = []

        # Check if "change header/title" mentioned but no blue text found
        header_keywords = ['change header', 'change title', 'new header', 'new title', 'change the header', 'change the title']
        has_header_instruction = any(kw in body_lower for kw in header_keywords)
        if has_header_instruction and not blue_text:
            reasons.append("'change header' mentioned but no blue text found")

        # Check if "change description" or "remove" mentioned but no red text found
        remove_keywords = ['change description', 'remove', 'delete']
        has_remove_instruction = any(kw in body_lower for kw in remove_keywords)
        if has_remove_instruction and not red_text and 'change description' in body_lower:
            reasons.append("'change description' mentioned but no red text found")

        # Check for unusual patterns that might indicate missed parsing
        if 'gallery photo' in body_lower:
            reasons.append("gallery photo change requested - verify manually")

        return '; '.join(reasons) if reasons else None

    def _determine_action(self, text: str) -> str:
        """Determine what action to take based on email content."""
        text_lower = text.lower()

        # Check for specific action keywords
        if any(kw in text_lower for kw in ['end and relist', 'end & relist', 'relist']):
            return 'end_and_relist'
        elif any(kw in text_lower for kw in ['sell similar', 'create new']):
            return 'sell_similar'
        elif any(kw in text_lower for kw in ['end listing', 'end item']):
            return 'end_listing'
        else:
            # Default to price update if price is mentioned
            if any(kw in text_lower for kw in ['list new', 'new price', 'price']):
                return 'update_price'

        return 'update_price'  # Default action

    def parse_multiple(self, emails: List[Dict]) -> List[EbayListingInfo]:
        """Parse multiple emails and return list of valid listings."""
        results = []
        for email in emails:
            parsed = self.parse_email(email)
            if parsed:
                results.append(parsed)
        return results


def test_parser():
    """Test the parser with sample data."""
    sample_email = {
        'subject': 'Sterling Silver Solid Link Chain 23" NO Clasp NEW 8.3gr | eBay',
        'body': '''List new $79.50

https://www.ebay.com/itm/276715685145?_skw=silver+chain&itmmeta=01KEVXH0EHP7504DG493T4V762&hash=item406d8a4519:g:cvTkAAOSwf5FnKJOC
'''
    }

    parser = EmailParser()
    result = parser.parse_email(sample_email)

    if result:
        print("Parsed successfully:")
        print(result)
        print(f"\nAction: {result.action}")
    else:
        print("Failed to parse email")


if __name__ == "__main__":
    test_parser()
