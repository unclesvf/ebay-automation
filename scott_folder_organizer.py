"""
Scott Folder Organizer - Analyze, organize, and extract insights
"""
import sys
sys.path.insert(0, r'C:\Users\scott\ebay-automation')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from outlook_reader import OutlookReader
from datetime import datetime
import re

# Mapping of keywords to subfolder names
SUBFOLDER_RULES = {
    'AI Art-Images': ['midjourney', 'dalle', 'stable diffusion', 'image generat', 'ai art', 'flux', 'ideogram'],
    'AI Agents': ['ai agent', 'autonomous agent', 'agent framework'],
    'AI Music-Audio': ['suno', 'udio', 'music ai', 'audio ai', 'voice clone'],
    'Business Docs': ['invoice', 'contract', 'agreement', 'business plan'],
    'ChatGPT-OpenAI': ['chatgpt', 'openai', 'gpt-4', 'gpt4', 'dall-e'],
    'Claude-Anthropic': ['claude', 'anthropic', 'sonnet', 'haiku', 'opus'],
    'Coding-Development': ['github', 'python', 'javascript', 'coding', 'programming', 'developer'],
    'Coins-Numismatics': ['coin', 'numismatic', 'silver', 'gold', 'bullion', 'mint'],
    'eBay Related': ['ebay', 'listing', 'auction', 'buyer', 'seller'],
    'eBay-Auction Photos': ['auction photo', 'ebay photo', 'product photo'],
    'Engraving-Laser': ['laser', 'engrav', 'xtool', 'lightburn', 'opa', 'fiber laser',
                        'co2 laser', '3d engrav', 'coin engrav', 'creative space'],
    'Adobe-Editing': ['lightroom', 'photoshop', 'firefly', 'adobe creative', 'adobe cc'],
    'HiggsField': ['higgsfield', 'nanobanana', 'higgs field'],
    'Grok-xAI': ['grok imagine', 'grok image', 'grok ai', 'xai'],
    'Fadal': ['fadal', 'cnc', 'machining'],
    'General AI': ['artificial intelligence', 'machine learning', 'llm', 'neural', 'deep learning'],
    'GitHub Projects': ['repository', 'pull request', 'commit', 'github.com'],
    'Google-Gemini': ['gemini', 'google ai', 'bard', 'google brain'],
    'History Project': ['history', 'historical', 'genealogy'],
    'Medical-Personal': ['medical', 'health', 'doctor', 'prescription'],
    'Mint Asset Sale': ['mint asset', 'asset sale'],
    'NotebookLM': ['notebooklm', 'notebook lm'],
    'Outlook-Email': ['outlook', 'email setup', 'mail config'],
    'Personal-Family': ['family', 'personal', 'birthday', 'holiday'],
    'Pricing-Plans': ['pricing', 'subscription', 'plan', 'tier'],
    'Reddit Posts': ['reddit', 'r/'],
    'Short Notes': [],  # Manual only
    'Software-Apps': ['software', 'application', 'app', 'tool', 'utility'],
    'X-Twitter Posts': ['x.com', 'twitter.com', 'tweet', '@'],
    'YouTube Videos': ['youtube', 'youtu.be', 'video'],
}

def categorize_email(subject, body):
    """Determine the best subfolder for an email based on content."""
    subject = subject or ''
    body = body or ''
    text = f"{subject} {body}".lower()

    # Check X-Twitter first (high priority)
    if 'x.com' in text or 'twitter.com' in text or text.count('@') >= 2:
        return 'X-Twitter Posts'

    # Check other categories
    for folder, keywords in SUBFOLDER_RULES.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return folder

    return 'Other-Misc'

def analyze_and_organize():
    reader = OutlookReader()

    if not reader.connect():
        print("ERROR: Failed to connect to Outlook")
        return

    print("=" * 80)
    print(f"SCOTT FOLDER ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)

    folder = reader.get_folder_by_name("scott", "scott@unclesvf.com")

    if not folder:
        print("ERROR: Could not find 'scott' folder")
        return

    # Get subfolder references
    subfolders = {}
    for sf in folder.Folders:
        subfolders[sf.Name] = sf

    # Count items in main folder
    main_count = folder.Items.Count
    print(f"\nMain 'Scott' folder: {main_count} items")

    # Analyze and move items from main folder
    if main_count > 0:
        print("\n" + "-" * 80)
        print("EMAILS IN MAIN FOLDER (to be organized)")
        print("-" * 80)

        items = folder.Items
        items.Sort("[ReceivedTime]", True)

        emails_to_move = []
        for item in items:
            if item.Class != 43:  # Not a mail item
                continue

            subject = item.Subject or '(no subject)'
            try:
                body = item.Body[:2000] if item.Body else ''
            except:
                body = ''
            date_str = str(item.ReceivedTime)[:10]

            target_folder = categorize_email(subject, body)
            emails_to_move.append({
                'item': item,
                'subject': subject,
                'date': date_str,
                'target': target_folder
            })
            print(f"  [{date_str}] {subject[:50]} -> {target_folder}")

        # Move emails to subfolders
        print("\n" + "-" * 80)
        print("MOVING EMAILS TO SUBFOLDERS")
        print("-" * 80)

        moved_count = 0
        for email in emails_to_move:
            target = email['target']
            if target in subfolders:
                try:
                    email['item'].Move(subfolders[target])
                    print(f"  MOVED: {email['subject'][:40]} -> {target}")
                    moved_count += 1
                except Exception as e:
                    print(f"  ERROR moving {email['subject'][:30]}: {e}")
            else:
                print(f"  SKIP: Subfolder '{target}' not found")

        print(f"\nMoved {moved_count} emails")

    # Analyze subfolders
    print("\n" + "-" * 80)
    print("SUBFOLDER COUNTS")
    print("-" * 80)
    print(f"{'Subfolder':<35} {'Count':>8}")
    print("-" * 50)

    total = 0
    for sf in folder.Folders:
        count = sf.Items.Count
        total += count
        print(f"{sf.Name:<35} {count:>8}")

    print("-" * 50)
    print(f"{'TOTAL':<35} {total:>8}")

    # Get new X-Twitter posts
    print("\n" + "=" * 80)
    print("NEW X-TWITTER POSTS (since Jan 19, 2026)")
    print("=" * 80)

    if 'X-Twitter Posts' in subfolders:
        twitter_folder = subfolders['X-Twitter Posts']
        items = twitter_folder.Items
        items.Sort("[ReceivedTime]", True)

        new_posts = []
        cutoff_date = datetime(2026, 1, 19, 18, 30)  # After last analysis

        for item in items:
            if item.Class != 43:
                continue

            try:
                received = item.ReceivedTime
                # Handle pywintypes datetime
                if hasattr(received, 'year'):
                    item_date = datetime(received.year, received.month, received.day,
                                       received.hour, received.minute)
                else:
                    continue

                if item_date > cutoff_date:
                    subject = item.Subject or '(no subject)'
                    try:
                        body = item.Body or ''
                    except:
                        body = ''

                    # Extract URLs
                    urls = re.findall(r'https?://[^\s<>"\']+', body)
                    x_urls = [u for u in urls if 'x.com' in u or 'twitter.com' in u]

                    new_posts.append({
                        'date': item_date.strftime('%Y-%m-%d'),
                        'subject': subject,
                        'body': body,
                        'urls': urls,
                        'x_urls': x_urls
                    })

            except Exception as e:
                pass

        if new_posts:
            print(f"\nFound {len(new_posts)} new posts:\n")
            for post in new_posts:
                print(f"DATE: {post['date']}")
                print(f"SUBJECT: {post['subject']}")
                print(f"X URLS: {post['x_urls']}")
                print("-" * 40)
                print(post['body'][:1500])
                print("=" * 60)
                print()
        else:
            print("\nNo new posts since January 19, 2026")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    analyze_and_organize()
