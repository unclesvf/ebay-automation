# eBay Listing Automation Tool - Project Status

**Last Updated:** January 20, 2026
**Status:** COMPLETED & ENHANCED

---

## January 20, 2026 (Session 3) - Critical Classification Bug Fix

### Critical Bug Fix
1. **"List new and raise to $X" was misclassified as PRICE REVISION** - The `_is_price_revision()` method checked for "raise to" BEFORE "list new", causing emails like "List new and raise to $69.50" to be incorrectly treated as price revisions (just change price) instead of END & RELIST.

   **Root cause:** Pattern matching order was wrong:
   ```python
   # OLD (buggy): checked "raise to" first
   if re.search(r'\braise\s+to\s+\$?[\d,]+', text_lower):
       return True  # WRONG - matched before checking "list new"
   ```

   **Fix:** Check for "list new" FIRST:
   ```python
   # NEW (fixed): check "list new" first
   if re.search(r'\blist\s+new\b', text_lower):
       return False  # Correct - END & RELIST, not price revision
   ```

   **Impact:** 25+ items were processed incorrectly (price revised instead of ended/relisted). User had to manually end and relist all affected items.

### New Feature
2. **Follow-up email auto-detection** - When Linda sends a follow-up email for an already-completed item with new instructions:
   - Script detects the newer unread email
   - Prints a warning: "*** FOLLOW-UP EMAILS DETECTED ***"
   - Automatically removes item from completed list
   - Includes item in current batch with the NEW instructions

### Classification Rules (Clarified)
| Email Text | Classification |
|------------|----------------|
| "List new and raise to $X" | END & RELIST |
| "List new $X" | END & RELIST |
| "Raise to $X" (no "list new") | PRICE REVISION |
| "Lower to $X" (no "list new") | PRICE REVISION |

### Files Modified
- `email_parser.py` - Fixed `_is_price_revision()` to check "list new" before "raise to"
- `end_and_relist.py` - Added follow-up email detection in `get_next_batch()`

### Statistics
- **Session:** 55 items processed + 25 items re-done due to bug
- **Today total:** 55 items

---

## January 20, 2026 (Session 2) - Title-Only Tracking & Gallery Photo Features

### Bug Fix
1. **Title-only items now tracked by `--done` flag** - Previously, title-only items (Add Silver, NEW TITLE, etc.) were NOT tracked and required manual marking as read in Outlook. Now:
   - Title-only items are saved to `title_pending_entries.txt`
   - Running `--done` marks both price items AND title-only items as complete
   - Both types are marked as read in Outlook and logged to `completed_items.txt`

### New Features
1. **Pending Items Verification Table** - When running without `--done`, shows a full table of pending items:
   - Displays Item ID, Price/Type for each pending item
   - Shows eBay links for easy verification
   - Helps user confirm items are actually completed before marking done

2. **Gallery Photo Info Pages** - When Linda's email mentions "gallery photo":
   - Creates an HTML info page with the email body and instructions
   - Opens the info page in Chrome BEFORE the item's eBay page
   - Makes it easy to see what photo change is needed

3. **Fixed ebay-linda Skill** - Simplified skill.md to avoid bash parsing errors with inline backticks

### Files Modified
- `end_and_relist.py` - Added `TITLE_PENDING_FILE`, `GALLERY_INFO_DIR`, pending verification table, gallery photo info pages
- `.claude/skills/ebay-linda/skill.md` - Simplified to avoid parsing errors
- `.claude/skills/ebay-linda/REFERENCE.md` - Updated file tracking documentation

---

## January 20, 2026 (Session 1) - Major Fixes & UI Improvements

### Critical Bug Fix
1. **REVISE vs END & RELIST separation** - Previously ALL price items were treated as END & RELIST. Now correctly separates:
   - **"Raise to $X"** or **"Lower to $X"** = **REVISE** (just change the price, do NOT end listing)
   - **"List new $X"** = **END & RELIST** (end listing, then Sell Similar with new price)
   - Added `is_price_revision` field to `EbayListingInfo` dataclass
   - Added `_is_price_revision()` method to detect Raise/Lower patterns

### UI Improvements
1. **Compact table format** - Each item now shows on 2-3 lines:
   ```
   [1] 277385925984 | NEW PRICE: $150.00 | REVISE
       TITLE:  Silver Souvenir Spoon AUDITORIUM Long Beach
       ACTION: Raise to $150.00
   ```
2. **Separate sections** - PRICE REVISIONS and END & RELIST shown in separate sections with different Chrome windows
3. **All fields visible** - Tab #, Item ID, Title, New Price, Type (REVISE/LIST NEW), Action

### New Features
1. **Buyer blocking** - When "block" is detected in notes:
   - Opens eBay Buyer Block page (https://www.ebay.com/bmgt/BuyerBlock)
   - Extracts and displays buyer username from email
   - Added `buyer_username` field and `_extract_buyer_username()` method

### Files Modified
- `email_parser.py` - Added `is_price_revision`, `buyer_username` fields and detection methods
- `end_and_relist.py` - Complete UI rewrite, separated REVISE from END & RELIST sections

### Statistics (at time of session)
- **Session:** 4 items processed
- **Running total:** 184 items

---

## January 18, 2026 - Bug Fixes

### Bug Fixes
1. **"List new" without price now handled correctly** - Emails that say "List new" followed by a URL (but no price) were incorrectly categorized as "title-only/REVISE" items. They are now correctly treated as End/Relist items with "(Current Price)" displayed.

2. **Title-only items no longer auto-marked as done** - Previously, running `--done` would mark ALL pending items complete, including "title-only" items that may not have displayed properly. Now:
   - Only End/Relist items are tracked in the pending file
   - Title-only items are shown separately with a note to mark them read manually in Outlook
   - Running `--done` only marks the End/Relist items as complete

### Files Modified
- `email_parser.py` - Added `relist_current_price` flag and `_is_list_new_no_price()` method
- `end_and_relist.py` - Updated pending file logic and display handling

---

## Summary

Tool to automate eBay listing price updates based on emails from Linda in Outlook.

**Correct Workflow (End & Relist):**
1. Read unread emails from "Linda" folder in scott@unclesvf.com account
2. Parse eBay item ID, price, quantity, and special instructions from each email
3. Open eBay "End Your Listing" page + item pages in Chrome
4. End each listing (reason: "error in listing")
5. Click "Sell Similar" on item page, set new price (and quantity if specified)
6. Run with `--done` flag to mark batch complete and get next batch

---

## Completion Summary

### Completed: 235 items as of January 20, 2026

All price update emails from the Linda folder have been processed using the end → sell similar workflow.

**Note:** Initial approach (revising prices) was incorrect. Correct workflow is to END the listing, then use "Sell Similar" to relist at the new price.

---

## January 17, 2026 - Additional Enhancements (Batch 2)

### New Features
1. **Typo tolerance** - Parser now handles common typos:
   - "List ne $39.50" (missing 'w')
   - "List nw $55.00" (transposed letters)
   - "Raise to $XX", "Lower to $XX", "Change to $XX" patterns

2. **Email preview mode** - When items need review, shows the first 8 lines of the email body so you can see the original context without opening Outlook

3. **Undo/recovery mode** (`--undo` flag) - Remove items from completed list for reprocessing:
   ```
   python end_and_relist.py --undo 276715685145 276715685146
   ```

4. **Statistics tracking** (`--stats` flag) - Track processing counts:
   - Today's count
   - This week's count
   - All-time total
   - Daily breakdown for last 7 days

5. **Custom batch size** (`--batch N` flag) - Adjust batch size as needed:
   ```
   python end_and_relist.py --batch 10  # Process 10 items at a time
   ```

6. **Title-only listing support** - Emails with eBay URL but no price are now shown as a separate category:
   - Displayed with `***` markers as "TITLE/HEADER CHANGES ONLY"
   - Uses REVISE workflow (not End/Relist) since price doesn't change
   - Opens item pages directly for quick editing

7. **Full new title extraction** - When Linda shows the complete new title after "Add to header" or similar:
   - Extracts and displays the full title with placement already shown
   - Example: `*** NEW TITLE: Lot 3 Copper 1/2" Fittings Threaded Male Adapters New`
   - Makes it easy to copy/paste the exact title Linda wants

---

## January 17, 2026 - Major Bug Fixes & Enhancements (Batch 1)

### Bug Fixes
1. **Price parsing from body only** - Fixed bug where "$1" from item titles like "$1 Rare Brass Koala Bear" was incorrectly parsed as the price. Now extracts prices only from email body.

2. **Explicit completion with --done flag** - Script no longer auto-marks batches complete. Must run with `--done` flag after processing. Prevents items from being accidentally skipped.

3. **Skip reply emails** - Emails starting with "Re:" are now filtered out (these are conversations, not listings).

4. **Surface instruction emails** - Emails from Linda without eBay URLs (general instructions like "change all coin cards to $7.95") are now displayed prominently.

### New Features
1. **Quantity parsing** - Detects "quantity 2", "qty 2", "list 2 at $9.99" patterns
2. **Special instructions/notes** - Captures "change header", "change title", "change description", "gallery photo", etc.
3. **mark_as_unread() method** - Added to OutlookReader for recovery scenarios
4. **Colored text extraction from HTML** - Parses Linda's colored text:
   - **Blue text** = New header/title to USE (e.g., `>>> USE (blue): New Title Here`)
   - **Red text** = Text to REMOVE (e.g., `>>> REMOVE (red): Old Text`)
5. **"Needs Review" flag** - Alerts when parser detects inconsistencies:
   - "change header" mentioned but no blue text found
   - "change description" mentioned but no colored text found
   - Gallery photo changes requested
   - Displays as: `!!! REVIEW NEEDED: reason`
6. **Smart instruction handling** (`--instructions` flag) - Parses bulk instruction emails:
   - Extracts search terms from "change all X to $Y" style emails
   - Extracts target price and expected item count
   - Opens Seller Hub with pre-filled searches for easy bulk editing

---

## Files in Project

| File | Purpose |
|------|---------|
| `end_and_relist.py` | **CURRENT SCRIPT** - End listing + Sell Similar workflow |
| `instruction_parser.py` | Parses bulk instruction emails (change all X to $Y) |
| `main.py` | Original interactive CLI (deprecated) |
| `outlook_reader.py` | Outlook COM automation module |
| `email_parser.py` | Parses eBay URLs and prices from email text |
| `ebay_browser.py` | Selenium Chrome automation (not used) |
| `config.py` | Configuration settings |
| `process_batch.py` | Old batch processor - revise workflow (deprecated) |
| `OutlookMacro.vba` | VBA macro for Outlook (backup approach) |
| `process_export.py` | Processes VBA export (backup approach) |
| `completed_items.txt` | Log of processed item IDs |
| `stats.txt` | Processing statistics by date |
| `requirements.txt` | Python dependencies (installed) |

---

## How to Use (Future Batches)

When new emails arrive in the Linda folder:

```
cd C:\Users\scott\ebay-automation
python end_and_relist.py
```

**Commands:**
- `python end_and_relist.py` - Show current batch (safe to run anytime, does NOT mark anything complete)
- `python end_and_relist.py --done` - Mark previous batch complete, then show next batch
- `python end_and_relist.py --instructions` - Process bulk instruction emails (e.g., "change all X to $Y")
- `python end_and_relist.py --test` - Process only 2 items (for testing)
- `python end_and_relist.py --batch N` - Set custom batch size (e.g., `--batch 10` for 10 items)
- `python end_and_relist.py --stats` - Show processing statistics (today, week, all-time)
- `python end_and_relist.py --undo ID1 ID2` - Remove items from completed list (for reprocessing)

**Workflow:**
1. Run script (no flags) - opens End Your Listing page (Tab 1) + item pages (Tabs 2+)
2. Review terminal output for:
   - Item numbers and prices
   - **QUANTITY** (if not 1)
   - **NOTES** (change header, etc.)
   - **INSTRUCTION EMAILS** (general instructions from Linda)
3. Copy item numbers to End Your Listing page, select "error in listing", end each
4. Go to each item tab, click "Sell Similar", enter the new price (and quantity if specified)
5. Run `python end_and_relist.py --done` to mark batch complete and get next batch
6. Repeat until "No more unread emails" message

---

## Configuration

- **Outlook Account:** scott@unclesvf.com
- **Folder:** Linda
- **Filter:** Unread emails only
- **Batch size:** 5 items (2 in test mode)
- **End Listing URL:** https://www.ebay.com/help/action?topicid=4146

---

## Technical Notes

### Email Parser
- **Prices:** Extracts from email BODY only (not subject) to avoid false matches in item titles
- **Patterns:** "List new $XX.XX", "New price: $XX.XX", "Price: $XX.XX", or bare "$XX.XX"
- **Quantity:** Detects "quantity N", "qty N", "list N at $XX.XX"
- **Notes:** Captures lines containing: change header, change title, change description, gallery photo, raise to, lower to
- **Item ID:** Extracts from eBay URL (ebay.com/itm/XXXXXXXXX)
- **Filtering:** Skips "Re:" reply emails, surfaces instruction emails without eBay URLs

### Outlook COM
- Uses pywin32 for Outlook automation
- Methods: mark_as_read(), mark_as_unread(), move_email()
- Can be unstable after Windows Updates
- VBA macro approach available as backup (see OutlookMacro.vba)

### Known Limitations
- "End listing" or "Decline offer" emails are skipped (no price to extract)
- Instruction emails (no eBay URL) are surfaced but require manual handling

---

## Dependencies (Installed)

- pywin32 (Outlook COM)
- selenium (Chrome automation - not currently used)
- webdriver-manager (ChromeDriver management)
