"""
Instruction Parser Module
Parses Linda's general instruction emails (no eBay URL) to extract actionable items.
"""

import re
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class ParsedInstruction:
    """Data class for a parsed instruction."""
    search_terms: List[str]  # What to search for in active listings
    new_price: Optional[float]  # Price to change to
    action: str  # 'change_price', 'change_title', 'end_listing', etc.
    raw_text: str  # Original instruction text
    item_count: Optional[int]  # If mentioned ("about 10 of them")
    additional_notes: Optional[str]  # Any other instructions

    def __str__(self):
        result = f"Action: {self.action}\n"
        result += f"Search for: {', '.join(self.search_terms)}\n"
        if self.new_price:
            result += f"New price: ${self.new_price:.2f}\n"
        if self.item_count:
            result += f"Expected items: ~{self.item_count}\n"
        if self.additional_notes:
            result += f"Notes: {self.additional_notes}\n"
        return result


class InstructionParser:
    """Parser for Linda's instruction emails."""

    # Price patterns
    PRICE_PATTERN = r'\$\s*([\d,]+\.?\d*)'

    # Count patterns ("10 of them", "about 5", etc.)
    COUNT_PATTERNS = [
        r'(\d+)\s+of\s+them',
        r'about\s+(\d+)',
        r'around\s+(\d+)',
        r'approximately\s+(\d+)',
        r'there\s+are\s+(\d+)',
        r'(\d+)\s+items?',
    ]

    # Action keywords
    PRICE_CHANGE_KEYWORDS = ['change', 'update', 'raise', 'lower', 'set', 'make']
    END_LISTING_KEYWORDS = ['end', 'remove', 'delete', 'take down']

    def parse(self, subject: str, body: str) -> Optional[ParsedInstruction]:
        """
        Parse an instruction email.

        Args:
            subject: Email subject
            body: Email body text

        Returns:
            ParsedInstruction if actionable instruction found, None otherwise
        """
        text = f"{subject}\n{body}".lower()
        original_body = body

        # Extract price if mentioned
        new_price = self._extract_price(body)

        # Extract item count if mentioned
        item_count = self._extract_count(text)

        # Extract search terms (what items to find)
        search_terms = self._extract_search_terms(body)

        # Determine action type
        action = self._determine_action(text, new_price)

        # If we couldn't extract meaningful search terms, return None
        if not search_terms:
            return None

        # Extract any additional notes
        additional_notes = self._extract_additional_notes(body)

        return ParsedInstruction(
            search_terms=search_terms,
            new_price=new_price,
            action=action,
            raw_text=original_body.strip(),
            item_count=item_count,
            additional_notes=additional_notes
        )

    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text."""
        match = re.search(self.PRICE_PATTERN, text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except ValueError:
                pass
        return None

    def _extract_count(self, text: str) -> Optional[int]:
        """Extract expected item count from text."""
        for pattern in self.COUNT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None

    def _extract_search_terms(self, body: str) -> List[str]:
        """
        Extract search terms from the instruction.
        Looks for quoted text, or key noun phrases.
        """
        search_terms = []

        # Look for quoted text first (most explicit)
        quoted = re.findall(r'["\']([^"\']+)["\']', body)
        if quoted:
            search_terms.extend(quoted)

        # Look for "all the X" or "all X" patterns
        all_patterns = [
            r'all\s+(?:the\s+)?([a-zA-Z][a-zA-Z\s]{2,30}?)(?:\s+to|\s+at|\s*\$|\.)',
            r'change\s+(?:all\s+)?(?:the\s+)?([a-zA-Z][a-zA-Z\s]{2,30}?)(?:\s+to|\s+at|\s*\$)',
        ]
        for pattern in all_patterns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            for match in matches:
                term = match.strip()
                # Filter out common non-search words
                if term.lower() not in ['price', 'prices', 'them', 'it', 'listing', 'listings']:
                    if term and term not in search_terms:
                        search_terms.append(term)

        # Clean up search terms
        cleaned = []
        for term in search_terms:
            # Remove trailing punctuation and common suffixes
            term = re.sub(r'[\s,\.]+$', '', term)
            term = re.sub(r'\s+(to|at|for)$', '', term, flags=re.IGNORECASE)
            if len(term) >= 3:
                cleaned.append(term)

        return cleaned

    def _determine_action(self, text: str, has_price: bool) -> str:
        """Determine what action to take."""
        if any(kw in text for kw in self.END_LISTING_KEYWORDS):
            if 'end' in text and 'relist' not in text:
                return 'end_listing'

        if has_price:
            return 'change_price'

        if any(kw in text for kw in ['title', 'header', 'description']):
            return 'change_details'

        return 'review'  # Generic action for unclear instructions

    def _extract_additional_notes(self, body: str) -> Optional[str]:
        """Extract any additional notes or context."""
        # Look for parenthetical notes
        parens = re.findall(r'\(([^)]+)\)', body)
        if parens:
            return '; '.join(parens)
        return None


def generate_seller_hub_url(search_term: str) -> str:
    """Generate a Seller Hub search URL for the given term."""
    from urllib.parse import quote
    return f"https://www.ebay.com/sh/lst/active?search={quote(search_term)}"


if __name__ == "__main__":
    # Test the parser
    parser = InstructionParser()

    test_cases = [
        {
            'subject': 'Change',
            'body': 'Please change all the coin cards "frame up card" to $7.95. I think there are 10 of them'
        },
        {
            'subject': 'Price update',
            'body': 'Can you lower all the silver chains to $19.95'
        },
        {
            'subject': 'End listings',
            'body': 'Please end all the broken items'
        },
    ]

    for test in test_cases:
        print("=" * 50)
        print(f"Subject: {test['subject']}")
        print(f"Body: {test['body']}")
        print()
        result = parser.parse(test['subject'], test['body'])
        if result:
            print("Parsed:")
            print(result)
            for term in result.search_terms:
                print(f"Search URL: {generate_seller_hub_url(term)}")
        else:
            print("Could not parse instruction")
        print()
