"""
Full analysis of Scott folder and all subfolders in Outlook
"""

import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from datetime import datetime

def analyze_full_scott_folder():
    reader = OutlookReader()

    if not reader.connect():
        print("Failed to connect to Outlook")
        return

    print("=" * 80)
    print(f"SCOTT FOLDER ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)

    folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

    if not folder:
        print("Could not find 'scott' folder")
        return

    # Count items in main folder
    main_count = folder.Items.Count
    print(f"\nMain 'Scott' folder: {main_count} items")

    # Analyze subfolders
    print("\n" + "-" * 80)
    print("SUBFOLDERS")
    print("-" * 80)
    print(f"{'Subfolder':<35} {'Count':>8}  {'Newest Email':>15}")
    print("-" * 60)

    total_subfolder_items = 0
    subfolder_data = []

    for subfolder in folder.Folders:
        count = subfolder.Items.Count
        total_subfolder_items += count

        # Get newest email date
        newest_date = "N/A"
        if count > 0:
            items = subfolder.Items
            items.Sort("[ReceivedTime]", True)
            try:
                newest = items.GetFirst()
                if newest and hasattr(newest, 'ReceivedTime'):
                    newest_date = str(newest.ReceivedTime)[:10]
            except:
                pass

        subfolder_data.append({
            'name': subfolder.Name,
            'count': count,
            'newest': newest_date
        })

    # Sort by count descending
    subfolder_data.sort(key=lambda x: -x['count'])

    for sf in subfolder_data:
        print(f"{sf['name']:<35} {sf['count']:>8}  {sf['newest']:>15}")

    print("-" * 60)
    print(f"{'TOTAL IN SUBFOLDERS':<35} {total_subfolder_items:>8}")
    print(f"{'TOTAL IN MAIN FOLDER':<35} {main_count:>8}")
    print(f"{'GRAND TOTAL':<35} {total_subfolder_items + main_count:>8}")

    # Sample emails from main folder
    if main_count > 0:
        print("\n" + "-" * 80)
        print("EMAILS IN MAIN FOLDER (not yet categorized)")
        print("-" * 80)

        items = folder.Items
        items.Sort("[ReceivedTime]", True)

        count = 0
        for item in items:
            if item.Class != 43:
                continue
            count += 1
            if count > 20:
                print(f"  ... and {main_count - 20} more")
                break

            subject = item.Subject or '(no subject)'
            date_str = str(item.ReceivedTime)[:10]
            print(f"  [{date_str}] {subject[:60]}")

    print("\n" + "=" * 80)
    print("END OF ANALYSIS")
    print("=" * 80)

if __name__ == "__main__":
    analyze_full_scott_folder()
