"""
End and Relist Script
Workflow: End listing via eBay help page, then Sell Similar with new price

Usage:
    python end_and_relist.py              # Show current batch (does NOT mark anything complete)
    python end_and_relist.py --done       # Mark previous batch complete, then show next batch
    python end_and_relist.py --test       # Test with just 2 items
    python end_and_relist.py --instructions  # Process instruction emails (bulk changes)

Workflow:
    1. Run script (no flags) to see batch and open pages
    2. Process the items in Chrome
    3. Run with --done to mark complete and get next batch
"""
import os
import sys
import subprocess
from outlook_reader import OutlookReader
from email_parser import EmailParser
from instruction_parser import InstructionParser, generate_seller_hub_url
from config import OUTLOOK_CONFIG

PENDING_FILE = os.path.join(os.path.dirname(__file__), 'pending_entries.txt')
COMPLETED_FILE = os.path.join(os.path.dirname(__file__), 'completed_items.txt')
END_LISTING_URL = "https://www.ebay.com/help/action?topicid=4146"


def load_completed():
    """Load set of already completed item IDs."""
    if not os.path.exists(COMPLETED_FILE):
        return set()
    with open(COMPLETED_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())


def save_completed(item_ids):
    """Append item IDs to completed file."""
    with open(COMPLETED_FILE, 'a', encoding='utf-8') as f:
        for item_id in item_ids:
            f.write(f"{item_id}\n")


def mark_previous_done(reader):
    """Mark previous batch emails as read and log as completed."""
    if not os.path.exists(PENDING_FILE):
        return 0

    with open(PENDING_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return 0

    completed_ids = []
    marked_count = 0
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) >= 2:
            entry_id = parts[0]
            item_id = parts[1]
            completed_ids.append(item_id)
            try:
                if reader.mark_as_read(entry_id):
                    marked_count += 1
            except Exception:
                pass  # Continue even if marking fails

    # Save to completed file
    if completed_ids:
        save_completed(completed_ids)
        print(f"Saved {len(completed_ids)} items to completed log")

    if marked_count:
        print(f"Marked {marked_count} emails as read")

    os.remove(PENDING_FILE)
    return len(completed_ids)


def get_next_batch(reader, limit=5):
    """Get next batch of unread emails, skipping already completed items."""
    folder = reader.get_folder_by_name(OUTLOOK_CONFIG['folder_name'], OUTLOOK_CONFIG['account_email'])
    if not folder:
        print(f"Folder '{OUTLOOK_CONFIG['folder_name']}' not found")
        return [], []

    # Load already completed items
    completed = load_completed()
    if completed:
        print(f"Skipping {len(completed)} already-completed items")

    # Get more emails than needed since some may be skipped
    emails = reader.read_emails(folder, limit=limit * 5, unread_only=True)

    parser = EmailParser()
    listings = []
    instruction_emails = []  # Emails without eBay URLs (instructions from Linda)

    for email in emails:
        subject = email.get('subject', '')

        # Skip reply emails (Re:) - these are conversations, not listings
        if subject.lower().startswith('re:'):
            continue

        if len(listings) >= limit:
            # Still check remaining emails for instruction emails
            parsed = parser.parse_email(email)
            if not parsed:
                # No eBay URL - might be an instruction email
                instruction_emails.append({
                    'subject': subject,
                    'body': email.get('body', '')[:300],
                    'entry_id': email['entry_id'],
                })
            continue

        parsed = parser.parse_email(email)
        if parsed and parsed.new_price is not None:
            # Skip if already completed
            if parsed.item_id in completed:
                continue
            listings.append({
                'entry_id': email['entry_id'],
                'item_id': parsed.item_id,
                'title': parsed.item_title[:55],
                'price': parsed.new_price,
                'quantity': parsed.quantity,
                'notes': parsed.notes,
                'blue_text': parsed.blue_text,
                'red_text': parsed.red_text,
                'needs_review': parsed.needs_review,
            })
        elif not parsed:
            # No eBay URL found - might be an instruction email from Linda
            instruction_emails.append({
                'subject': subject,
                'body': email.get('body', '')[:300],
                'entry_id': email['entry_id'],
            })

    # Save pending entries for next run
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        for l in listings:
            f.write(f"{l['entry_id']}|{l['item_id']}|{l['price']}\n")

    return listings, instruction_emails


def open_pages(listings):
    """Open End Listing page and item pages in Chrome."""
    # First, open the End Your Listing page
    urls = [END_LISTING_URL]

    # Then open each item page (for Sell Similar after ending)
    for l in listings:
        urls.append(f"https://www.ebay.com/itm/{l['item_id']}")

    cmd = ['start', 'chrome'] + urls
    subprocess.run(' '.join(cmd), shell=True)


def handle_instructions(reader):
    """Handle instruction emails (bulk changes like 'change all coin cards to $7.95')."""
    folder = reader.get_folder_by_name(OUTLOOK_CONFIG['folder_name'], OUTLOOK_CONFIG['account_email'])
    if not folder:
        print(f"Folder '{OUTLOOK_CONFIG['folder_name']}' not found")
        return

    # Get unread emails
    emails = reader.read_emails(folder, limit=20, unread_only=True)

    # Filter for instruction emails (no eBay URL)
    import re
    ebay_url_pattern = r'https?://(?:www\.)?ebay\.com/itm/\d+'

    instruction_emails = []
    for email in emails:
        subject = email.get('subject', '')
        body = email.get('body', '')

        # Skip reply emails
        if subject.lower().startswith('re:'):
            continue

        # Check if it has an eBay item URL - if not, it might be an instruction
        if not re.search(ebay_url_pattern, body):
            instruction_emails.append(email)

    if not instruction_emails:
        print("No instruction emails found.")
        return

    # Parse each instruction email
    parser = InstructionParser()
    parsed_instructions = []

    for email in instruction_emails:
        subject = email.get('subject', '')
        body = email.get('body', '')

        parsed = parser.parse(subject, body)
        if parsed:
            parsed_instructions.append({
                'email': email,
                'parsed': parsed,
            })

    if not parsed_instructions:
        print("Found instruction emails but could not parse actionable items.")
        print("\nRaw instruction emails:")
        for email in instruction_emails:
            print(f"  Subject: {email.get('subject', 'No subject')}")
            print(f"  Body: {email.get('body', '')[:200]}...")
            print()
        return

    # Display parsed instructions
    print()
    print("=" * 70)
    print("INSTRUCTION EMAILS - PARSED")
    print("=" * 70)

    for i, instr in enumerate(parsed_instructions, 1):
        parsed = instr['parsed']
        print(f"\n[{i}] {instr['email'].get('subject', 'No subject')}")
        print(f"    Action: {parsed.action.upper()}")
        print(f"    Search for: {', '.join(parsed.search_terms)}")
        if parsed.new_price:
            print(f"    New price: ${parsed.new_price:.2f}")
        if parsed.item_count:
            print(f"    Expected items: ~{parsed.item_count}")
        if parsed.additional_notes:
            print(f"    Notes: {parsed.additional_notes}")

    print()
    print("-" * 70)
    print("Opening Seller Hub searches in Chrome...")
    print("-" * 70)

    # Open search URLs
    urls = []
    for instr in parsed_instructions:
        for term in instr['parsed'].search_terms:
            url = generate_seller_hub_url(term)
            urls.append(url)
            print(f"  Search: '{term}'")
            print(f"  URL: {url}")
            print()

    if urls:
        cmd = ['start', 'chrome'] + urls
        subprocess.run(' '.join(cmd), shell=True)

    print("=" * 70)
    print("NEXT STEPS:")
    print("  1. Review search results in Chrome")
    print("  2. Select matching items and bulk edit")
    print("  3. Once done, mark instruction emails as read in Outlook")
    print("=" * 70)


def main():
    # Check for flags
    test_mode = '--test' in sys.argv
    mark_done = '--done' in sys.argv
    instructions_mode = '--instructions' in sys.argv
    batch_size = 2 if test_mode else 5

    if test_mode:
        print("=== TEST MODE: Processing only 2 items ===\n")

    reader = OutlookReader()
    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    # Handle instruction emails mode
    if instructions_mode:
        handle_instructions(reader)
        return

    # Only mark previous batch as done if --done flag is passed
    if mark_done:
        completed_count = mark_previous_done(reader)
        if completed_count:
            print(f"Marked {completed_count} items as completed.\n")
    elif os.path.exists(PENDING_FILE):
        # Remind user about pending items
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            pending_count = len([l for l in f.readlines() if l.strip()])
        if pending_count:
            print(f"NOTE: {pending_count} items from previous batch still pending.")
            print("      Run with --done flag after completing them.\n")

    # Get next batch
    listings, instruction_emails = get_next_batch(reader, limit=batch_size)

    # Always show instruction emails first (important messages from Linda)
    if instruction_emails:
        print()
        print("!" * 70)
        print("ATTENTION: INSTRUCTION EMAILS FROM LINDA")
        print("!" * 70)
        for instr in instruction_emails:
            print(f"\nSubject: {instr['subject']}")
            print(f"Message: {instr['body']}")
            print("-" * 50)
        print()

    if not listings:
        if instruction_emails:
            print("No eBay listings to process, but please review the instruction emails above.")
        else:
            print("No more unread emails with eBay price updates!")
        return

    # Display items with full info
    print(f"\nNext batch: {len(listings)} items\n")
    print("=" * 70)
    print("ITEM NUMBERS TO END (copy these to the End Listing page):\n")
    for i, l in enumerate(listings, 1):
        print(f"  {i}. {l['item_id']}")
    print()
    print("-" * 70)
    print("DETAILS (for Sell Similar - use these prices):\n")
    for i, l in enumerate(listings, 1):
        print(f"  [{i}] {l['title']}")
        print(f"      Item #: {l['item_id']}")
        print(f"      Price:  ${l['price']:.2f}")
        if l.get('quantity'):
            print(f"      >>> QUANTITY: {l['quantity']} <<<")
        if l.get('notes'):
            print(f"      >>> NOTES: {'; '.join(l['notes'])}")
        if l.get('blue_text'):
            for bt in l['blue_text']:
                print(f"      >>> USE (blue): {bt}")
        if l.get('red_text'):
            for rt in l['red_text']:
                print(f"      >>> REMOVE (red): {rt}")
        if l.get('needs_review'):
            print(f"      !!! REVIEW NEEDED: {l['needs_review']}")
        print()
    print("=" * 70)

    # Open pages
    open_pages(listings)

    print("Opened in Chrome:")
    print("  - Tab 1: End Your Listing page (enter item numbers, reason: 'error in listing')")
    print("  - Tabs 2+: Item pages (click 'Sell Similar' after ending each)")
    print()
    print("When done, run: python end_and_relist.py --done")


if __name__ == "__main__":
    main()
