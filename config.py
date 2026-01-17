"""
Configuration settings for eBay Automation
"""

# Outlook Settings
OUTLOOK_CONFIG = {
    # Email account to monitor (set to None for default account)
    'account_email': 'scott@unclesvf.com',

    # Folder name to monitor for eBay listing emails
    'folder_name': 'Linda',

    # Only process unread emails
    'unread_only': True,

    # Maximum emails to fetch at once
    'max_emails': 50,
}

# eBay Settings
EBAY_CONFIG = {
    # eBay username (optional - can do manual login)
    'username': None,

    # eBay password (optional - can do manual login)
    # WARNING: Storing passwords in plain text is not secure
    'password': None,
}

# Browser Settings
BROWSER_CONFIG = {
    # Run browser in headless mode (not recommended for eBay)
    'headless': False,

    # Chrome profile path to persist login sessions
    # Example: 'C:/Users/scott/AppData/Local/Google/Chrome/User Data'
    # Set to None to use fresh browser session
    'profile_path': None,

    # Wait timeout for elements (seconds)
    'timeout': 10,
}

# Processing Settings
PROCESS_CONFIG = {
    # Automatically mark emails as read after processing
    'mark_read_after_process': True,

    # Folder to move processed emails to (set to None to leave in place)
    'move_processed_to': None,

    # Pause between processing items (seconds)
    'pause_between_items': 2,
}
