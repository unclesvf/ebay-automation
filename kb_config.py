"""
Shared Configuration for AI Knowledge Base Scripts

Centralizes paths, settings, logging, and utilities used across all knowledge base scripts.
"""
from pathlib import Path
import logging
import sys
import time
import shutil
from datetime import datetime
from functools import wraps

# =============================================================================
# BASE PATHS
# =============================================================================
KNOWLEDGE_BASE = Path(r"D:\AI-Knowledge-Base")
SOURCE_DIR = Path(r"C:\Users\scott\ebay-automation")
CHROMADB_PATH = SOURCE_DIR / "data" / "knowledge_base"

# =============================================================================
# DATABASE PATHS
# =============================================================================
MASTER_DB = KNOWLEDGE_BASE / "master_db.json"
URL_CACHE = KNOWLEDGE_BASE / "url_cache.json"
METADATA_CACHE = KNOWLEDGE_BASE / "youtube_metadata_cache.json"
TOKEN_USAGE = KNOWLEDGE_BASE / "token_usage.json"

# =============================================================================
# DIRECTORY PATHS
# =============================================================================
TRANSCRIPTS_DIR = KNOWLEDGE_BASE / "tutorials" / "transcripts"
ANALYSIS_DIR = KNOWLEDGE_BASE / "tutorials" / "analysis"
SEARCH_INDEX = KNOWLEDGE_BASE / "tutorials" / "search_index.db"
EXTRACTED_DIR = KNOWLEDGE_BASE / "extracted"
EXPORTS_DIR = KNOWLEDGE_BASE / "exports"
STYLES_DIR = KNOWLEDGE_BASE / "styles" / "midjourney-sref"
COURSE_DIR = KNOWLEDGE_BASE / "course_materials"
BACKUPS_DIR = KNOWLEDGE_BASE / "backups"
SCRIPTS_DIR = KNOWLEDGE_BASE / "scripts"

# =============================================================================
# SERVER/API SETTINGS
# =============================================================================
# IMPORTANT: vLLM uses port 8000, so FastAPI must use 8001
VLLM_PORT = 8000
VLLM_HOST = "localhost"
VLLM_URL = f"http://{VLLM_HOST}:{VLLM_PORT}"

API_PORT = 8001
API_HOST = "0.0.0.0"

FRONTEND_PORT = 5173

# =============================================================================
# LLM MODEL SETTINGS
# =============================================================================
# vLLM is the primary (and only) LLM backend for this project
# Runs in WSL2 on port 8000
VLLM_MODEL = "Qwen/Qwen2.5-7B-Instruct"

# LLM extraction settings
LLM_TIMEOUT = 120  # seconds per request
LLM_MAX_RETRIES = 3
LLM_STAGE_TIMEOUT = 4 * 60 * 60  # 4 hours for full LLM stage

# Note: Ollama is NOT used in this project (vLLM is faster)
# Ollama remains installed on system for other projects

# =============================================================================
# OUTLOOK SETTINGS
# =============================================================================
OUTLOOK_ACCOUNT = "scott@unclesvf.com"
SCOTT_FOLDER = "scott"

# =============================================================================
# EMAIL FOLDER CATEGORIES
# =============================================================================
AI_CONTENT_FOLDERS = [
    'AI Agents', 'AI Art-Images', 'AI Music-Audio',
    'General AI', 'Claude-Anthropic', 'ChatGPT-OpenAI', 'Google-Gemini',
    'HiggsField', 'Grok-xAI'
]
RELATED_CONTENT_FOLDERS = [
    'GitHub Projects', 'Software-Apps', 'YouTube Videos',
    'Coding-Development', 'X-Twitter Posts',
    'Engraving-Laser', 'Adobe-Editing'
]
DEFAULT_EXTRACT_FOLDERS = AI_CONTENT_FOLDERS + RELATED_CONTENT_FOLDERS

# =============================================================================
# PROCESSING SETTINGS
# =============================================================================
DEFAULT_BATCH_SIZE = 5

# Rate limiting for external APIs
RATE_LIMIT_DELAY = 1.0  # seconds between API calls
RATE_LIMIT_BURST = 5    # requests before enforcing delay

# Retry settings
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0  # seconds
RETRY_MAX_DELAY = 30.0  # seconds
RETRY_BACKOFF_FACTOR = 2.0

# =============================================================================
# LOGGING SETUP
# =============================================================================
LOG_FORMAT = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = KNOWLEDGE_BASE / "logs" / "pipeline.log"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger for a module.

    Args:
        name: Logger name (usually __name__ or script name)
        level: Logging level (default INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    logger.addHandler(console_handler)

    # File handler (create log directory if needed)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(file_handler)
    except Exception:
        pass  # Skip file logging if it fails

    return logger


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def backup_database(source_path: Path = None, reason: str = "auto") -> Path:
    """
    Create a timestamped backup of a database file.

    Args:
        source_path: Path to file to backup (default: MASTER_DB)
        reason: Reason for backup (included in filename)

    Returns:
        Path to backup file
    """
    if source_path is None:
        source_path = MASTER_DB

    if not source_path.exists():
        return None

    # Ensure backup directory exists
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    # Create timestamped backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{source_path.stem}_{reason}_{timestamp}{source_path.suffix}"
    backup_path = BACKUPS_DIR / backup_name

    # Copy file
    shutil.copy2(source_path, backup_path)

    # Clean old backups (keep last 10)
    cleanup_old_backups(source_path.stem, keep=10)

    return backup_path


def cleanup_old_backups(prefix: str, keep: int = 10):
    """Remove old backup files, keeping the most recent ones."""
    if not BACKUPS_DIR.exists():
        return

    # Find all backups matching prefix
    backups = sorted(
        BACKUPS_DIR.glob(f"{prefix}_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    # Remove old ones
    for old_backup in backups[keep:]:
        try:
            old_backup.unlink()
        except Exception:
            pass


def retry_with_backoff(max_attempts: int = None, base_delay: float = None,
                       max_delay: float = None, backoff_factor: float = None,
                       exceptions: tuple = (Exception,)):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts (default from config)
        base_delay: Initial delay in seconds (default from config)
        max_delay: Maximum delay in seconds (default from config)
        backoff_factor: Multiplier for each retry (default from config)
        exceptions: Tuple of exceptions to catch

    Usage:
        @retry_with_backoff(max_attempts=3, exceptions=(ConnectionError,))
        def fetch_data():
            ...
    """
    max_attempts = max_attempts or RETRY_MAX_ATTEMPTS
    base_delay = base_delay or RETRY_BASE_DELAY
    max_delay = max_delay or RETRY_MAX_DELAY
    backoff_factor = backoff_factor or RETRY_BACKOFF_FACTOR

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(min(delay, max_delay))
                        delay *= backoff_factor

            raise last_exception

        return wrapper
    return decorator


class RateLimiter:
    """
    Simple rate limiter for API calls.

    Usage:
        limiter = RateLimiter(delay=1.0, burst=5)
        for item in items:
            limiter.wait()
            api_call(item)
    """

    def __init__(self, delay: float = None, burst: int = None):
        self.delay = delay or RATE_LIMIT_DELAY
        self.burst = burst or RATE_LIMIT_BURST
        self.call_count = 0
        self.last_call_time = 0

    def wait(self):
        """Wait if necessary before making next call."""
        self.call_count += 1

        if self.call_count > self.burst:
            elapsed = time.time() - self.last_call_time
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)

        self.last_call_time = time.time()

    def reset(self):
        """Reset the rate limiter."""
        self.call_count = 0
        self.last_call_time = 0


class ProgressTracker:
    """
    Track progress of long-running operations.

    Usage:
        tracker = ProgressTracker(total=100, description="Processing items")
        for item in items:
            process(item)
            tracker.update()
        tracker.finish()
    """

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = time.time()
        self.logger = get_logger("Progress")

    def update(self, count: int = 1, message: str = None):
        """Update progress by count."""
        self.current += count

        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0
        remaining = (self.total - self.current) / rate if rate > 0 else 0

        pct = (self.current / self.total) * 100 if self.total > 0 else 0

        status = f"{self.description}: {self.current}/{self.total} ({pct:.1f}%)"
        if remaining > 0:
            mins, secs = divmod(int(remaining), 60)
            hours, mins = divmod(mins, 60)
            if hours > 0:
                status += f" - ETA: {hours}h {mins}m"
            elif mins > 0:
                status += f" - ETA: {mins}m {secs}s"
            else:
                status += f" - ETA: {secs}s"

        if message:
            status += f" - {message}"

        self.logger.info(status)

    def finish(self):
        """Mark progress as complete."""
        elapsed = time.time() - self.start_time
        mins, secs = divmod(int(elapsed), 60)
        hours, mins = divmod(mins, 60)

        if hours > 0:
            time_str = f"{hours}h {mins}m {secs}s"
        elif mins > 0:
            time_str = f"{mins}m {secs}s"
        else:
            time_str = f"{secs}s"

        self.logger.info(f"{self.description}: Complete! {self.current} items in {time_str}")


# =============================================================================
# VLLM MANAGEMENT (WSL2)
# =============================================================================
# vLLM runs in WSL2 (Ubuntu-24.04) and persists in GPU memory
# These utilities allow starting/stopping vLLM to free GPU resources

WSL_DISTRO = "Ubuntu-24.04"

def is_vllm_running():
    """Check if vLLM is currently running in WSL2."""
    import subprocess
    try:
        result = subprocess.run(
            ['wsl', '-d', WSL_DISTRO, '-e', 'bash', '-c', 'pgrep -f "vllm serve"'],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False

def stop_vllm():
    """Stop vLLM server in WSL2 to free GPU memory."""
    import subprocess
    import os
    logger = get_logger("vLLM")

    if not is_vllm_running():
        logger.info("vLLM is not running")
        return True

    try:
        logger.info("Stopping vLLM server...")

        # Kill tmux session first (if using tmux approach)
        subprocess.run(
            ['wsl', '-d', WSL_DISTRO, '--', 'bash', '-c', 'tmux kill-session -t vllm 2>/dev/null'],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, 'MSYS_NO_PATHCONV': '1'}
        )

        # Then kill any remaining vLLM processes
        subprocess.run(
            ['wsl', '-d', WSL_DISTRO, '--', 'bash', '-c', 'pkill -f "vllm serve"'],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, 'MSYS_NO_PATHCONV': '1'}
        )
        time.sleep(2)

        # If still running, force kill
        if is_vllm_running():
            logger.info("Forcing vLLM shutdown...")
            subprocess.run(
                ['wsl', '-d', WSL_DISTRO, '--', 'bash', '-c', 'pkill -9 -f "vllm serve"'],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, 'MSYS_NO_PATHCONV': '1'}
            )
            time.sleep(2)

        if not is_vllm_running():
            logger.info("vLLM stopped successfully - GPU memory freed")
            return True
        else:
            logger.warning("vLLM may still be running")
            return False

    except Exception as e:
        logger.error(f"Error stopping vLLM: {e}")
        return False

def start_vllm():
    """Start vLLM server in WSL2 using tmux for persistence."""
    import subprocess
    import os
    logger = get_logger("vLLM")

    if is_vllm_running():
        logger.info("vLLM is already running")
        return True

    try:
        logger.info(f"Starting vLLM with {VLLM_MODEL}...")

        # Kill any existing tmux session
        subprocess.run(
            ['wsl', '-d', WSL_DISTRO, '--', 'bash', '-c', 'tmux kill-session -t vllm 2>/dev/null'],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, 'MSYS_NO_PATHCONV': '1'}
        )

        # Start vLLM in tmux session for persistence
        # Use full path to vllm since PATH may not be set correctly
        vllm_cmd = f'/home/scott/.local/bin/vllm serve {VLLM_MODEL} --port {VLLM_PORT} --host 0.0.0.0 2>&1 | tee /tmp/vllm.log'
        cmd = f"tmux new-session -d -s vllm '{vllm_cmd}'"
        subprocess.run(
            ['wsl', '-d', WSL_DISTRO, '--', 'bash', '-c', cmd],
            capture_output=True, text=True, timeout=10,
            env={**os.environ, 'MSYS_NO_PATHCONV': '1'}
        )

        # Wait for vLLM to start (it takes a while to load the model)
        logger.info("Waiting for vLLM to load model (this may take 30-60 seconds)...")
        import requests
        for i in range(90):  # Wait up to 90 seconds
            time.sleep(1)
            try:
                response = requests.get(f"{VLLM_URL}/v1/models", timeout=2)
                if response.status_code == 200:
                    logger.info("vLLM started successfully")
                    return True
            except Exception:
                pass

        logger.warning("vLLM may not have started properly - check /tmp/vllm.log in WSL2")
        return False

    except Exception as e:
        logger.error(f"Error starting vLLM: {e}")
        return False

def vllm_status():
    """Get vLLM status information."""
    import requests
    status = {
        'running': is_vllm_running(),
        'responsive': False,
        'model': None
    }

    if status['running']:
        try:
            response = requests.get(f"{VLLM_URL}/v1/models", timeout=5)
            if response.status_code == 200:
                status['responsive'] = True
                data = response.json()
                if data.get('data'):
                    status['model'] = data['data'][0].get('id')
        except:
            pass

    return status
