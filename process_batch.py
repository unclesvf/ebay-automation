"""
Process a batch: mark previous as read, get next batch, open in Chrome
"""
import os
import subprocess
from outlook_reader import OutlookReader
from email_parser import EmailParser
from config import OUTLOOK_CONFIG

PENDING_FILE = os.path.join(os.path.dirname(__file__), 'pending_entries.txt')
COMPLETED_FILE = os.path.join(os.path.dirname(__file__), 'completed_items.txt')


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

def mark_previous_read(reader):
    """Mark previous batch emails as read and log as completed."""
    if not os.path.exists(PENDING_FILE):
        return 0

    with open(PENDING_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return 0

    completed_ids = []
    count = 0
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) >= 2:
            entry_id = parts[0]
            item_id = parts[1]
            completed_ids.append(item_id)
            try:
                if reader.mark_as_read(entry_id):
                    count += 1
            except:
                pass  # Continue even if marking fails

    # Always save to completed file
    save_completed(completed_ids)
    print(f"Saved {len(completed_ids)} items to completed log")

    os.remove(PENDING_FILE)
    return count

def get_next_batch(reader, limit=10):
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
        if parsed:
            # Skip if already completed
            if parsed.item_id in completed:
                continue
            listings.append({
                'entry_id': email['entry_id'],
                'item_id': parsed.item_id,
                'title': parsed.item_title[:50],
                'price': parsed.new_price,
            })

    # Save for next time
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        for l in listings:
            f.write(f"{l['entry_id']}|{l['item_id']}|{l['price']}\n")

    return listings

def open_in_chrome(listings):
    """Open item pages in Chrome."""
    urls = [f"https://www.ebay.com/itm/{l['item_id']}" for l in listings]
    cmd = ['start', 'chrome'] + urls
    subprocess.run(' '.join(cmd), shell=True)

def main():
    reader = OutlookReader()
    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    # Mark previous batch as read
    marked = mark_previous_read(reader)
    if marked:
        print(f"Marked {marked} previous emails as read")

    # Get next batch (reduced to 5 to be gentler on Outlook)
    listings = get_next_batch(reader, limit=5)

    if not listings:
        print("No more unread emails with eBay listings!")
        return

    print(f"\nNext batch: {len(listings)} listings\n")
    print("=" * 60)
    for i, l in enumerate(listings, 1):
        print(f"[{i}] {l['title']}")
        if l['price'] is not None:
            print(f"    Price: ${l['price']:.2f}")
        else:
            print(f"    Price: (check email)")
    print("=" * 60)

    # Open in Chrome
    open_in_chrome(listings)
    print("\nOpened in Chrome. Update prices, then run this script again for next batch.")

if __name__ == "__main__":
    main()
