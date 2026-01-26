# Claude Code Context - Scott's Workstation

This file provides context for Claude Code sessions.

---

## Skills Available

- **ambrose-server** - Start the Ambrose/Cortex server and frontend. Invoke with "start the server", "start Cortex", or "open the dashboard"
- **ebay-linda** - Process eBay listing emails from Linda's Outlook folder. Invoke with "run the eBay automation" or "process Linda's eBay emails"
- **scott-folder** - Organize emails in Outlook's Scott folder and extract X-Twitter AI insights. Invoke with "organize my Scott folder" or "process Scott emails"
- **fix-outlook-kb** - Fix Outlook Classic hanging after Windows Update. Invoke with "fix Outlook KB issue" or "Outlook is hanging after update"

---

## Active Project: AMBROSE AI Knowledge Base

**Location:** `C:\Users\scott\ebay-automation\` (scripts) + `D:\AI-Knowledge-Base\` (data)
**Status:** Production Ready - January 26, 2026
**Full Documentation:** `PROJECT_STATUS.md`

### What It Does

Full-stack AI knowledge extraction system:
- Extracts GitHub repos, HuggingFace models, YouTube tutorials from Outlook emails
- Uses local vLLM (Qwen2.5-7B-Instruct in WSL2) for knowledge extraction - no API costs
- Downloads transcripts, analyzes content, builds ChromaDB vector search
- Generates HTML reports, course materials, Midjourney style galleries
- React frontend (Cortex) for semantic search

### Port Configuration (IMPORTANT)

| Service | Port | Notes |
|---------|------|-------|
| vLLM | 8000 | Runs in WSL2, do NOT use for FastAPI |
| FastAPI Server | 8001 | Backend API |
| Frontend (Vite) | 5173 | React dev server |

### Quick Commands

```bash
# Run full pipeline (extracts knowledge, generates reports)
python run_pipeline.py

# Run pipeline without opening browser
python run_pipeline.py --no-open

# Show knowledge base status
python run_pipeline.py status

# Run single stage
python run_pipeline.py --stage llm

# List all stages
python run_pipeline.py --list-stages

# Start backend server (port 8001)
cd C:\Users\scott\ebay-automation
python -m uvicorn server:app --host 0.0.0.0 --port 8001

# Start frontend
cd C:\Users\scott\ebay-automation\frontend
npm run dev

# View static reports
start chrome "D:\AI-Knowledge-Base\exports\index.html"
```

### Pipeline Stages (11 total)

1. **extract** - Extract URLs from emails (runs FIRST to capture before organizing)
2. **organize** - Organize Outlook emails into subfolders
3. **youtube** - Fetch video metadata/transcripts
4. **analyze** - Extract tools, tips from transcripts
5. **search** - Build FTS5 search index
6. **llm** - vLLM/QWEN knowledge extraction (4 hour timeout)
7. **reports** - Generate HTML reports
8. **gallery** - Generate Midjourney sref gallery
9. **models** - Generate AI model tracking report
10. **courses** - Generate course materials
11. **sync** - Sync to D: drive

### Key Files

| File | Purpose |
|------|---------|
| `run_pipeline.py` | Master orchestration script |
| `server.py` | FastAPI backend (port 8001) |
| `extract_knowledge.py` | vLLM/Ollama knowledge extraction |
| `ai_content_extractor.py` | Email URL extraction |
| `scott_folder_organizer.py` | Email organization |
| `kb_config.py` | Centralized config, logging, utilities |
| `PROJECT_STATUS.md` | Full technical documentation |

### ChromaDB Location

```
C:\Users\scott\ebay-automation\data\knowledge_base\
```
Collection: `uncles_wisdom` (30 items)

Both server.py and orchestrator actions use this same path.

### Current Stats (Jan 25, 2026)

- 117 GitHub repos, 45 HuggingFace models, 46 YouTube tutorials
- 3,303 extracted items (824 tips, 413 workflows, 235 prompts, 1,068 insights, 763 fabrication apps)
- 3 Midjourney sref codes

---

## Other Completed Projects

### eBay Listing Automation Tool
**Location:** `C:\Users\scott\ebay-automation\`
**Status:** Enhanced - January 20, 2026

Reads emails from Outlook's "Linda" folder, separates items into:
- **TITLE REVISIONS** - Add 'Silver' after 'Sterling', new titles
- **PRICE REVISIONS** - "Raise to $X" / "Lower to $X"
- **END & RELIST** - "List new $X" (end listing, Sell Similar)

```bash
python end_and_relist.py          # Process emails
python end_and_relist.py --done   # Mark batch complete
python end_and_relist.py --stats  # Show statistics
```

### Budget Forecast Tool
**Location:** `C:\Users\scott\budget-forecast\`
**Status:** Completed - January 17, 2026

Analyzes Bank of America CSV for recurring charges, generates Excel forecast.

```bash
cd C:\Users\scott\budget-forecast
python budget_forecast.py
```

---

## Environment Notes

- **OS:** Windows 11
- **Python:** 3.13 (in PATH)
- **WSL2:** Ubuntu with vLLM installed
- **Office:** 32-bit (reinstalled Jan 16, 2026)
- **Outlook accounts:** scott@unclesvf.com (primary)
- **GPU:** 24GB VRAM (RTX 3090 or 4090)

---

## Fabrication Equipment (for cross-domain AI analysis)

The LLM extraction identifies connections between AI techniques and physical fabrication:

- **Fadal VMC4020**: CNC machining center for metals
- **ShopBot PRS Alpha**: 5'x8' CNC router, 5HP Colombo spindle
- **100W Mopa Fiber Laser**: Metal engraving, marking, annealing
- **55W CO2 Laser**: Wood, acrylic, leather cutting/engraving
- **3D Printers**: Prototyping, small parts

---

## Known Issues & Fixes

### vLLM Uses Port 8000
The FastAPI server MUST use port 8001 to avoid conflict with vLLM.

### Cortex ChromaDB Path
server.py must point to `data/knowledge_base` (same as orchestrator actions), NOT `D:\AI-Knowledge-Base\chromadb`.

### Email Content Loss (FIXED)
Pipeline extract stage runs BEFORE organize stage to capture URLs before emails are moved.

### Outlook COM Automation
Can hang after Windows Updates. Use `fix-outlook-kb` skill to diagnose and fix.

---

## User Preferences

- Batch size: 5 items at a time
- eBay workflow: End listing, then "Sell Similar" with new price (NOT revise)
- Track completed work in persistent files to survive crashes
- Auto-open reports in Chrome when pipeline completes
