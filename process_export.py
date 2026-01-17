"""
Process the email export from VBA macro
Opens eBay items in Chrome and tracks completed items
"""
import os
import subprocess

SCRIPT_DIR = os.path.dirname(__file__)
EXPORT_FILE = os.path.join(SCRIPT_DIR, 'email_export.txt')
COMPLETED_FILE = os.path.join(SCRIPT_DIR, 'completed_items.txt')
PENDING_FILE = os.path.join(SCRIPT_DIR, 'pending_batch.txt')


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


def load_export():
    """Load emails from VBA export file."""
    if not os.path.exists(EXPORT_FILE):
        print(f"Export file not found: {EXPORT_FILE}")
        print("Run the VBA macro in Outlook first!")
        return []

    listings = []
    with open(EXPORT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('|')
            if len(parts) >= 2:
                item_id = parts[0].strip()
                price = parts[1].strip()
                title = parts[2].strip() if len(parts) > 2 else ""
                if item_id:
                    listings.append({
                        'item_id': item_id,
                        'price': price,
                        'title': title
                    })
    return listings


def get_next_batch(limit=5):
    """Get next batch of items to process."""
    completed = load_completed()
    all_listings = load_export()

    # Filter out completed items
    pending = [l for l in all_listings if l['item_id'] not in completed]

    # Get next batch
    batch = pending[:limit]

    # Save to pending file
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        for l in batch:
            f.write(f"{l['item_id']}|{l['price']}|{l['title']}\n")

    return batch, len(pending)


def mark_batch_complete():
    """Mark the current pending batch as complete."""
    if not os.path.exists(PENDING_FILE):
        return 0

    item_ids = []
    with open(PENDING_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if parts[0]:
                item_ids.append(parts[0])

    save_completed(item_ids)
    os.remove(PENDING_FILE)
    return len(item_ids)


def open_in_chrome(listings):
    """Open item pages in Chrome."""
    if not listings:
        return
    urls = [f"https://www.ebay.com/itm/{l['item_id']}" for l in listings]
    cmd = ['start', 'chrome'] + urls
    subprocess.run(' '.join(cmd), shell=True)


def main():
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'done':
        # Mark previous batch as complete and get next
        marked = mark_batch_complete()
        if marked:
            print(f"Marked {marked} items as complete")

    batch, remaining = get_next_batch(limit=5)

    if not batch:
        print("No more items to process!")
        return

    print(f"\nNext batch: {len(batch)} items ({remaining} total remaining)\n")
    print("=" * 60)
    for i, l in enumerate(batch, 1):
        price_str = f"${float(l['price']):,.2f}" if l['price'] else "N/A"
        print(f"[{i}] {l['title']}")
        print(f"    Price: {price_str}")
    print("=" * 60)

    open_in_chrome(batch)
    print("\nOpened in Chrome. When done, run:")
    print("  python process_export.py done")


if __name__ == "__main__":
    main()
