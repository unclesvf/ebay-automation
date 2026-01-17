# eBay Listing Automation Tool - Project Status

**Last Updated:** January 16, 2026
**Status:** COMPLETED

---

## Summary

Tool to automate eBay listing price updates based on emails from Linda in Outlook.

**Correct Workflow (End & Relist):**
1. Read unread emails from "Linda" folder in scott@unclesvf.com account
2. Parse eBay item ID and new price from each email
3. Open eBay "End Your Listing" page + item pages in Chrome
4. End each listing (reason: "error in listing")
5. Click "Sell Similar" on item page, set new price
6. Mark processed emails as read / track in completed log

---

## Completion Summary

### Completed: 41 items on January 16, 2026

All price update emails from the Linda folder have been processed using the end → sell similar workflow.

**Note:** Initial approach (revising prices) was incorrect. Correct workflow is to END the listing, then use "Sell Similar" to relist at the new price.

---

## Files in Project

| File | Purpose |
|------|---------|
| `end_and_relist.py` | **CURRENT SCRIPT** - End listing + Sell Similar workflow |
| `main.py` | Original interactive CLI (deprecated) |
| `outlook_reader.py` | Outlook COM automation module |
| `email_parser.py` | Parses eBay URLs and prices from email text |
| `ebay_browser.py` | Selenium Chrome automation (not used) |
| `config.py` | Configuration settings |
| `process_batch.py` | Old batch processor - revise workflow (deprecated) |
| `OutlookMacro.vba` | VBA macro for Outlook (backup approach) |
| `process_export.py` | Processes VBA export (backup approach) |
| `completed_items.txt` | Log of processed item IDs |
| `requirements.txt` | Python dependencies (installed) |

---

## How to Use (Future Batches)

When new emails arrive in the Linda folder:

```
cd C:\Users\scott\ebay-automation
python end_and_relist.py
```

**Options:**
- `python end_and_relist.py` - Process next 5 items
- `python end_and_relist.py --test` - Process only 2 items (for testing)

**Workflow:**
1. Script opens End Your Listing page (Tab 1) + item pages (Tabs 2+)
2. Copy item numbers to End Your Listing page, select "error in listing", end each
3. Go to each item tab, click "Sell Similar", enter the new price shown in terminal
4. Run script again to mark batch complete and get next batch
5. Repeat until "No more unread emails" message

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
- Looks for "List new $XX.XX" pattern in email body
- Extracts eBay item ID from URL (ebay.com/itm/XXXXXXXXX)
- Skips emails without valid price (e.g., "end listing" requests)

### Outlook COM
- Uses pywin32 for Outlook automation
- Can be unstable after Windows Updates
- VBA macro approach available as backup (see OutlookMacro.vba)

### Known Limitations
- Emails with typos like "List ne $39.50" or "List nw $55.00" may not parse
- "End listing" or "Decline offer" emails are skipped (no price to extract)

---

## Dependencies (Installed)

- pywin32 (Outlook COM)
- selenium (Chrome automation - not currently used)
- webdriver-manager (ChromeDriver management)
