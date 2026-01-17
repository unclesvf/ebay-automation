"""
End and Relist Script
Workflow: End listing via eBay help page, then Sell Similar with new price

Usage:
    python end_and_relist.py          # Get next batch, open pages
    python end_and_relist.py --test   # Test with just 2 items
"""
import os
import sys
import subprocess
from outlook_reader import OutlookReader
from email_parser import EmailParser
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
        return []

    # Load already completed items
    completed = load_completed()
    if completed:
        print(f"Skipping {len(completed)} already-completed items")

    # Get more emails than needed since some may be skipped
    emails = reader.read_emails(folder, limit=limit * 3, unread_only=True)

    parser = EmailParser()
    listings = []

    for email in emails:
        if len(listings) >= limit:
            break
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
            })

    # Save pending entries for next run
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        for l in listings:
            f.write(f"{l['entry_id']}|{l['item_id']}|{l['price']}\n")

    return listings


def open_pages(listings):
    """Open End Listing page and item pages in Chrome."""
    # First, open the End Your Listing page
    urls = [END_LISTING_URL]

    # Then open each item page (for Sell Similar after ending)
    for l in listings:
        urls.append(f"https://www.ebay.com/itm/{l['item_id']}")

    cmd = ['start', 'chrome'] + urls
    subprocess.run(' '.join(cmd), shell=True)


def main():
    # Check for test mode
    test_mode = '--test' in sys.argv
    batch_size = 2 if test_mode else 5

    if test_mode:
        print("=== TEST MODE: Processing only 2 items ===\n")

    reader = OutlookReader()
    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    # Mark previous batch as done
    mark_previous_done(reader)

    # Get next batch
    listings = get_next_batch(reader, limit=batch_size)

    if not listings:
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
        print()
    print("=" * 70)

    # Open pages
    open_pages(listings)

    print("Opened in Chrome:")
    print("  - Tab 1: End Your Listing page (enter item numbers, reason: 'error in listing')")
    print("  - Tabs 2+: Item pages (click 'Sell Similar' after ending each)")
    print()
    print("When done, run this script again to mark complete and get next batch.")


if __name__ == "__main__":
    main()
