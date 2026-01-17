"""
Email Parser Module
Extracts eBay listing information from emails
"""

import re
from typing import Dict, Optional, List
from dataclasses import dataclass


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

    def __str__(self):
        result = f"Item: {self.item_title}\nID: {self.item_id}\nURL: {self.item_url}"
        if self.new_price:
            result += f"\nNew Price: ${self.new_price:.2f}"
        if self.quantity:
            result += f"\nQuantity: {self.quantity}"
        if self.notes:
            result += f"\nNotes: {'; '.join(self.notes)}"
        return result


class EmailParser:
    """Parser for extracting eBay listing data from emails."""

    # Regex patterns
    EBAY_URL_PATTERN = r'https?://(?:www\.)?ebay\.com/itm/(\d+)[^\s<"\']*'
    PRICE_PATTERNS = [
        r'List\s+new\s+\$?([\d,]+\.?\d*)',  # "List new $79.50"
        r'New\s+price[:\s]+\$?([\d,]+\.?\d*)',  # "New price: $79.50"
        r'Price[:\s]+\$?([\d,]+\.?\d*)',  # "Price: $79.50"
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

        # Determine action based on email content
        action = self._determine_action(combined_text)

        return EbayListingInfo(
            item_url=item_url,
            item_id=item_id,
            item_title=item_title,
            new_price=new_price,
            original_subject=subject,
            action=action,
            quantity=quantity,
            notes=notes
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
