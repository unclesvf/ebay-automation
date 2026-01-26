# AMBROSE AI Knowledge Base - Project Status

**Last Updated:** January 26, 2026
**Status:** Production Ready
**Git Branch:** feature/orchestrator-v1

---

## System Overview

The AMBROSE AI Knowledge Base is a comprehensive system for extracting, organizing, and searching AI-related knowledge from emails, YouTube tutorials, GitHub repos, and other sources. It features a FastAPI backend, React frontend (Cortex), and local LLM processing via vLLM.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AMBROSE System                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Frontend (React/Vite)              │  Backend (FastAPI)                    │
│  - Cortex: Semantic Search UI       │  - REST API (port 8001)               │
│  - Universal Insights Dashboard     │  - Pipeline Orchestration             │
│  - Reports Viewer                   │  - vLLM Integration                   │
│  - Interactive Transcript Search    │  - Outlook COM Automation             │
├─────────────────────────────────────────────────────────────────────────────┤
│  LLM Processing                                                              │
│  - vLLM (WSL2, port 8000): Qwen2.5-7B-Instruct                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  Data Storage                                                                │
│  - ChromaDB: Vector embeddings (30 items in uncles_wisdom)                  │
│  - SQLite FTS5: Transcript search (32 videos, 37,258 segments)              │
│  - JSON: master_db.json, extracted knowledge files                          │
│  - D:\AI-Knowledge-Base\: Reports, transcripts, exports                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Port Configuration

| Service | Port | Purpose |
|---------|------|---------|
| vLLM | 8000 | Local LLM inference (WSL2) - PRIMARY |
| FastAPI Server | 8001 | Backend API |
| Frontend (Vite) | 5173 | React development server |

### Key Configuration

All settings are centralized in `kb_config.py`:

| Setting | Value |
|---------|-------|
| LLM Backend | vLLM (runs in WSL2) |
| LLM Model | Qwen/Qwen2.5-7B-Instruct |
| vLLM URL | http://localhost:8000/v1 |
| Scripts | C:\Users\scott\ebay-automation\ |
| Data | D:\AI-Knowledge-Base\ |
| ChromaDB | C:\Users\scott\ebay-automation\data\knowledge_base\ |
| Logs | D:\AI-Knowledge-Base\logs\pipeline.log |

---

## Current Statistics (January 26, 2026)

### Content Inventory

| Source | Count |
|--------|-------|
| GitHub Repositories | 124 |
| HuggingFace Models | 45 |
| YouTube Tutorials | 51 |
| - With Transcripts | 36 |
| - LLM Processed | 36 |
| Midjourney sref Codes | 3 |

### Extracted Knowledge

| Category | Files |
|----------|-------|
| Knowledge files | 45 |
| Analysis files | 36 |
| Export reports | 19 |
| Course materials | 12 |

### Search Capabilities

| Type | Database | Contents |
|------|----------|----------|
| Cortex (semantic) | ChromaDB | 30 items (uncles_wisdom collection) |
| Transcript (FTS5) | SQLite | 36 videos, 37,258+ searchable segments |

---

## Skills (Claude Code)

Use these commands to invoke automated workflows:

| Skill | Trigger | Purpose |
|-------|---------|---------|
| ambrose-server | "start the server" | Start FastAPI + React frontend |
| ebay-linda | "process eBay emails" | Process Linda's eBay listing emails |
| scott-folder | "organize Scott folder" | Organize emails, extract insights |
| fix-outlook-kb | "fix Outlook KB issue" | Fix Outlook COM after Windows Update |

---

## Pipeline Stages

**Execution Order:** Extract runs BEFORE organize to capture URLs from new emails before they're moved to subfolders.

| # | ID | Script | Description | Timeout |
|---|-----|--------|-------------|---------|
| 1 | extract | ai_content_extractor.py | Extract URLs from main folder + subfolders | 10 min |
| 2 | organize | scott_folder_organizer.py | Move emails to categorized subfolders | 10 min |
| 3 | youtube | youtube_metadata.py | Fetch video metadata and transcripts | 10 min |
| 4 | analyze | transcript_analyzer.py | Extract tools, tips from transcripts | 10 min |
| 5 | search | transcript_search.py | Build FTS5 full-text search index | 10 min |
| 6 | llm | extract_knowledge.py | vLLM/QWEN knowledge extraction | 4 hours |
| 7 | reports | generate_reports.py | Generate HTML reports | 10 min |
| 8 | gallery | style_code_gallery.py | Generate Midjourney sref gallery | 10 min |
| 9 | models | model_tracker.py | Generate AI model tracking report | 10 min |
| 10 | courses | course_materials.py | Generate course materials | 10 min |
| 11 | sync | sync_to_d_drive.py | Sync scripts and data to D: drive | 10 min |

### Running the Pipeline

```bash
# Full pipeline (opens reports when done)
python run_pipeline.py

# Options
python run_pipeline.py --no-open       # Don't open browser
python run_pipeline.py --dry-run       # Preview only
python run_pipeline.py --skip-llm      # Skip LLM stage (faster)
python run_pipeline.py status          # Show KB status
python run_pipeline.py --stage llm     # Run single stage
python run_pipeline.py --stages youtube,analyze  # Multiple stages
python run_pipeline.py --from youtube  # Run from stage onwards
python run_pipeline.py --list-stages   # List all stages
```

---

## Key Files Reference

### Core Scripts (C:\Users\scott\ebay-automation\)

| File | Purpose | Key Functions |
|------|---------|---------------|
| `run_pipeline.py` | Master orchestrator | Runs all 11 stages in order |
| `server.py` | FastAPI backend | /knowledge, /search, /reports, /run endpoints |
| `extract_knowledge.py` | LLM extraction | Processes transcripts with vLLM/Ollama |
| `ai_content_extractor.py` | Email extraction | Extracts GitHub, HF, YouTube URLs from emails |
| `scott_folder_organizer.py` | Email organization | Moves emails to 30+ categorized subfolders |
| `generate_reports.py` | HTML reports | Creates index.html and category reports |
| `kb_config.py` | Configuration | Centralized config, logging, RateLimiter, ProgressTracker, backup utilities |
| `youtube_metadata.py` | YouTube processing | Fetches metadata and transcripts |
| `transcript_analyzer.py` | Transcript analysis | Extracts tools, techniques, tips |
| `transcript_search.py` | Search index | Builds FTS5 full-text search |
| `style_code_gallery.py` | Sref gallery | Generates Midjourney style reference gallery |

### Frontend (C:\Users\scott\ebay-automation\frontend\)

| File | Purpose |
|------|---------|
| `src/App.jsx` | Main React app with routing |
| `src/api.js` | API client (proxies to port 8001) |
| `src/components/Cortex.jsx` | Semantic search UI (ChromaDB) |
| `src/components/Dashboard.jsx` | Main dashboard |
| `src/components/UniversalInsights.jsx` | Insights browser |
| `src/components/Reports.jsx` | Reports viewer |
| `vite.config.js` | Vite config (proxy to 8001) |

### Data Files (D:\AI-Knowledge-Base\)

| Path | Contents |
|------|----------|
| `master_db.json` | Main database (repos, tutorials, styles) |
| `extracted/` | all_tips.json, all_workflows.json, etc. |
| `exports/` | HTML reports (index.html is entry point) |
| `tutorials/transcripts/` | YouTube transcript cache |
| `tutorials/search_index.db` | FTS5 search database |
| `backups/` | Timestamped backups |

### ChromaDB Location

```
C:\Users\scott\ebay-automation\data\knowledge_base\
  └── chroma.sqlite3
  └── [collection folders]
```

Collection: `uncles_wisdom` - Used by both orchestrator actions and server.py

---

## API Endpoints

### System
- `GET /` - System status
- `GET /health` - Health check (ChromaDB, search index, vLLM, reports)
- `GET /status` - Detailed status with vLLM check
- `GET /logs` - Orchestrator log tail

### Knowledge Base (Cortex) - Semantic Search
- `GET /knowledge?query=X&limit=N` - Semantic search via ChromaDB
- `GET /knowledge` (no query) - List all items in collection

### Transcript Search - Full-Text Search
- `GET /search?q=X&channel=Y&topic=Z` - FTS5 transcript search
- `GET /search/stats` - Search index statistics (videos, segments, channels)

### Reports
- `GET /reports/list` - List available HTML reports
- Static files served at `/reports-static/`

### Pipeline
- `POST /run?profile=X` - Run orchestrator
- `GET /config` - Get current config
- `POST /config/dry_run` - Set dry run mode

### Insights
- `GET /insights?limit=N&sort_by=X` - Universal insights

---

## Recent Bug Fixes (January 2026)

| Issue | File | Fix |
|-------|------|-----|
| Email content loss | run_pipeline.py | Extract runs BEFORE organize |
| Cortex ChromaDB mismatch | server.py | Changed to use data\knowledge_base path |
| vLLM hangs | extract_knowledge.py | Added 5-min timeout per request |
| LLM stage timeout | run_pipeline.py | Increased to 4 hours |
| Race condition | server.py | Added threading.Lock() |
| Silent email errors | ai_content_extractor.py | Proper error logging |
| Empty knowledge peek | server.py | Fixed items array building |
| JSON corruption | ai_content_extractor.py | Added try/except handling |
| Missing subfolders | scott_folder_organizer.py | Auto-create on demand |
| Port conflict (Jan 26) | server.py | Fixed port 8000→8001 (vLLM uses 8000) |
| Missing import (Jan 26) | server.py | Added missing `import requests` |
| Missing logger (Jan 26) | ai_content_extractor.py | Added logger setup |
| API port mismatch (Jan 26) | generate_reports.py | Fixed search.html to use port 8001 |
| Tool data format (Jan 26) | generate_reports.py | Fixed tool_mentions JSON loading |
| Bare except clauses (Jan 26) | outlook_reader.py, scott_folder_organizer.py | Specified exception types |

---

## New Features (January 26, 2026)

### Centralized Configuration (`kb_config.py`)

All ports, paths, and settings now centralized:

```python
from kb_config import (
    API_PORT, VLLM_PORT, OLLAMA_MODEL,
    get_logger, backup_database, RateLimiter, ProgressTracker
)
```

### Health Check Endpoint

Monitor system component health:

```bash
curl http://localhost:8001/health
```

Returns status of ChromaDB, search index, Ollama, and reports.

### Rate Limiting

Prevent API throttling with built-in rate limiter:

```python
from kb_config import RateLimiter
limiter = RateLimiter(delay=1.5, burst=3)
for item in items:
    limiter.wait()
    api_call(item)
```

### Progress Tracking

ETA and progress for long operations:

```python
from kb_config import ProgressTracker
tracker = ProgressTracker(total=100, description="Processing")
for item in items:
    process(item)
    tracker.update()
tracker.finish()
```

### Automatic Database Backup

Backup before major operations:

```python
from kb_config import backup_database
backup_database(reason="before_llm")  # Creates timestamped backup
```

### Incremental Processing

Transcript analyzer only processes new items by default:

```bash
python transcript_analyzer.py all          # Only new transcripts
python transcript_analyzer.py all --force  # Reanalyze all
```

---

## Starting the System

### Quick Start (use skill)
Say: "start the server" or "start Cortex"

### Manual Start

```bash
# 1. Start vLLM (in WSL2)
vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000

# 2. Start FastAPI backend
cd C:\Users\scott\ebay-automation
python -m uvicorn server:app --host 0.0.0.0 --port 8001

# 3. Start React frontend
cd C:\Users\scott\ebay-automation\frontend
npm run dev

# 4. Open browser
start chrome "http://localhost:5173"
```

### View Static Reports
```bash
start chrome "D:\AI-Knowledge-Base\exports\index.html"
```

---

## Troubleshooting

### vLLM Not Responding
```bash
# Check vLLM status
curl http://localhost:8000/v1/models

# If not running, start in WSL2:
wsl -d Ubuntu
vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000

# If WSL2 needs restart:
wsl --shutdown
# Then relaunch Ubuntu and start vLLM
```

### Port 8001 Already in Use
```bash
netstat -ano | findstr :8001
taskkill /PID <pid> /F
```

### Cortex Returns No Results
1. Check ChromaDB has items: `python -c "import chromadb; c=chromadb.PersistentClient(path='data/knowledge_base'); print(c.get_collection('uncles_wisdom').count())"`
2. Verify server.py DB_PATH points to `data/knowledge_base`
3. Restart server after path changes

### Outlook COM Errors
- Often caused by Windows Updates
- Use `fix-outlook-kb` skill to diagnose
- May need to uninstall specific KB updates

---

## Fabrication Context

The LLM extraction includes cross-domain fabrication analysis for Scott's shop capabilities:

- **Fadal VMC4020**: CNC machining center
- **ShopBot PRS Alpha**: 5'x8' CNC router
- **100W Mopa Fiber Laser**: Metal engraving
- **55W CO2 Laser**: Wood/acrylic cutting
- **3D Printers**: Prototyping

The system identifies potential connections between AI techniques and physical fabrication workflows.

---

## Future Enhancements

1. **ChromaDB Expansion** - Ingest more content into vector store
2. **Real-time Pipeline** - Watch folder for new emails
3. **Search Filters** - Faceted search by category, date, source
4. **Export Options** - CSV/PDF export of knowledge
5. **Scheduling** - Automated daily pipeline runs
6. **Better Transcripts** - Handle YouTube API blocks gracefully

---

## Git Repository

- **Remote:** https://github.com/unclesvf/ebay-automation.git
- **Branch:** feature/orchestrator-v1
- **Main scripts committed and pushed**

---

## Contact

**Developer:** Scott
**Scripts:** C:\Users\scott\ebay-automation\
**Data:** D:\AI-Knowledge-Base\
**Skills:** C:\Users\scott\.claude\skills\
