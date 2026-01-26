"""
Transcript Translation Module
Translates non-English YouTube transcripts to English using local LLMs.

Supports two backends:
1. vLLM (Qwen2.5-7B-Instruct) - Already running, good multilingual support
2. Helsinki-NLP/opus-mt - Lightweight, dedicated translation models (fallback)
"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import os
import re
import requests
from datetime import datetime
from pathlib import Path

# Import centralized config
from kb_config import (
    get_logger, ProgressTracker, backup_database,
    MASTER_DB, TRANSCRIPTS_DIR, VLLM_URL
)

# Setup logger
logger = get_logger("TranslateTranscripts")

# Paths
MASTER_DB_PATH = str(MASTER_DB)
TRANSCRIPTS_PATH = str(TRANSCRIPTS_DIR)

# Translation settings
CHUNK_SIZE = 2000  # Characters per chunk for translation
MAX_RETRIES = 3

# Language code to full name mapping
LANGUAGE_NAMES = {
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ru': 'Russian',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'nl': 'Dutch',
    'pl': 'Polish',
    'tr': 'Turkish',
    'vi': 'Vietnamese',
    'th': 'Thai',
    'id': 'Indonesian',
    'sv': 'Swedish',
    'da': 'Danish',
    'no': 'Norwegian',
    'fi': 'Finnish',
}

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def load_db():
    """Load the master database."""
    if os.path.exists(MASTER_DB_PATH):
        with open(MASTER_DB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_db(db):
    """Save the master database."""
    db['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    with open(MASTER_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# =============================================================================
# VLLM TRANSLATION (Primary)
# =============================================================================

def translate_with_vllm(text, source_lang='es', target_lang='en'):
    """
    Translate text using vLLM (Qwen2.5-7B-Instruct).

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code (default English)

    Returns:
        Translated text or None on failure
    """
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    target_name = LANGUAGE_NAMES.get(target_lang, 'English')

    prompt = f"""Translate the following {source_name} text to {target_name}.
Provide only the translation, no explanations or notes.

Text to translate:
{text}

Translation:"""

    try:
        response = requests.post(
            f"{VLLM_URL}/chat/completions",
            json={
                "model": "Qwen/Qwen2.5-7B-Instruct",
                "messages": [
                    {"role": "system", "content": f"You are a professional translator. Translate from {source_name} to {target_name} accurately and naturally."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": len(text) * 2,  # Allow for expansion
                "temperature": 0.1,  # Low temperature for consistent translation
            },
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            translated = result['choices'][0]['message']['content'].strip()
            return translated
        else:
            logger.error(f"vLLM error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.Timeout:
        logger.error("vLLM translation timeout")
        return None
    except Exception as e:
        logger.error(f"vLLM translation error: {e}")
        return None

# =============================================================================
# OPUS-MT TRANSLATION (Fallback - lightweight)
# =============================================================================

_opus_models = {}  # Cache loaded models

def get_opus_model(source_lang, target_lang='en'):
    """
    Load Helsinki-NLP/opus-mt model for a language pair.
    Models are cached after first load.
    """
    model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"

    if model_name in _opus_models:
        return _opus_models[model_name]

    try:
        from transformers import MarianMTModel, MarianTokenizer

        logger.info(f"Loading translation model: {model_name}")
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)

        _opus_models[model_name] = (tokenizer, model)
        return (tokenizer, model)

    except Exception as e:
        logger.error(f"Could not load opus-mt model {model_name}: {e}")
        return None

def translate_with_opus(text, source_lang='es', target_lang='en'):
    """
    Translate text using Helsinki-NLP/opus-mt models.
    These are small, fast, and purpose-built for translation.

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        Translated text or None on failure
    """
    model_data = get_opus_model(source_lang, target_lang)
    if not model_data:
        return None

    tokenizer, model = model_data

    try:
        # Tokenize and translate
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        translated = model.generate(**inputs)
        result = tokenizer.decode(translated[0], skip_special_tokens=True)
        return result

    except Exception as e:
        logger.error(f"Opus-MT translation error: {e}")
        return None

# =============================================================================
# TRANSLATION ORCHESTRATION
# =============================================================================

def translate_text(text, source_lang='es', target_lang='en', backend='vllm'):
    """
    Translate text using specified backend.

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code
        backend: 'vllm' (default) or 'opus'

    Returns:
        Translated text or None on failure
    """
    if backend == 'vllm':
        return translate_with_vllm(text, source_lang, target_lang)
    elif backend == 'opus':
        return translate_with_opus(text, source_lang, target_lang)
    else:
        logger.error(f"Unknown translation backend: {backend}")
        return None

def translate_long_text(text, source_lang='es', target_lang='en', backend='vllm'):
    """
    Translate long text by chunking into smaller pieces.

    Args:
        text: Long text to translate
        source_lang: Source language code
        target_lang: Target language code
        backend: Translation backend to use

    Returns:
        Fully translated text or None on failure
    """
    if len(text) <= CHUNK_SIZE:
        return translate_text(text, source_lang, target_lang, backend)

    # Split into chunks at sentence boundaries
    chunks = []
    current_chunk = ""

    # Split by sentences (rough approximation)
    sentences = re.split(r'(?<=[.!?])\s+', text)

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= CHUNK_SIZE:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Translate each chunk
    translated_chunks = []
    for i, chunk in enumerate(chunks):
        logger.info(f"  Translating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
        translated = translate_text(chunk, source_lang, target_lang, backend)
        if translated:
            translated_chunks.append(translated)
        else:
            logger.error(f"  Failed to translate chunk {i+1}")
            return None

    return " ".join(translated_chunks)

# =============================================================================
# TRANSCRIPT PROCESSING
# =============================================================================

def find_transcript_file(video_id):
    """Find the transcript file for a video ID."""
    transcript_dir = Path(TRANSCRIPTS_PATH)

    # Look for files matching the video ID
    for file in transcript_dir.glob(f"{video_id}*.txt"):
        return str(file)

    return None

def read_transcript_text(filepath):
    """Read the raw transcript text from a transcript file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract just the transcript text (after "TRANSCRIPT" header)
        if "TRANSCRIPT\n" in content:
            parts = content.split("TRANSCRIPT\n", 1)
            if len(parts) > 1:
                # Get text before timestamped segments
                text = parts[1]
                if "TIMESTAMPED SEGMENTS" in text:
                    text = text.split("TIMESTAMPED SEGMENTS")[0]
                return text.strip()

        return None

    except Exception as e:
        logger.error(f"Error reading transcript: {e}")
        return None

def save_translated_transcript(video_id, original_lang, translated_text, metadata=None):
    """Save translated transcript to file."""
    transcript_dir = Path(TRANSCRIPTS_PATH)

    # Build filename
    if metadata and metadata.get('title'):
        safe_title = re.sub(r'[<>:"/\\|?*]', '', metadata['title'])
        safe_title = safe_title[:50].strip()
        filename = f"{video_id}_{safe_title}_EN.txt"
    else:
        filename = f"{video_id}_translated_EN.txt"

    filepath = transcript_dir / filename

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"YouTube Video Transcript (Translated to English)\n")
        f.write(f"{'=' * 60}\n\n")

        if metadata:
            f.write(f"Title: {metadata.get('title', 'Unknown')}\n")
            f.write(f"Channel: {metadata.get('channel', 'Unknown')}\n")
            f.write(f"Original Language: {LANGUAGE_NAMES.get(original_lang, original_lang)}\n")
            f.write(f"URL: https://youtube.com/watch?v={video_id}\n")
            f.write(f"Translated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"\n{'=' * 60}\n\n")

        f.write("TRANSLATED TRANSCRIPT (English)\n")
        f.write(f"{'-' * 60}\n\n")
        f.write(translated_text)
        f.write("\n")

    return str(filepath)

def process_translations(backend='vllm', force=False):
    """
    Process all transcripts that need translation.

    Args:
        backend: Translation backend ('vllm' or 'opus')
        force: If True, re-translate already translated transcripts
    """
    logger.info("=" * 70)
    logger.info("TRANSCRIPT TRANSLATION")
    logger.info(f"Backend: {backend.upper()}")
    logger.info("=" * 70)

    # Check vLLM availability if using that backend
    if backend == 'vllm':
        try:
            response = requests.get(f"{VLLM_URL}/models", timeout=5)
            if response.status_code != 200:
                logger.error("vLLM not available. Start it with: vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000")
                return
        except:
            logger.error("vLLM not available. Start it with: vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000")
            return

    # Backup database
    backup_path = backup_database(reason="translation")
    if backup_path:
        logger.info(f"Database backed up to: {backup_path}")

    db = load_db()
    if not db:
        logger.error("Could not load database")
        return

    tutorials = db.get('tutorials', [])

    # Find tutorials needing translation
    to_translate = []
    for t in tutorials:
        if t.get('needs_translation') and t.get('has_transcript'):
            if force or not t.get('translated_to_english'):
                to_translate.append(t)

    if not to_translate:
        logger.info("No transcripts need translation.")
        return

    logger.info(f"Found {len(to_translate)} transcripts to translate")

    # Initialize progress tracker
    tracker = ProgressTracker(total=len(to_translate), description="Translation")

    translated_count = 0
    error_count = 0

    for tutorial in to_translate:
        video_id = tutorial.get('video_id')
        source_lang = tutorial.get('transcript_language', 'es')
        title = tutorial.get('title', video_id)[:40]

        logger.info(f"Translating: {title}")
        logger.info(f"  Language: {LANGUAGE_NAMES.get(source_lang, source_lang)} -> English")

        # Find and read original transcript
        transcript_file = find_transcript_file(video_id)
        if not transcript_file:
            logger.warning(f"  No transcript file found for {video_id}")
            error_count += 1
            tracker.update()
            continue

        original_text = read_transcript_text(transcript_file)
        if not original_text:
            logger.warning(f"  Could not read transcript text for {video_id}")
            error_count += 1
            tracker.update()
            continue

        logger.info(f"  Original: {len(original_text)} characters")

        # Translate
        translated_text = translate_long_text(original_text, source_lang, 'en', backend)

        if translated_text:
            logger.info(f"  Translated: {len(translated_text)} characters")

            # Save translated transcript
            output_path = save_translated_transcript(
                video_id, source_lang, translated_text,
                metadata={'title': tutorial.get('title'), 'channel': tutorial.get('channel')}
            )
            logger.info(f"  Saved: {os.path.basename(output_path)}")

            # Update database
            tutorial['translated_to_english'] = True
            tutorial['translation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            tutorial['translation_backend'] = backend

            translated_count += 1
        else:
            logger.error(f"  Translation failed for {video_id}")
            error_count += 1

        tracker.update()

    # Save database
    save_db(db)
    tracker.finish()

    print("\n" + "=" * 70)
    print("TRANSLATION SUMMARY")
    print("=" * 70)
    print(f"  Translated: {translated_count}")
    print(f"  Errors:     {error_count}")
    print(f"  Backend:    {backend}")

def show_status():
    """Show translation status."""
    db = load_db()
    if not db:
        print("ERROR: Could not load database")
        return

    tutorials = db.get('tutorials', [])

    needs_translation = [t for t in tutorials if t.get('needs_translation')]
    already_translated = [t for t in tutorials if t.get('translated_to_english')]
    pending = [t for t in needs_translation if not t.get('translated_to_english')]

    print("\n" + "=" * 50)
    print("TRANSLATION STATUS")
    print("=" * 50)
    print(f"  Need translation:     {len(needs_translation)}")
    print(f"  Already translated:   {len(already_translated)}")
    print(f"  Pending:              {len(pending)}")

    if pending:
        print("\n" + "-" * 50)
        print("PENDING TRANSLATIONS")
        print("-" * 50)
        for t in pending:
            title = t.get('title', t.get('video_id', 'Unknown'))[:40]
            lang = t.get('transcript_language', 'unknown')
            lang_name = LANGUAGE_NAMES.get(lang, lang)
            print(f"  - {title} ({lang_name})")

    if already_translated:
        print("\n" + "-" * 50)
        print("COMPLETED TRANSLATIONS")
        print("-" * 50)
        for t in already_translated:
            title = t.get('title', t.get('video_id', 'Unknown'))[:40]
            backend = t.get('translation_backend', 'unknown')
            print(f"  - {title} (via {backend})")

# =============================================================================
# CLI
# =============================================================================

def main():
    """Main CLI entry point."""
    import sys

    if len(sys.argv) < 2:
        print("Transcript Translation Tool")
        print("=" * 50)
        print("\nUsage:")
        print("  python translate_transcripts.py <command> [options]")
        print("\nCommands:")
        print("  translate            Translate pending transcripts")
        print("  translate --force    Re-translate all (including already done)")
        print("  translate --opus     Use opus-mt backend instead of vLLM")
        print("  status               Show translation status")
        print("  test <text>          Test translation with sample text")
        print("\nBackends:")
        print("  vLLM (default) - Uses Qwen2.5-7B-Instruct (already running)")
        print("  opus-mt        - Lightweight Helsinki-NLP models (auto-downloads)")
        return

    cmd = sys.argv[1].lower()

    if cmd == 'translate':
        force = '--force' in sys.argv
        backend = 'opus' if '--opus' in sys.argv else 'vllm'
        process_translations(backend=backend, force=force)

    elif cmd == 'status':
        show_status()

    elif cmd == 'test' and len(sys.argv) > 2:
        # Test translation with provided text
        test_text = ' '.join(sys.argv[2:])
        print(f"Testing translation: {test_text[:50]}...")

        backend = 'opus' if '--opus' in sys.argv else 'vllm'
        print(f"Backend: {backend}")

        result = translate_text(test_text, 'es', 'en', backend)
        if result:
            print(f"\nTranslation: {result}")
        else:
            print("Translation failed")

    else:
        print(f"Unknown command: {cmd}")
        print("Run without arguments for help.")

if __name__ == "__main__":
    main()
