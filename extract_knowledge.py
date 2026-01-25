#!/usr/bin/env python3
"""
Extract Knowledge - Use LLM to extract structured knowledge from transcripts.

Extracts:
- Actionable tips and best practices
- Step-by-step workflows
- Useful prompts mentioned in videos
- Key insights and techniques

Usage:
    python extract_knowledge.py                    # Process all unprocessed transcripts
    python extract_knowledge.py --video aQvpqlSiUIQ  # Process specific video
    python extract_knowledge.py --force            # Reprocess all transcripts
    python extract_knowledge.py --dry-run          # Show what would be extracted
    python extract_knowledge.py stats              # Show extraction statistics
    python extract_knowledge.py export             # Export all extracted knowledge
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import requests as ollama_requests
    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# LLM Backend setting - options: 'ollama', 'claude', 'groq', 'vllm'
# Ollama is stable and has built-in timeout handling
# vLLM is fast but can hang without proper timeouts
# Groq is 10-20x faster than Ollama (uses custom LPU hardware)
LLM_BACKEND = 'ollama'  # Options: 'ollama', 'claude', 'groq', 'vllm'
OLLAMA_MODEL = 'qwen2.5:14b'  # 14B fits entirely in 24GB VRAM
OLLAMA_URL = 'http://localhost:11434/api/generate'

# vLLM settings (runs in WSL2 on localhost:8000)
VLLM_URL = 'http://localhost:8000/v1'  # OpenAI-compatible API
VLLM_MODEL = 'Qwen/Qwen2.5-7B-Instruct'  # 7B for faster inference

# Groq settings (get free API key at https://console.groq.com/)
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')  # Set in environment or here
GROQ_MODEL = 'llama-3.3-70b-versatile'  # Fast, high quality

# Paths
KNOWLEDGE_BASE = Path(r"D:\AI-Knowledge-Base")
MASTER_DB = KNOWLEDGE_BASE / "master_db.json"
TRANSCRIPTS_DIR = KNOWLEDGE_BASE / "tutorials" / "transcripts"
EXTRACTED_DIR = KNOWLEDGE_BASE / "extracted"
TOKEN_USAGE_FILE = KNOWLEDGE_BASE / "token_usage.json"

# Session token tracking
SESSION_TOKENS = {
    'input': 0,
    'output': 0,
    'total': 0,
    'api_calls': 0
}

# Extraction settings
CHUNK_SIZE = 3000  # Characters per chunk (roughly 750 tokens)
CHUNK_OVERLAP = 200  # Overlap between chunks for context

# =============================================================================
# FABRICATION CONTEXT - Scott's Shop Capabilities
# =============================================================================
# This context helps the LLM identify cross-domain applications connecting
# digital techniques to physical fabrication capabilities.

FABRICATION_CONTEXT = """
FABRICATION CAPABILITIES (for cross-domain connection analysis):

PRECISION MACHINING:
- Fadal VMC4020: CNC machining center for ferrous/non-ferrous metals, high precision parts

LARGE FORMAT CNC:
- ShopBot PRS Alpha: 5'x8' bed, 5HP Colombo spindle
  - Materials: wood, plastics, non-ferrous metals
  - Applications: furniture, cabinets, 3D sculpting, architectural elements, signs
  - Future: rotary axis for spindles, bed posts, columns, totem poles

LASER SYSTEMS:
- 100W Mopa Fiber Laser: metal engraving, marking, annealing, deep engraving
- 55W CO2 Laser: cutting/engraving wood, acrylic, leather, paper

ADDITIVE:
- 3D Printers: prototyping, small parts, models

TRADITIONAL:
- Full machine shop, wood shop, electronics shop

KEY FABRICATION WORKFLOWS TO IDENTIFY:
- 3D capture/scanning → STL/OBJ → CNC machining or 3D printing
- Image/video → depth map → laser engraving or CNC relief carving
- AI generation → physical reproduction
- Reverse engineering → CAD/CAM → fabrication
- Scale transformations (small scan → large carving, or vice versa)
"""

# Extraction prompt template
EXTRACTION_PROMPT = """Analyze this transcript segment from an AI tutorial video and extract structured knowledge.

VIDEO: {video_title}
CHANNEL: {channel}
SEGMENT: {segment_num} of {total_segments}

TRANSCRIPT:
{transcript_chunk}

---
""" + FABRICATION_CONTEXT + """
---

Extract the following in JSON format:

1. **tips**: Actionable tips and best practices mentioned. Each tip should be:
   - Clear and actionable (something someone can do)
   - Self-contained (understandable without the video)
   - Include the approximate timestamp if mentioned

2. **workflows**: Step-by-step processes or workflows described. Each workflow should have:
   - A descriptive name
   - Ordered steps
   - Any prerequisites mentioned

3. **prompts**: Any AI prompts, system prompts, or prompt templates mentioned. Include:
   - The prompt text (as complete as possible)
   - Its purpose/use case

4. **insights**: Key insights or non-obvious observations about AI tools/techniques.

5. **tools_mentioned**: Specific tools, services, or technologies mentioned with context.

6. **fabrication_applications**: Cross-domain connections to physical fabrication. Think creatively about how this technique could connect to CNC machining, laser engraving, 3D printing, woodworking, or metalworking. Consider:
   - Output formats (STL, OBJ, depth maps, G-code, images)
   - Input methods (3D scanning, video capture, AI generation)
   - Scale transformations (small to large or vice versa)
   - Material possibilities

Respond ONLY with valid JSON in this exact format:
{{
  "tips": [
    {{
      "text": "Always create a CLAUDE.md file at the root of your project",
      "category": "project-setup",
      "timestamp_approx": "03:45"
    }}
  ],
  "workflows": [
    {{
      "name": "Claude Code Project Setup",
      "steps": ["Step 1", "Step 2", "Step 3"],
      "prerequisites": ["Have Claude Code installed"]
    }}
  ],
  "prompts": [
    {{
      "text": "You are a senior software architect...",
      "purpose": "Code review prompt"
    }}
  ],
  "insights": [
    {{
      "text": "Plan mode reduces token usage by 40%",
      "topic": "optimization"
    }}
  ],
  "tools_mentioned": [
    {{
      "name": "Claude Code",
      "context": "Main tool for AI-assisted coding"
    }}
  ],
  "fabrication_applications": [
    {{
      "technique": "Video-to-3D capture",
      "outputs": ["3D mesh", "STL", "OBJ"],
      "potential_uses": ["CNC carving of captured objects", "3D printing replicas", "Laser depth engraving"],
      "materials": ["wood", "metal", "plastic"],
      "notes": "Metrically accurate capture enables precise reproduction at any scale"
    }}
  ]
}}

If a category has no items, use an empty array []. For fabrication_applications, think creatively about non-obvious connections - even if the video doesn't explicitly mention fabrication, consider how the technique COULD connect to physical making. Ensure valid JSON output."""


def load_token_usage():
    """Load token usage statistics."""
    if TOKEN_USAGE_FILE.exists():
        with open(TOKEN_USAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'total_input_tokens': 0,
        'total_output_tokens': 0,
        'total_tokens': 0,
        'total_api_calls': 0,
        'sessions': [],
        'first_use': None,
        'last_use': None
    }


def save_token_usage(usage_data):
    """Save token usage statistics."""
    TOKEN_USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_USAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(usage_data, f, indent=2)


def record_token_usage(input_tokens, output_tokens):
    """Record token usage for session and all-time tracking."""
    global SESSION_TOKENS

    # Update session counters
    SESSION_TOKENS['input'] += input_tokens
    SESSION_TOKENS['output'] += output_tokens
    SESSION_TOKENS['total'] += input_tokens + output_tokens
    SESSION_TOKENS['api_calls'] += 1

    # Update all-time counters
    usage = load_token_usage()
    usage['total_input_tokens'] += input_tokens
    usage['total_output_tokens'] += output_tokens
    usage['total_tokens'] += input_tokens + output_tokens
    usage['total_api_calls'] += 1

    now = datetime.now().isoformat()
    if not usage['first_use']:
        usage['first_use'] = now
    usage['last_use'] = now

    save_token_usage(usage)


def finalize_session():
    """Record session summary to token usage file."""
    if SESSION_TOKENS['api_calls'] == 0:
        return

    usage = load_token_usage()
    usage['sessions'].append({
        'date': datetime.now().isoformat(),
        'input_tokens': SESSION_TOKENS['input'],
        'output_tokens': SESSION_TOKENS['output'],
        'total_tokens': SESSION_TOKENS['total'],
        'api_calls': SESSION_TOKENS['api_calls']
    })

    # Keep only last 50 sessions
    usage['sessions'] = usage['sessions'][-50:]
    save_token_usage(usage)


def load_database():
    """Load the master database."""
    if not MASTER_DB.exists():
        return {}
    with open(MASTER_DB, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_database(db):
    """Save the master database."""
    db['metadata']['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    with open(MASTER_DB, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2)


def chunk_transcript(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split transcript into overlapping chunks."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end within last 200 chars
            search_start = max(end - 200, start)
            last_period = text.rfind('. ', search_start, end)
            if last_period > search_start:
                end = last_period + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap
        if start >= len(text):
            break

    return chunks


API_KEY = None  # Global API key storage


def extract_with_ollama(chunk, video_title, channel, segment_num, total_segments):
    """Use Ollama (local QWEN) to extract knowledge from a chunk."""
    prompt = EXTRACTION_PROMPT.format(
        video_title=video_title,
        channel=channel,
        segment_num=segment_num,
        total_segments=total_segments,
        transcript_chunk=chunk
    )

    try:
        response = ollama_requests.post(
            OLLAMA_URL,
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.3,
                    'num_predict': 2000
                }
            },
            timeout=300  # 5 minute timeout per chunk (QWEN 32B is slow)
        )
        response.raise_for_status()

        result = response.json()
        response_text = result.get('response', '')

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"  Warning: Could not parse JSON from response")
            return None

    except json.JSONDecodeError as e:
        print(f"  Warning: JSON parse error: {e}")
        return None
    except ollama_requests.exceptions.Timeout:
        print(f"  Warning: Ollama request timed out")
        return None
    except Exception as e:
        print(f"  Error calling Ollama: {e}")
        return None


def extract_with_claude(chunk, video_title, channel, segment_num, total_segments):
    """Use Claude API to extract knowledge from a chunk."""
    global API_KEY

    if not HAS_ANTHROPIC:
        print("ERROR: anthropic package not installed. Run: pip install anthropic")
        return None

    # Check for API key (global first, then env var)
    api_key = API_KEY or os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set. Use --api-key or set environment variable")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    prompt = EXTRACTION_PROMPT.format(
        video_title=video_title,
        channel=channel,
        segment_num=segment_num,
        total_segments=total_segments,
        transcript_chunk=chunk
    )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Record token usage
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        record_token_usage(input_tokens, output_tokens)

        response_text = message.content[0].text

        # Parse JSON from response
        # Try to find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"  Warning: Could not parse JSON from response")
            return None

    except json.JSONDecodeError as e:
        print(f"  Warning: JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"  Error calling Claude API: {e}")
        return None


def extract_with_groq(chunk, video_title, channel, segment_num, total_segments):
    """Use Groq API for ultra-fast extraction (10-20x faster than Ollama)."""
    if not HAS_GROQ:
        print("ERROR: groq package not installed. Run: pip install groq")
        return None

    api_key = GROQ_API_KEY or os.environ.get('GROQ_API_KEY')
    if not api_key:
        print("ERROR: GROQ_API_KEY not set. Get free key at https://console.groq.com/")
        return None

    client = Groq(api_key=api_key)

    prompt = EXTRACTION_PROMPT.format(
        video_title=video_title,
        channel=channel,
        segment_num=segment_num,
        total_segments=total_segments,
        transcript_chunk=chunk
    )

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        response_text = completion.choices[0].message.content

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"  Warning: Could not parse JSON from response")
            return None

    except json.JSONDecodeError as e:
        print(f"  Warning: JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"  Error calling Groq API: {e}")
        return None


def extract_with_vllm(chunk, video_title, channel, segment_num, total_segments):
    """Use vLLM (local, runs in WSL2) for fast extraction via OpenAI-compatible API."""
    if not HAS_OPENAI:
        print("ERROR: openai package not installed. Run: pip install openai")
        return None

    # Connect to local vLLM server (running in WSL2) with timeout
    client = OpenAI(
        base_url=VLLM_URL,
        api_key="not-needed",  # vLLM doesn't require API key
        timeout=300.0  # 5 minute timeout per request
    )

    prompt = EXTRACTION_PROMPT.format(
        video_title=video_title,
        channel=channel,
        segment_num=segment_num,
        total_segments=total_segments,
        transcript_chunk=chunk
    )

    try:
        completion = client.chat.completions.create(
            model=VLLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            timeout=300  # 5 minute timeout
        )

        response_text = completion.choices[0].message.content

        # Parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            return json.loads(json_match.group())
        else:
            print(f"  Warning: Could not parse JSON from response")
            return None

    except json.JSONDecodeError as e:
        print(f"  Warning: JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"  Error calling vLLM API: {e}")
        return None


def extract_knowledge(chunk, video_title, channel, segment_num, total_segments):
    """Extract knowledge using configured backend (Ollama, Claude, Groq, or vLLM)."""
    if LLM_BACKEND == 'ollama':
        return extract_with_ollama(chunk, video_title, channel, segment_num, total_segments)
    elif LLM_BACKEND == 'groq':
        return extract_with_groq(chunk, video_title, channel, segment_num, total_segments)
    elif LLM_BACKEND == 'vllm':
        return extract_with_vllm(chunk, video_title, channel, segment_num, total_segments)
    else:
        return extract_with_claude(chunk, video_title, channel, segment_num, total_segments)


def merge_extractions(extractions):
    """Merge and deduplicate extractions from multiple chunks."""
    merged = {
        'tips': [],
        'workflows': [],
        'prompts': [],
        'insights': [],
        'tools_mentioned': [],
        'fabrication_applications': []
    }

    seen_tips = set()
    seen_workflows = set()
    seen_prompts = set()
    seen_insights = set()
    seen_tools = set()
    seen_fabrication = set()

    for extraction in extractions:
        if not extraction:
            continue

        # Merge tips (dedupe by text similarity)
        for tip in extraction.get('tips', []):
            tip_key = tip.get('text', '')[:50].lower()
            if tip_key and tip_key not in seen_tips:
                seen_tips.add(tip_key)
                merged['tips'].append(tip)

        # Merge workflows (dedupe by name)
        for workflow in extraction.get('workflows', []):
            wf_key = workflow.get('name', '').lower()
            if wf_key and wf_key not in seen_workflows:
                seen_workflows.add(wf_key)
                merged['workflows'].append(workflow)

        # Merge prompts (dedupe by text start)
        for prompt in extraction.get('prompts', []):
            prompt_key = prompt.get('text', '')[:50].lower()
            if prompt_key and prompt_key not in seen_prompts:
                seen_prompts.add(prompt_key)
                merged['prompts'].append(prompt)

        # Merge insights
        for insight in extraction.get('insights', []):
            insight_key = insight.get('text', '')[:50].lower()
            if insight_key and insight_key not in seen_insights:
                seen_insights.add(insight_key)
                merged['insights'].append(insight)

        # Merge tools
        for tool in extraction.get('tools_mentioned', []):
            tool_key = tool.get('name', '').lower()
            if tool_key and tool_key not in seen_tools:
                seen_tools.add(tool_key)
                merged['tools_mentioned'].append(tool)

        # Merge fabrication applications (dedupe by technique name)
        for fab in extraction.get('fabrication_applications', []):
            fab_key = fab.get('technique', '').lower()
            if fab_key and fab_key not in seen_fabrication:
                seen_fabrication.add(fab_key)
                merged['fabrication_applications'].append(fab)

    return merged


def process_transcript(video_id, force=False, dry_run=False):
    """Process a single transcript and extract knowledge."""
    db = load_database()

    # Find video in database
    video_info = None
    for tutorial in db.get('tutorials', []):
        if tutorial.get('video_id') == video_id:
            video_info = tutorial
            break

    if not video_info:
        print(f"Video {video_id} not found in database")
        return None

    # Check if already processed
    if video_info.get('llm_extracted') and not force:
        print(f"Video {video_id} already processed. Use --force to reprocess.")
        return None

    # Find transcript file
    transcript_file = None
    for f in TRANSCRIPTS_DIR.glob(f"{video_id}*.txt"):
        transcript_file = f
        break

    if not transcript_file:
        print(f"Transcript not found for {video_id}")
        return None

    # Read transcript
    with open(transcript_file, 'r', encoding='utf-8') as f:
        transcript_text = f.read()

    video_title = video_info.get('title', 'Unknown')
    channel = video_info.get('channel', 'Unknown')

    print(f"\nProcessing: {video_title}")
    print(f"  Video ID: {video_id}")
    print(f"  Channel: {channel}")
    print(f"  Transcript: {len(transcript_text)} characters")

    # Chunk the transcript
    chunks = chunk_transcript(transcript_text)
    print(f"  Chunks: {len(chunks)}")

    if dry_run:
        print(f"  [DRY RUN] Would process {len(chunks)} chunks with Claude API")
        return None

    # Process each chunk
    extractions = []
    for i, chunk in enumerate(chunks, 1):
        print(f"  Processing chunk {i}/{len(chunks)}...", end=' ')

        result = extract_knowledge(
            chunk,
            video_title,
            channel,
            i,
            len(chunks)
        )

        if result:
            tips_count = len(result.get('tips', []))
            workflows_count = len(result.get('workflows', []))
            print(f"Found {tips_count} tips, {workflows_count} workflows")
            extractions.append(result)
        else:
            print("No results")

    # Merge all extractions
    merged = merge_extractions(extractions)

    # Add metadata
    merged['video_id'] = video_id
    merged['video_title'] = video_title
    merged['channel'] = channel
    merged['extracted_at'] = datetime.now().isoformat()
    merged['chunks_processed'] = len(chunks)

    # Save individual extraction file
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    extraction_file = EXTRACTED_DIR / f"{video_id}_knowledge.json"
    with open(extraction_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2)

    print(f"\n  Extraction complete:")
    print(f"    Tips: {len(merged['tips'])}")
    print(f"    Workflows: {len(merged['workflows'])}")
    print(f"    Prompts: {len(merged['prompts'])}")
    print(f"    Insights: {len(merged['insights'])}")
    print(f"    Tools: {len(merged['tools_mentioned'])}")
    print(f"    Fabrication Apps: {len(merged['fabrication_applications'])}")
    print(f"  Saved to: {extraction_file}")

    # Update database
    video_info['llm_extracted'] = True
    video_info['llm_extraction_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    video_info['llm_tips_count'] = len(merged['tips'])
    video_info['llm_workflows_count'] = len(merged['workflows'])
    video_info['llm_fabrication_count'] = len(merged['fabrication_applications'])
    save_database(db)

    return merged


def process_all_transcripts(force=False, dry_run=False):
    """Process all unprocessed transcripts."""
    db = load_database()

    processed = 0
    skipped = 0
    errors = 0

    for tutorial in db.get('tutorials', []):
        video_id = tutorial.get('video_id')
        if not video_id:
            continue

        # Check if has transcript
        if not tutorial.get('has_transcript'):
            continue

        # Check if already processed
        if tutorial.get('llm_extracted') and not force:
            skipped += 1
            continue

        result = process_transcript(video_id, force=force, dry_run=dry_run)
        if result:
            processed += 1
        else:
            if not dry_run:
                errors += 1

    # Finalize session token tracking
    finalize_session()

    print(f"\n{'='*50}")
    print(f"Processing complete:")
    print(f"  Processed: {processed}")
    print(f"  Skipped (already done): {skipped}")
    print(f"  Errors: {errors}")

    # Show session token usage
    if SESSION_TOKENS['api_calls'] > 0:
        print(f"\nSession Token Usage:")
        print(f"  Input tokens:  {SESSION_TOKENS['input']:,}")
        print(f"  Output tokens: {SESSION_TOKENS['output']:,}")
        print(f"  Total tokens:  {SESSION_TOKENS['total']:,}")
        print(f"  API calls:     {SESSION_TOKENS['api_calls']}")


def aggregate_all_knowledge():
    """Aggregate all extracted knowledge into master files."""
    all_tips = []
    all_workflows = []
    all_prompts = []
    all_insights = []
    all_fabrication = []

    # Load all extraction files
    for extraction_file in EXTRACTED_DIR.glob("*_knowledge.json"):
        with open(extraction_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        video_id = data.get('video_id', extraction_file.stem.replace('_knowledge', ''))
        video_title = data.get('video_title', 'Unknown')

        # Add source info to each item
        for tip in data.get('tips', []):
            tip['source_video'] = video_id
            tip['source_title'] = video_title
            all_tips.append(tip)

        for workflow in data.get('workflows', []):
            workflow['source_video'] = video_id
            workflow['source_title'] = video_title
            all_workflows.append(workflow)

        for prompt in data.get('prompts', []):
            prompt['source_video'] = video_id
            prompt['source_title'] = video_title
            all_prompts.append(prompt)

        for insight in data.get('insights', []):
            insight['source_video'] = video_id
            insight['source_title'] = video_title
            all_insights.append(insight)

        for fab in data.get('fabrication_applications', []):
            fab['source_video'] = video_id
            fab['source_title'] = video_title
            all_fabrication.append(fab)

    # Save aggregated files
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    with open(EXTRACTED_DIR / 'all_tips.json', 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().isoformat(),
            'total': len(all_tips),
            'tips': all_tips
        }, f, indent=2)

    with open(EXTRACTED_DIR / 'all_workflows.json', 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().isoformat(),
            'total': len(all_workflows),
            'workflows': all_workflows
        }, f, indent=2)

    with open(EXTRACTED_DIR / 'all_prompts.json', 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().isoformat(),
            'total': len(all_prompts),
            'prompts': all_prompts
        }, f, indent=2)

    with open(EXTRACTED_DIR / 'all_insights.json', 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().isoformat(),
            'total': len(all_insights),
            'insights': all_insights
        }, f, indent=2)

    with open(EXTRACTED_DIR / 'all_fabrication.json', 'w', encoding='utf-8') as f:
        json.dump({
            'extracted_at': datetime.now().isoformat(),
            'total': len(all_fabrication),
            'fabrication_context': FABRICATION_CONTEXT,
            'applications': all_fabrication
        }, f, indent=2)

    print(f"Aggregated knowledge saved:")
    print(f"  Tips: {len(all_tips)} -> all_tips.json")
    print(f"  Workflows: {len(all_workflows)} -> all_workflows.json")
    print(f"  Prompts: {len(all_prompts)} -> all_prompts.json")
    print(f"  Insights: {len(all_insights)} -> all_insights.json")
    print(f"  Fabrication: {len(all_fabrication)} -> all_fabrication.json")

    return {
        'tips': len(all_tips),
        'workflows': len(all_workflows),
        'prompts': len(all_prompts),
        'insights': len(all_insights),
        'fabrication': len(all_fabrication)
    }


def show_stats():
    """Show extraction statistics."""
    db = load_database()

    print("\n=== KNOWLEDGE EXTRACTION STATISTICS ===")
    print("="*50)

    # Count processed videos
    total_tutorials = len(db.get('tutorials', []))
    processed = sum(1 for t in db.get('tutorials', []) if t.get('llm_extracted'))
    with_transcripts = sum(1 for t in db.get('tutorials', []) if t.get('has_transcript'))

    print(f"\nTutorials:")
    print(f"  Total in database: {total_tutorials}")
    print(f"  With transcripts: {with_transcripts}")
    print(f"  LLM processed: {processed}")
    print(f"  Pending: {with_transcripts - processed}")

    # Count extracted items
    total_tips = 0
    total_workflows = 0
    total_prompts = 0
    total_insights = 0

    for extraction_file in EXTRACTED_DIR.glob("*_knowledge.json"):
        with open(extraction_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        total_tips += len(data.get('tips', []))
        total_workflows += len(data.get('workflows', []))
        total_prompts += len(data.get('prompts', []))
        total_insights += len(data.get('insights', []))

    print(f"\nExtracted Knowledge:")
    print(f"  Tips: {total_tips}")
    print(f"  Workflows: {total_workflows}")
    print(f"  Prompts: {total_prompts}")
    print(f"  Insights: {total_insights}")
    print(f"  Total items: {total_tips + total_workflows + total_prompts + total_insights}")

    # Show by video
    print(f"\nBy Video:")
    for tutorial in db.get('tutorials', []):
        if tutorial.get('llm_extracted'):
            tips = tutorial.get('llm_tips_count', 0)
            workflows = tutorial.get('llm_workflows_count', 0)
            print(f"  {tutorial.get('title', 'Unknown')[:40]}...")
            print(f"    Tips: {tips}, Workflows: {workflows}")


def show_token_stats():
    """Show API token usage statistics."""
    usage = load_token_usage()

    print("\n=== API TOKEN USAGE STATISTICS ===")
    print("="*50)

    # All-time stats
    print(f"\nAll-Time Usage:")
    print(f"  Input tokens:  {usage['total_input_tokens']:,}")
    print(f"  Output tokens: {usage['total_output_tokens']:,}")
    print(f"  Total tokens:  {usage['total_tokens']:,}")
    print(f"  API calls:     {usage['total_api_calls']:,}")

    if usage['first_use']:
        print(f"\n  First use: {usage['first_use'][:19].replace('T', ' ')}")
    if usage['last_use']:
        print(f"  Last use:  {usage['last_use'][:19].replace('T', ' ')}")

    # Estimate costs (Claude Sonnet pricing as of 2025)
    # Input: $3/million tokens, Output: $15/million tokens
    input_cost = (usage['total_input_tokens'] / 1_000_000) * 3.00
    output_cost = (usage['total_output_tokens'] / 1_000_000) * 15.00
    total_cost = input_cost + output_cost

    print(f"\n  Estimated cost: ${total_cost:.4f}")
    print(f"    Input:  ${input_cost:.4f}")
    print(f"    Output: ${output_cost:.4f}")

    # Recent sessions
    sessions = usage.get('sessions', [])
    if sessions:
        print(f"\nRecent Sessions (last 5):")
        for session in sessions[-5:]:
            date = session['date'][:19].replace('T', ' ')
            total = session['total_tokens']
            calls = session['api_calls']
            print(f"  {date}: {total:,} tokens ({calls} calls)")

    # Current session (if any)
    if SESSION_TOKENS['api_calls'] > 0:
        print(f"\nCurrent Session:")
        print(f"  Input tokens:  {SESSION_TOKENS['input']:,}")
        print(f"  Output tokens: {SESSION_TOKENS['output']:,}")
        print(f"  Total tokens:  {SESSION_TOKENS['total']:,}")
        print(f"  API calls:     {SESSION_TOKENS['api_calls']}")


def export_knowledge_markdown():
    """Export all extracted knowledge as markdown."""
    exports_dir = KNOWLEDGE_BASE / 'exports'
    exports_dir.mkdir(parents=True, exist_ok=True)

    # Load all knowledge
    all_tips = []
    all_workflows = []
    all_prompts = []

    for extraction_file in EXTRACTED_DIR.glob("*_knowledge.json"):
        with open(extraction_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        video_title = data.get('video_title', 'Unknown')
        video_id = data.get('video_id', '')

        for tip in data.get('tips', []):
            tip['_source'] = f"[{video_title}](https://youtube.com/watch?v={video_id})"
            all_tips.append(tip)

        for workflow in data.get('workflows', []):
            workflow['_source'] = f"[{video_title}](https://youtube.com/watch?v={video_id})"
            all_workflows.append(workflow)

        for prompt in data.get('prompts', []):
            prompt['_source'] = f"[{video_title}](https://youtube.com/watch?v={video_id})"
            all_prompts.append(prompt)

    # Generate Tips markdown
    md = "# Extracted Tips\n\n"
    md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    md += f"Total tips: {len(all_tips)}\n\n---\n\n"

    # Group by category
    tips_by_category = {}
    for tip in all_tips:
        category = tip.get('category', 'general')
        if category not in tips_by_category:
            tips_by_category[category] = []
        tips_by_category[category].append(tip)

    for category, tips in sorted(tips_by_category.items()):
        md += f"## {category.replace('-', ' ').title()}\n\n"
        for tip in tips:
            md += f"- {tip.get('text', '')}\n"
            md += f"  - Source: {tip.get('_source', 'Unknown')}\n"
            if tip.get('timestamp_approx'):
                md += f"  - Timestamp: ~{tip['timestamp_approx']}\n"
            md += "\n"

    with open(exports_dir / 'extracted_tips.md', 'w', encoding='utf-8') as f:
        f.write(md)

    # Generate Workflows markdown
    md = "# Extracted Workflows\n\n"
    md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    md += f"Total workflows: {len(all_workflows)}\n\n---\n\n"

    for workflow in all_workflows:
        md += f"## {workflow.get('name', 'Unnamed Workflow')}\n\n"
        md += f"Source: {workflow.get('_source', 'Unknown')}\n\n"

        if workflow.get('prerequisites'):
            md += "**Prerequisites:**\n"
            for prereq in workflow['prerequisites']:
                md += f"- {prereq}\n"
            md += "\n"

        md += "**Steps:**\n"
        for i, step in enumerate(workflow.get('steps', []), 1):
            md += f"{i}. {step}\n"
        md += "\n---\n\n"

    with open(exports_dir / 'extracted_workflows.md', 'w', encoding='utf-8') as f:
        f.write(md)

    # Generate Prompts markdown
    md = "# Extracted Prompts\n\n"
    md += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    md += f"Total prompts: {len(all_prompts)}\n\n---\n\n"

    for prompt in all_prompts:
        md += f"## {prompt.get('purpose', 'Unnamed Prompt')}\n\n"
        md += f"Source: {prompt.get('_source', 'Unknown')}\n\n"
        md += "```\n"
        md += prompt.get('text', '')
        md += "\n```\n\n---\n\n"

    with open(exports_dir / 'extracted_prompts.md', 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"Exported to {exports_dir}:")
    print(f"  extracted_tips.md ({len(all_tips)} tips)")
    print(f"  extracted_workflows.md ({len(all_workflows)} workflows)")
    print(f"  extracted_prompts.md ({len(all_prompts)} prompts)")


def main():
    parser = argparse.ArgumentParser(
        description='Extract structured knowledge from transcripts using LLM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python extract_knowledge.py                      # Process all unprocessed
  python extract_knowledge.py --video aQvpqlSiUIQ  # Process specific video
  python extract_knowledge.py --force              # Reprocess all
  python extract_knowledge.py --dry-run            # Preview without API calls
  python extract_knowledge.py stats                # Show statistics
  python extract_knowledge.py export               # Export to markdown
  python extract_knowledge.py aggregate            # Aggregate all extractions

Requirements:
  - pip install anthropic
  - Set ANTHROPIC_API_KEY environment variable
        '''
    )

    parser.add_argument('--video', '-v', help='Process specific video ID')
    parser.add_argument('--force', '-f', action='store_true', help='Reprocess already extracted')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Preview without API calls')
    parser.add_argument('--api-key', '-k', help='Anthropic API key')

    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('stats', help='Show extraction statistics')
    subparsers.add_parser('export', help='Export knowledge to markdown')
    subparsers.add_parser('aggregate', help='Aggregate all extractions')
    subparsers.add_parser('token-stats', help='Show API token usage statistics')

    args = parser.parse_args()

    # Set global API key if provided
    global API_KEY
    if args.api_key:
        API_KEY = args.api_key

    if args.command == 'stats':
        show_stats()
    elif args.command == 'token-stats':
        show_token_stats()
    elif args.command == 'export':
        export_knowledge_markdown()
    elif args.command == 'aggregate':
        aggregate_all_knowledge()
    elif args.video:
        process_transcript(args.video, force=args.force, dry_run=args.dry_run)
        finalize_session()
        if SESSION_TOKENS['api_calls'] > 0:
            print(f"\nSession Token Usage:")
            print(f"  Input tokens:  {SESSION_TOKENS['input']:,}")
            print(f"  Output tokens: {SESSION_TOKENS['output']:,}")
            print(f"  Total tokens:  {SESSION_TOKENS['total']:,}")
            print(f"  API calls:     {SESSION_TOKENS['api_calls']}")
    else:
        # Check for LLM backend availability before processing
        if not args.dry_run:
            if LLM_BACKEND == 'ollama':
                # Check if Ollama is running
                try:
                    resp = ollama_requests.get('http://localhost:11434', timeout=5)
                    print(f"Using Ollama with model: {OLLAMA_MODEL}")
                except Exception:
                    print("ERROR: Ollama is not running at localhost:11434")
                    print("Start Ollama first: ollama serve")
                    sys.exit(1)
            elif LLM_BACKEND == 'vllm':
                # Check if vLLM is running
                try:
                    resp = ollama_requests.get(f'{VLLM_URL}/models', timeout=5)
                    print(f"Using vLLM with model: {VLLM_MODEL}")
                except Exception:
                    print(f"ERROR: vLLM is not running at {VLLM_URL}")
                    print("Start vLLM in WSL2: vllm serve Qwen/Qwen2.5-7B-Instruct --port 8000")
                    sys.exit(1)
            elif LLM_BACKEND == 'groq':
                if not HAS_GROQ:
                    print("ERROR: groq package not installed")
                    print("Run: pip install groq")
                    sys.exit(1)
                if not GROQ_API_KEY and not os.environ.get('GROQ_API_KEY'):
                    print("ERROR: GROQ_API_KEY not provided")
                    print("Get free key at https://console.groq.com/")
                    sys.exit(1)
                print(f"Using Groq with model: {GROQ_MODEL}")
            else:
                if not HAS_ANTHROPIC:
                    print("ERROR: anthropic package not installed")
                    print("Run: pip install anthropic")
                    sys.exit(1)
                if not API_KEY and not os.environ.get('ANTHROPIC_API_KEY'):
                    print("ERROR: ANTHROPIC_API_KEY not provided")
                    print("Use --api-key YOUR_KEY or set ANTHROPIC_API_KEY environment variable")
                    sys.exit(1)

        process_all_transcripts(force=args.force, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
