# eBay Listing Automation Tool - Project Status

**Last Updated:** January 17, 2026
**Status:** COMPLETED & ENHANCED

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

### Completed: 52 items as of January 17, 2026 (plus 4 title/quantity corrections)

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
- Emails with typos like "List ne $39.50" or "List nw $55.00" may not parse
- "End listing" or "Decline offer" emails are skipped (no price to extract)
- Instruction emails (no eBay URL) are surfaced but require manual handling

---

## Dependencies (Installed)

- pywin32 (Outlook COM)
- selenium (Chrome automation - not currently used)
- webdriver-manager (ChromeDriver management)
