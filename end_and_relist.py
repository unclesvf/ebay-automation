"""
End and Relist Script
Workflow: End listing via eBay help page, then Sell Similar with new price

Usage:
    python end_and_relist.py              # Show current batch (does NOT mark anything complete)
    python end_and_relist.py --done       # Mark previous batch complete, then show next batch
    python end_and_relist.py --test       # Test with just 2 items
    python end_and_relist.py --batch N    # Set custom batch size (e.g., --batch 10)
    python end_and_relist.py --instructions  # Process instruction emails (bulk changes)
    python end_and_relist.py --stats      # Show processing statistics
    python end_and_relist.py --undo ID1 ID2  # Remove items from completed (for reprocessing)

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
TITLE_PENDING_FILE = os.path.join(os.path.dirname(__file__), 'title_pending_entries.txt')
COMPLETED_FILE = os.path.join(os.path.dirname(__file__), 'completed_items.txt')
STATS_FILE = os.path.join(os.path.dirname(__file__), 'stats.txt')
GALLERY_INFO_DIR = os.path.join(os.path.dirname(__file__), 'gallery_info')
END_LISTING_URL = "https://www.ebay.com/help/action?topicid=4146"
BUYER_BLOCK_URL = "https://www.ebay.com/bmgt/BuyerBlock"


def has_gallery_photo_instruction(listing):
    """Check if a listing has gallery photo change instructions."""
    notes_text = ' '.join(listing.get('notes', []) or []).lower()
    body_text = listing.get('body_preview', '').lower()
    return 'gallery photo' in notes_text or 'gallery photo' in body_text


def create_gallery_info_page(listing):
    """Create an HTML info page for gallery photo instructions."""
    import re

    # Ensure directory exists
    if not os.path.exists(GALLERY_INFO_DIR):
        os.makedirs(GALLERY_INFO_DIR)

    item_id = listing['item_id']
    title = listing.get('title', 'Unknown Item')
    body = listing.get('body_preview', 'No email body available')
    notes = listing.get('notes', []) or []

    # Extract image URLs from the body (eBay image URLs)
    image_urls = re.findall(r'https?://i\.ebayimg\.com/images/[^\s<>"\']+', body)
    # Also check for URLs in angle brackets like <https://...>
    bracketed_urls = re.findall(r'<(https?://i\.ebayimg\.com/images/[^>]+)>', body)
    image_urls.extend(bracketed_urls)
    # Remove duplicates while preserving order
    seen = set()
    unique_images = []
    for url in image_urls:
        if url not in seen:
            seen.add(url)
            unique_images.append(url)

    # Build image HTML
    images_html = ""
    if unique_images:
        images_html = '<div class="images"><h3>Photo to Use as Gallery Photo:</h3>'
        for img_url in unique_images:
            # Convert thumbnail URL to larger version if possible
            large_url = img_url.replace('/s-l140.', '/s-l500.').replace('/s-l64.', '/s-l500.')
            images_html += f'<img src="{large_url}" alt="Gallery photo" style="max-width:100%; border:2px solid #ff6600; border-radius:8px; margin:10px 0;">'
        images_html += '</div>'

    # Escape HTML in body (but preserve line breaks)
    body_escaped = body.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>')

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Gallery Photo Info - {item_id}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: #ff6600;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .info-box {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .info-box h2 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #ff6600;
            padding-bottom: 10px;
        }}
        .item-id {{
            font-family: monospace;
            font-size: 18px;
            background: #eee;
            padding: 5px 10px;
            border-radius: 4px;
        }}
        .notes {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .email-body {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #ddd;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 14px;
        }}
        .action {{
            background: #d4edda;
            border: 1px solid #28a745;
            padding: 15px;
            border-radius: 4px;
            font-weight: bold;
            color: #155724;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>GALLERY PHOTO CHANGE REQUIRED</h1>
    </div>

    <div class="info-box">
        <h2>Item Details</h2>
        <p><strong>Item ID:</strong> <span class="item-id">{item_id}</span></p>
        <p><strong>Title:</strong> {title}</p>
    </div>

    <div class="info-box">
        <h2>Instructions from Linda</h2>
        <div class="notes">
            {('<br>'.join(notes)) if notes else 'See email body below for instructions'}
        </div>
        {images_html}
    </div>

    <div class="info-box">
        <h2>Email Body</h2>
        <div class="email-body">{body_escaped}</div>
    </div>

    <div class="info-box">
        <div class="action">
            Next tab: eBay item page - Click "Sell Similar" and update the gallery photo as instructed above
        </div>
    </div>
</body>
</html>"""

    filepath = os.path.join(GALLERY_INFO_DIR, f"gallery_info_{item_id}.html")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return filepath


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
    # Update stats
    update_stats(len(item_ids))


def remove_from_completed(item_ids):
    """Remove item IDs from completed file (for undo)."""
    if not os.path.exists(COMPLETED_FILE):
        return 0

    with open(COMPLETED_FILE, 'r', encoding='utf-8') as f:
        existing = [line.strip() for line in f if line.strip()]

    removed = 0
    new_list = []
    for item_id in existing:
        if item_id in item_ids:
            removed += 1
        else:
            new_list.append(item_id)

    with open(COMPLETED_FILE, 'w', encoding='utf-8') as f:
        for item_id in new_list:
            f.write(f"{item_id}\n")

    return removed


def update_stats(count):
    """Update statistics file with processing count."""
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')

    # Load existing stats
    stats = {}
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if '|' in line:
                    date, cnt = line.strip().split('|')
                    stats[date] = int(cnt)

    # Update today's count
    stats[today] = stats.get(today, 0) + count

    # Save stats
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        for date in sorted(stats.keys()):
            f.write(f"{date}|{stats[date]}\n")


def load_pending_items():
    """Load pending items from both pending files for verification display."""
    pending_items = []

    # Load price pending items
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    pending_items.append({
                        'entry_id': parts[0],
                        'item_id': parts[1],
                        'price': parts[2],
                        'type': 'PRICE'
                    })

    # Load title-only pending items
    if os.path.exists(TITLE_PENDING_FILE):
        with open(TITLE_PENDING_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) >= 2:
                    pending_items.append({
                        'entry_id': parts[0],
                        'item_id': parts[1],
                        'price': 'TITLE_ONLY',
                        'type': 'TITLE'
                    })

    return pending_items


def show_pending_verification_table():
    """Display pending items in a table for user verification."""
    pending_items = load_pending_items()

    if not pending_items:
        return False

    print()
    print("=" * 70)
    print("PENDING ITEMS FROM PREVIOUS BATCH - Please verify these are done:")
    print("=" * 70)
    print()
    print("+-----+-----------------+----------------+--------+")
    print("|  #  | Item ID         | Price          | Type   |")
    print("+-----+-----------------+----------------+--------+")

    for i, item in enumerate(pending_items, 1):
        price_display = item['price'] if item['price'] != 'TITLE_ONLY' else '(title only)'
        if price_display not in ['CURRENT', '(title only)']:
            try:
                price_display = f"${float(price_display):.2f}"
            except (ValueError, TypeError):
                pass
        print(f"| {i:<3} | {item['item_id']:<15} | {price_display:<14} | {item['type']:<6} |")

    print("+-----+-----------------+----------------+--------+")
    print()
    print("If these items are DONE: run with --done flag to mark complete")
    print("If NOT done: process them now, then run --done")
    print()
    print("eBay links for verification:")
    for item in pending_items:
        print(f"  https://www.ebay.com/itm/{item['item_id']}")
    print()
    print("=" * 70)
    print()

    return True


def show_stats():
    """Display processing statistics."""
    from datetime import datetime, timedelta

    if not os.path.exists(STATS_FILE):
        print("No statistics available yet.")
        return

    stats = {}
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if '|' in line:
                date, cnt = line.strip().split('|')
                stats[date] = int(cnt)

    if not stats:
        print("No statistics available yet.")
        return

    today = datetime.now().strftime('%Y-%m-%d')
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    # Calculate totals
    total = sum(stats.values())
    today_count = stats.get(today, 0)
    week_count = sum(cnt for date, cnt in stats.items() if date >= week_ago)

    print()
    print("=" * 40)
    print("PROCESSING STATISTICS")
    print("=" * 40)
    print(f"  Today:      {today_count} items")
    print(f"  This week:  {week_count} items")
    print(f"  All time:   {total} items")
    print()
    print("Recent activity:")
    for date in sorted(stats.keys(), reverse=True)[:7]:
        print(f"  {date}: {stats[date]} items")
    print("=" * 40)


def mark_previous_done(reader):
    """Mark previous batch emails as read and log as completed."""
    total_completed = 0

    # Process price listings pending file
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if lines:
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
                print(f"Saved {len(completed_ids)} price items to completed log")
                total_completed += len(completed_ids)

            if marked_count:
                print(f"Marked {marked_count} price emails as read")

        os.remove(PENDING_FILE)

    # Process title-only listings pending file
    if os.path.exists(TITLE_PENDING_FILE):
        with open(TITLE_PENDING_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if lines:
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
                print(f"Saved {len(completed_ids)} title-only items to completed log")
                total_completed += len(completed_ids)

            if marked_count:
                print(f"Marked {marked_count} title-only emails as read")

        os.remove(TITLE_PENDING_FILE)

    return total_completed


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
    title_only_listings = []  # Emails with eBay URL but no price (title change only)
    instruction_emails = []  # Emails without eBay URLs (instructions from Linda)

    # Track items that have newer unread emails (already completed but Linda sent follow-up)
    follow_up_items = []

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
        if parsed and (parsed.new_price is not None or parsed.relist_current_price):
            # Check if already completed - but detect follow-up emails
            if parsed.item_id in completed:
                # This is a NEW unread email for an already-completed item
                # Linda sent a follow-up with different instructions!
                follow_up_items.append(parsed.item_id)
                # Remove from completed so it gets processed
                completed.discard(parsed.item_id)
            listings.append({
                'entry_id': email['entry_id'],
                'item_id': parsed.item_id,
                'title': parsed.item_title,
                'price': parsed.new_price,  # None means use current price
                'relist_current_price': parsed.relist_current_price,
                'is_price_revision': parsed.is_price_revision,  # True = REVISE, False = END & RELIST
                'quantity': parsed.quantity,
                'notes': parsed.notes,
                'blue_text': parsed.blue_text,
                'red_text': parsed.red_text,
                'needs_review': parsed.needs_review,
                'body_preview': email.get('body', '')[:500],  # Store preview for review
                'buyer_username': parsed.buyer_username,
                'suspected_new_title': parsed.suspected_new_title,
            })
        elif parsed and parsed.new_price is None and not parsed.relist_current_price:
            # Has eBay URL but no price - title/header change only
            if parsed.item_id in completed:
                follow_up_items.append(parsed.item_id)
                completed.discard(parsed.item_id)
            title_only_listings.append({
                'entry_id': email['entry_id'],
                'item_id': parsed.item_id,
                'title': parsed.item_title,
                'notes': parsed.notes,
                'blue_text': parsed.blue_text,
                'red_text': parsed.red_text,
                'new_title': parsed.new_title,
                'body_preview': email.get('body', '')[:500],
                'suspected_new_title': parsed.suspected_new_title,
            })
        elif not parsed:
            # No eBay URL found - might be an instruction email from Linda
            instruction_emails.append({
                'subject': subject,
                'body': email.get('body', '')[:300],
                'entry_id': email['entry_id'],
            })

    # If we found follow-up emails, update the completed file and notify user
    if follow_up_items:
        print(f"\n*** FOLLOW-UP EMAILS DETECTED ***")
        print(f"Found {len(follow_up_items)} item(s) with NEW instructions from Linda:")
        for item_id in follow_up_items:
            print(f"  - {item_id}")
        print("These items were already completed but have new unread emails.")
        print("Removing from completed list and processing the new instructions.\n")
        # Update the completed file
        remove_from_completed(follow_up_items)

    # Save pending entries for next run (price update listings)
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        for l in listings:
            price_str = l['price'] if l['price'] is not None else 'CURRENT'
            f.write(f"{l['entry_id']}|{l['item_id']}|{price_str}\n")

    # Save title-only pending entries (now also tracked by --done)
    with open(TITLE_PENDING_FILE, 'w', encoding='utf-8') as f:
        for l in title_only_listings:
            f.write(f"{l['entry_id']}|{l['item_id']}|TITLE_ONLY\n")

    return listings, title_only_listings, instruction_emails


def open_pages(listings, buyers_to_block=None):
    """Open End Listing page and item pages in Chrome."""
    # First, open the End Your Listing page
    urls = [END_LISTING_URL]

    # Open buyer block page if there are buyers to block
    if buyers_to_block:
        urls.append(BUYER_BLOCK_URL)

    # Track which items have gallery photo info pages
    gallery_photo_items = []

    # Then open each item page (for Sell Similar after ending)
    # For gallery photo items, open an info page BEFORE the item page
    for l in listings:
        if has_gallery_photo_instruction(l):
            # Create and add gallery info page before the item page
            info_path = create_gallery_info_page(l)
            urls.append(f"file:///{info_path.replace(os.sep, '/')}")
            gallery_photo_items.append(l['item_id'])
        urls.append(f"https://www.ebay.com/itm/{l['item_id']}")

    cmd = ['start', 'chrome'] + urls
    subprocess.run(' '.join(cmd), shell=True)

    return gallery_photo_items


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


def handle_undo(reader, item_ids):
    """Handle undo - remove items from completed and mark emails as unread."""
    if not item_ids:
        print("Usage: python end_and_relist.py --undo ITEM_ID1 ITEM_ID2 ...")
        return

    print(f"Attempting to undo {len(item_ids)} items...")

    # Remove from completed file
    removed = remove_from_completed(item_ids)
    print(f"  Removed {removed} items from completed log")

    # Note: We can't easily mark the emails as unread without knowing their entry_ids
    # But at least they're removed from completed so they'll be processed again
    print(f"\nItems removed from completed list. They will be processed again")
    print("if their emails are still unread in Outlook.")
    print("\nIf the emails are already marked as read, you may need to")
    print("manually mark them as unread in Outlook.")


def parse_batch_size(args):
    """Parse batch size from command line args."""
    for i, arg in enumerate(args):
        if arg == '--batch' and i + 1 < len(args):
            try:
                return int(args[i + 1])
            except ValueError:
                print(f"Invalid batch size: {args[i + 1]}")
                return None
    return None


def main():
    # Check for flags
    test_mode = '--test' in sys.argv
    mark_done = '--done' in sys.argv
    instructions_mode = '--instructions' in sys.argv
    stats_mode = '--stats' in sys.argv
    undo_mode = '--undo' in sys.argv

    # Parse batch size (default: 5, test mode: 2)
    custom_batch = parse_batch_size(sys.argv)
    if custom_batch is not None:
        batch_size = custom_batch
    elif test_mode:
        batch_size = 2
    else:
        batch_size = 5

    if test_mode:
        print("=== TEST MODE: Processing only 2 items ===\n")

    # Stats mode doesn't need Outlook
    if stats_mode:
        show_stats()
        return

    reader = OutlookReader()
    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    # Handle undo mode
    if undo_mode:
        # Get item IDs from args after --undo
        try:
            undo_idx = sys.argv.index('--undo')
            item_ids = sys.argv[undo_idx + 1:]
            # Filter out other flags
            item_ids = [x for x in item_ids if not x.startswith('--')]
        except (ValueError, IndexError):
            item_ids = []
        handle_undo(reader, item_ids)
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
    else:
        # Show pending items verification table if there are pending items
        show_pending_verification_table()

    # Get next batch
    listings, title_only_listings, instruction_emails = get_next_batch(reader, limit=batch_size)

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

    # Show title-only changes (no price change AND no "List new" - just revise title/description)
    if title_only_listings:
        print()
        print("*" * 70)
        print("TITLE REVISIONS (use REVISE in eBay)")
        print("*" * 70)

        # Determine action for each item
        def get_action(l):
            """Determine the action to display for a title-only listing."""
            body_lower = l.get('body_preview', '').lower()
            # Check for "remove this listing" type instructions
            if 'remove this listing' in body_lower or 'remove listing' in body_lower:
                return ("END LISTING", "Remove/end this listing (keep the other one)")
            # Check for blue text (specific new title)
            if l.get('blue_text'):
                return ("NEW TITLE", l['blue_text'][0])
            # Check for new_title
            if l.get('new_title'):
                return ("NEW TITLE", l['new_title'])
            # Check for "add silver after sterling" pattern
            if 'add' in body_lower and 'silver' in body_lower and 'sterling' in body_lower:
                return ("ADD SILVER", "Add 'Silver' after 'Sterling'")
            # Check notes
            if l.get('notes'):
                return ("OTHER", l['notes'][0])
            # Try to extract new title from body (first non-URL line after blank)
            body_lines = l.get('body_preview', '').strip().split('\n')
            new_title_lines = []
            for line in body_lines:
                line = line.strip()
                if line and not line.startswith('http') and 'ebay.com' not in line.lower():
                    new_title_lines.append(line)
                if len(new_title_lines) >= 2:
                    break
            if new_title_lines:
                return ("NEW TITLE", ' '.join(new_title_lines))
            return ("CHECK EMAIL", "Check email for instructions")

        # Add action info to each listing
        for l in title_only_listings:
            action_type, action_detail = get_action(l)
            l['action_type'] = action_type
            l['action_detail'] = action_detail

        # Group by action type and sort: ADD SILVER first (most common), then others
        action_order = ["ADD SILVER", "NEW TITLE", "END LISTING", "OTHER", "CHECK EMAIL"]
        sorted_listings = sorted(title_only_listings,
                                  key=lambda x: (action_order.index(x['action_type'])
                                                if x['action_type'] in action_order else 99))

        # Open Chrome tabs in GROUPED order
        title_urls = [f"https://www.ebay.com/itm/{l['item_id']}" for l in sorted_listings]
        cmd = ['start', 'chrome'] + title_urls
        subprocess.run(' '.join(cmd), shell=True)

        # Build the table data with tab numbers
        table_data = []
        for tab_num, l in enumerate(sorted_listings, 1):
            # Determine action text
            if l['action_type'] == "ADD SILVER":
                action_text = "Add 'Silver' after 'Sterling'"
            elif l['action_type'] == "NEW TITLE":
                action_text = "NEW TITLE: " + l['action_detail'].replace('\n', ' ')
            elif l['action_type'] == "END LISTING":
                action_text = "END/REMOVE THIS LISTING"
            else:
                action_text = l['action_detail']

            table_data.append({
                'tab': tab_num,
                'item_id': l['item_id'],
                'title': l['title'],
                'action': action_text,
                'item_type': "REVISE" if l['action_type'] != "END LISTING" else "END"
            })

        # Print compact format - 3 lines per item
        print()
        for row in table_data:
            print(f"[{row['tab']}] {row['item_id']} | {row['item_type']}")
            print(f"    TITLE:  {row['title']}")
            print(f"    ACTION: {row['action']}")
            print()
        print()
        print(f"Total: {len(sorted_listings)} title revisions | Chrome tabs match table order above")
        print("These items will be marked complete when you run: --done")
        print("*" * 70)
        print()

    if not listings:
        if title_only_listings:
            print("No price-change listings. Title-only changes shown above.")
            print("\nWhen done, run: python end_and_relist.py --done")
        elif instruction_emails:
            print("No eBay listings to process, but please review the instruction emails above.")
        else:
            print("No more unread emails with eBay price updates!")
        return

    # Check for buyers to block
    buyers_to_block = []
    for l in listings:
        notes_text = ' '.join(l.get('notes', []) or []).lower()
        title_text = l.get('title', '').lower()
        if 'block' in notes_text or 'block' in title_text:
            if l.get('buyer_username'):
                buyers_to_block.append({
                    'username': l['buyer_username'],
                    'item_id': l['item_id'],
                    'title': l['title']
                })

    # Display buyers to block first (important!)
    if buyers_to_block:
        print()
        print("!" * 70)
        print("BUYERS TO BLOCK (copy username to Block Buyer page):")
        print("!" * 70)
        for b in buyers_to_block:
            print(f"\n  Username: {b['username']}")
            print(f"  Item: {b['item_id']} - {b['title'][:40]}")
        print()
        print("!" * 70)
        print()

    # Split listings into REVISE (price changes) and END & RELIST
    price_revisions = [l for l in listings if l.get('is_price_revision')]
    end_relist_items = [l for l in listings if not l.get('is_price_revision')]

    # ===== PRICE REVISIONS (just change the price) =====
    if price_revisions:
        print()
        print("#" * 60)
        print("PRICE REVISIONS (just REVISE the price - do NOT end listing)")
        print("#" * 60)
        print()

        # Open just the item pages for revision
        revision_urls = [f"https://www.ebay.com/itm/{l['item_id']}" for l in price_revisions]
        cmd = ['start', 'chrome'] + revision_urls
        subprocess.run(' '.join(cmd), shell=True)

        for i, l in enumerate(price_revisions, 1):
            price_str = f"${l['price']:.2f}" if l['price'] else "(Current)"
            print(f"[{i}] {l['item_id']} | NEW PRICE: {price_str} | REVISE")
            print(f"    TITLE:  {l['title']}")
            action_parts = []
            if l.get('notes'):
                action_parts.append('; '.join(l['notes']))
            if l.get('new_title'):
                action_parts.append(f"NEW TITLE: {l['new_title']}")
            if l.get('blue_text'):
                for bt in l['blue_text']:
                    action_parts.append(f"USE TITLE: {bt}")
            if action_parts:
                print(f"    ACTION: {'; '.join(action_parts)}")
            # Show suspected title if Linda forgot blue text
            if l.get('suspected_new_title') and not l.get('blue_text') and not l.get('new_title'):
                print(f"    *** SUSPECTED TITLE (not blue): {l['suspected_new_title']}")
            print()

        print(f"Opened {len(price_revisions)} tabs - REVISE price only (do NOT end)")
        print()

    # ===== END & RELIST ITEMS =====
    if end_relist_items:
        print()
        print("#" * 60)
        print("END & RELIST ITEMS (End listing, then 'Sell Similar')")
        print("#" * 60)
        print()

        # Item numbers to copy
        print("ITEM NUMBERS TO COPY TO 'END YOUR LISTING' PAGE:")
        print("+" + "-"*16 + "+")
        for l in end_relist_items:
            print(f"| {l['item_id']:<14} |")
        print("+" + "-"*16 + "+")
        print()

        for i, l in enumerate(end_relist_items, 1):
            price_str = f"${l['price']:.2f}" if l['price'] else "(Current)"
            print(f"[{i}] {l['item_id']} | NEW PRICE: {price_str} | LIST NEW")
            print(f"    TITLE:  {l['title']}")
            action_parts = []
            if l.get('notes'):
                action_parts.append('; '.join(l['notes']))
            if l.get('buyer_username'):
                action_parts.append(f"BLOCK: {l['buyer_username']}")
            if l.get('blue_text'):
                for bt in l['blue_text']:
                    action_parts.append(f"USE TITLE: {bt}")
            if action_parts:
                print(f"    ACTION: {'; '.join(action_parts)}")
            # Show suspected title if Linda forgot blue text
            if l.get('suspected_new_title') and not l.get('blue_text'):
                print(f"    *** SUSPECTED TITLE (not blue): {l['suspected_new_title']}")
            print()

        # Open pages for end & relist
        gallery_photo_items = open_pages(end_relist_items, buyers_to_block)

        print("Opened in Chrome:")
        print("  - Tab 1: End Your Listing page")
        tab_num = 2
        if buyers_to_block:
            print(f"  - Tab {tab_num}: Buyer Block page")
            tab_num += 1
        if gallery_photo_items:
            print(f"  - Gallery photo info pages opened BEFORE these items: {', '.join(gallery_photo_items)}")
            print(f"  - Tabs {tab_num}+: Item pages with gallery info tabs preceding them")
        else:
            print(f"  - Tabs {tab_num}+: Item pages (click 'Sell Similar' after ending)")

    print()
    print("When done, run: python end_and_relist.py --done")


if __name__ == "__main__":
    main()
