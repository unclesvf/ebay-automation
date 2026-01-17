"""
eBay Listing Automation Tool
Main entry point for reading Outlook emails and managing eBay listings
"""

import sys
import time
import argparse
from typing import List

from outlook_reader import OutlookReader
from email_parser import EmailParser, EbayListingInfo
from ebay_browser import EbayBrowser
from config import OUTLOOK_CONFIG, EBAY_CONFIG, BROWSER_CONFIG, PROCESS_CONFIG
from dataclasses import dataclass


@dataclass
class ListingWithEmail:
    """Listing info paired with its source email data."""
    listing: EbayListingInfo
    entry_id: str  # Outlook email EntryID for marking as read


def print_banner():
    """Print application banner."""
    print("""
==============================================================
         eBay Listing Automation Tool
    Read Outlook emails -> Update eBay listings
==============================================================
    """)


def list_folders():
    """List all Outlook folders for configuration."""
    print("\nConnecting to Outlook...")
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook. Make sure Outlook is running.")
        return

    print("\nAvailable email accounts:")
    for acc in reader.get_accounts():
        print(f"  • {acc}")

    print("\nFolders:")
    folders = reader.get_folders(OUTLOOK_CONFIG['account_email'])
    _print_folders(folders)


def _print_folders(folder_dict, indent=0):
    """Pretty print folder structure."""
    prefix = "  " * indent
    name = folder_dict.get('name', 'Unknown')
    count = folder_dict.get('count', 0)
    print(f"{prefix}• {name} ({count} items)")
    for sub in folder_dict.get('subfolders', []):
        _print_folders(sub, indent + 1)


def get_unread_listings(reader: OutlookReader = None) -> tuple:
    """
    Get unread emails from Linda folder and parse for eBay listings.
    Returns (list of ListingWithEmail, OutlookReader instance)
    """
    if reader is None:
        reader = OutlookReader()
        if not reader.connect():
            print("Failed to connect to Outlook.")
            return [], None

    folder = reader.get_folder_by_name(
        OUTLOOK_CONFIG['folder_name'],
        OUTLOOK_CONFIG['account_email']
    )

    if not folder:
        print(f"Folder '{OUTLOOK_CONFIG['folder_name']}' not found.")
        return [], reader

    print(f"\nReading UNREAD emails from '{OUTLOOK_CONFIG['folder_name']}' folder...")
    emails = reader.read_emails(
        folder,
        limit=OUTLOOK_CONFIG['max_emails'],
        unread_only=True  # Always unread only
    )

    if not emails:
        print("No unread emails found.")
        return [], reader

    print(f"Found {len(emails)} unread email(s)")

    # Parse emails for eBay listings, keeping track of entry_id
    parser = EmailParser()
    listings_with_email = []

    for email in emails:
        parsed = parser.parse_email(email)
        if parsed:
            listings_with_email.append(ListingWithEmail(
                listing=parsed,
                entry_id=email['entry_id']
            ))

    if not listings_with_email:
        print("No eBay listings found in unread emails.")
        return [], reader

    return listings_with_email, reader


def preview_emails():
    """Preview emails that would be processed."""
    print("\nConnecting to Outlook...")
    listings_with_email, reader = get_unread_listings()

    if not listings_with_email:
        return []

    print(f"\nFound {len(listings_with_email)} eBay listing(s) to process:\n")
    print("-" * 70)

    for i, item in enumerate(listings_with_email, 1):
        listing = item.listing
        print(f"\n[{i}] {listing.item_title}")
        print(f"    Item ID: {listing.item_id}")
        print(f"    Action: {listing.action}")
        if listing.new_price:
            print(f"    New Price: ${listing.new_price:.2f}")
        print(f"    URL: {listing.item_url}")

    print("\n" + "-" * 70)
    return listings_with_email


def process_listings_interactive(listings_with_email: List[ListingWithEmail], reader: OutlookReader):
    """
    Process eBay listings one by one with process/skip choice for each.
    Marks emails as read after processing.
    """
    if not listings_with_email:
        print("No listings to process.")
        return

    print(f"\nStarting browser to process {len(listings_with_email)} listing(s)...")
    print("You'll be asked to Process or Skip each one.\n")

    browser = EbayBrowser(
        headless=BROWSER_CONFIG['headless'],
        profile_path=BROWSER_CONFIG['profile_path']
    )

    if not browser.start():
        print("Failed to start browser.")
        return

    processed_count = 0
    skipped_count = 0

    try:
        # Check/perform login
        if not browser.is_logged_in():
            print("\nNot logged into eBay.")
            if EBAY_CONFIG['username'] and EBAY_CONFIG['password']:
                print("Attempting automatic login...")
                browser.login(EBAY_CONFIG['username'], EBAY_CONFIG['password'])
            else:
                browser.login()  # Manual login

        if not browser.is_logged_in():
            print("Login failed or cancelled. Exiting.")
            return

        print("\nLogged into eBay successfully.\n")

        # Process each listing with user choice
        for i, item in enumerate(listings_with_email, 1):
            listing = item.listing

            print("\n" + "=" * 60)
            print(f"[{i}/{len(listings_with_email)}] {listing.item_title}")
            print(f"    Item ID: {listing.item_id}")
            print(f"    Action: {listing.action}")
            if listing.new_price:
                print(f"    New Price: ${listing.new_price:.2f}")
            print(f"    URL: {listing.item_url}")
            print("=" * 60)

            # Ask user what to do
            while True:
                choice = input("\n[P]rocess, [S]kip, or [Q]uit? ").strip().lower()

                if choice in ('p', 'process'):
                    # Process this listing
                    success = browser.process_listing(listing)

                    if success:
                        print("✓ Completed successfully")
                        processed_count += 1

                        # Mark email as read
                        if reader and PROCESS_CONFIG['mark_read_after_process']:
                            if reader.mark_as_read(item.entry_id):
                                print("  (Email marked as read)")
                    else:
                        print("✗ Failed or cancelled")
                    break

                elif choice in ('s', 'skip'):
                    print("Skipped.")
                    skipped_count += 1
                    break

                elif choice in ('q', 'quit'):
                    print("\nQuitting early.")
                    print(f"\nSummary: {processed_count} processed, {skipped_count} skipped, {len(listings_with_email) - i} remaining")
                    return

                else:
                    print("Invalid choice. Enter P, S, or Q.")

            # Pause between items
            if i < len(listings_with_email):
                time.sleep(PROCESS_CONFIG['pause_between_items'])

        print("\n" + "=" * 60)
        print(f"Done! Processed: {processed_count}, Skipped: {skipped_count}")
        print("=" * 60)

    finally:
        input("\nPress Enter to close browser...")
        browser.close()


def interactive_mode():
    """Run in interactive mode with menu."""
    reader = OutlookReader()
    if not reader.connect():
        print("Failed to connect to Outlook. Make sure Outlook is running.")
        return

    listings_with_email = []

    while True:
        print("\n" + "=" * 50)
        print("MENU")
        print("=" * 50)
        print("1. List Outlook folders")
        print("2. Preview unread emails from Linda folder")
        print("3. Process listings (one by one with Process/Skip)")
        print("4. Open eBay item in browser")
        print("0. Exit")
        print("-" * 50)

        choice = input("Enter choice: ").strip()

        if choice == '1':
            list_folders()

        elif choice == '2':
            listings_with_email, reader = get_unread_listings(reader)
            if listings_with_email:
                print(f"\nFound {len(listings_with_email)} eBay listing(s):\n")
                print("-" * 70)
                for i, item in enumerate(listings_with_email, 1):
                    listing = item.listing
                    print(f"\n[{i}] {listing.item_title}")
                    print(f"    Item ID: {listing.item_id}")
                    if listing.new_price:
                        print(f"    New Price: ${listing.new_price:.2f}")
                print("\n" + "-" * 70)

        elif choice == '3':
            if not listings_with_email:
                listings_with_email, reader = get_unread_listings(reader)
            if listings_with_email:
                process_listings_interactive(listings_with_email, reader)
                listings_with_email = []  # Clear after processing

        elif choice == '4':
            item_id = input("Enter eBay item ID or URL: ").strip()
            if 'ebay.com' in item_id:
                import re
                match = re.search(r'/itm/(\d+)', item_id)
                if match:
                    item_id = match.group(1)

            if item_id.isdigit():
                browser = EbayBrowser()
                if browser.start():
                    browser.navigate_to_item(f"https://www.ebay.com/itm/{item_id}")
                    input("Press Enter to close browser...")
                    browser.close()

        elif choice == '0':
            print("\nGoodbye!")
            break

        else:
            print("Invalid choice.")


def main():
    """Main entry point."""
    arg_parser = argparse.ArgumentParser(description='eBay Listing Automation Tool')
    arg_parser.add_argument('--list-folders', action='store_true',
                            help='List Outlook folders')
    arg_parser.add_argument('--preview', action='store_true',
                            help='Preview unread emails without processing')

    args = arg_parser.parse_args()

    print_banner()

    if args.list_folders:
        list_folders()
    elif args.preview:
        preview_emails()
    else:
        # Default to interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
