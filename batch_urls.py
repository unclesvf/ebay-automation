"""
Generate batch list of eBay edit URLs with prices
"""
from outlook_reader import OutlookReader
from email_parser import EmailParser
from config import OUTLOOK_CONFIG

def generate_batch():
    reader = OutlookReader()
    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    folder = reader.get_folder_by_name(OUTLOOK_CONFIG['folder_name'], OUTLOOK_CONFIG['account_email'])
    if not folder:
        print(f"Folder '{OUTLOOK_CONFIG['folder_name']}' not found")
        return

    emails = reader.read_emails(folder, limit=10, unread_only=True)
    print(f"Found {len(emails)} unread emails")

    parser = EmailParser()
    listings = []

    for email in emails:
        parsed = parser.parse_email(email)
        if parsed:
            listings.append({
                'entry_id': email['entry_id'],
                'item_id': parsed.item_id,
                'title': parsed.item_title[:60],
                'price': parsed.new_price,
                'edit_url': f'https://www.ebay.com/sl/list?itemId={parsed.item_id}&mode=Revise'
            })

    # Save entry_ids to file for later marking as read
    with open('pending_entries.txt', 'w', encoding='utf-8') as f:
        for l in listings:
            f.write(f"{l['entry_id']}|{l['item_id']}|{l['price']}\n")

    print(f"\nFound {len(listings)} listings to update:")
    print("=" * 70)

    for i, l in enumerate(listings, 1):
        print(f"\n[{i}] {l['title']}")
        print(f"    Set price to: ${l['price']:.2f}")
        print(f"    Edit URL: {l['edit_url']}")

    print("\n" + "=" * 70)
    print(f"\nEntry IDs saved to pending_entries.txt")
    print("After updating, run: python mark_read.py")

if __name__ == "__main__":
    generate_batch()
