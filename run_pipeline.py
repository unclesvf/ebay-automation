#!/usr/bin/env python3
"""
AI Knowledge Base Pipeline - Master orchestration script.

Runs all AI Knowledge Base scripts in the correct order with a single command.

Usage:
    python run_pipeline.py                          # Full pipeline (includes LLM)
    python run_pipeline.py --skip-llm               # Skip LLM extraction to save $
    python run_pipeline.py --stage reports          # Run single stage
    python run_pipeline.py --stages youtube,analyze # Run multiple stages
    python run_pipeline.py --from youtube           # Run from stage onwards
    python run_pipeline.py --dry-run                # Preview what would run
    python run_pipeline.py --list-stages            # List available stages
    python run_pipeline.py status                   # Show knowledge base status
"""

import os
import sys
import json
import argparse
import subprocess
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Paths
SCRIPT_DIR = Path(__file__).parent
KNOWLEDGE_BASE = Path(r"D:\AI-Knowledge-Base")
MASTER_DB = KNOWLEDGE_BASE / "master_db.json"
STATE_FILE = SCRIPT_DIR / "pipeline_state.json"


@dataclass
class Stage:
    """Represents a pipeline stage."""
    id: str
    script: str
    description: str
    args: List[str] = field(default_factory=list)
    default_enabled: bool = True
    requires_api_key: bool = False


@dataclass
class StageResult:
    """Result of running a pipeline stage."""
    stage_id: str
    status: str  # 'success', 'partial', 'failed', 'skipped'
    duration_seconds: float
    items_processed: int = 0
    errors: List[str] = field(default_factory=list)
    output_summary: str = ""


# Pipeline stages in execution order
STAGES = [
    Stage(
        id='organize',
        script='scott_folder_organizer.py',
        description='Organize Outlook emails, extract X-Twitter posts',
        default_enabled=True
    ),
    Stage(
        id='extract',
        script='ai_content_extractor.py',
        description='Extract GitHub/HuggingFace/YouTube URLs from emails',
        args=['--all'],
        default_enabled=True
    ),
    Stage(
        id='youtube',
        script='youtube_metadata.py',
        description='Fetch video metadata and transcripts',
        args=['all'],
        default_enabled=True
    ),
    Stage(
        id='analyze',
        script='transcript_analyzer.py',
        description='Extract tools, techniques, tips from transcripts',
        args=['all'],
        default_enabled=True
    ),
    Stage(
        id='search',
        script='transcript_search.py',
        description='Build FTS5 search index',
        args=['--index'],
        default_enabled=True
    ),
    Stage(
        id='llm',
        script='extract_knowledge.py',
        description='Claude API knowledge extraction (costs $)',
        default_enabled=True,
        requires_api_key=True
    ),
    Stage(
        id='reports',
        script='generate_reports.py',
        description='Generate HTML reports',
        default_enabled=True
    ),
    Stage(
        id='gallery',
        script='style_code_gallery.py',
        description='Generate Midjourney sref gallery',
        default_enabled=True
    ),
    Stage(
        id='models',
        script='model_tracker.py',
        description='Generate AI model tracking report',
        args=['report'],
        default_enabled=True
    ),
    Stage(
        id='courses',
        script='course_materials.py',
        description='Generate course materials',
        default_enabled=True
    ),
    Stage(
        id='sync',
        script='sync_to_d_drive.py',
        description='Sync scripts and data to D: drive',
        default_enabled=True
    ),
]


class PipelineRunner:
    """Orchestrates the AI Knowledge Base pipeline."""

    def __init__(self, dry_run: bool = False, skip_llm: bool = False):
        self.dry_run = dry_run
        self.skip_llm = skip_llm
        self.results: Dict[str, StageResult] = {}
        self.start_time = None

    def get_stage(self, stage_id: str) -> Optional[Stage]:
        """Get a stage by ID."""
        for stage in STAGES:
            if stage.id == stage_id:
                return stage
        return None

    def run_stage(self, stage: Stage) -> StageResult:
        """Run a single pipeline stage."""
        script_path = SCRIPT_DIR / stage.script

        if not script_path.exists():
            return StageResult(
                stage_id=stage.id,
                status='failed',
                duration_seconds=0,
                errors=[f"Script not found: {stage.script}"]
            )

        # Build command
        cmd = [sys.executable, str(script_path)] + stage.args

        if self.dry_run:
            return StageResult(
                stage_id=stage.id,
                status='skipped',
                duration_seconds=0,
                output_summary=f"Would run: {' '.join(cmd)}"
            )

        # Run the script
        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(SCRIPT_DIR),
                timeout=600  # 10 minute timeout per stage
            )
            duration = time.time() - start

            # Parse output for summary
            output = result.stdout + result.stderr
            summary = self._extract_summary(output, stage.id)
            items = self._count_items(output, stage.id)

            if result.returncode == 0:
                return StageResult(
                    stage_id=stage.id,
                    status='success',
                    duration_seconds=duration,
                    items_processed=items,
                    output_summary=summary
                )
            else:
                return StageResult(
                    stage_id=stage.id,
                    status='partial' if 'error' in output.lower() else 'failed',
                    duration_seconds=duration,
                    items_processed=items,
                    errors=[result.stderr[:500] if result.stderr else "Unknown error"],
                    output_summary=summary
                )

        except subprocess.TimeoutExpired:
            return StageResult(
                stage_id=stage.id,
                status='failed',
                duration_seconds=600,
                errors=["Stage timed out after 10 minutes"]
            )
        except Exception as e:
            return StageResult(
                stage_id=stage.id,
                status='failed',
                duration_seconds=time.time() - start,
                errors=[str(e)]
            )

    def _extract_summary(self, output: str, stage_id: str) -> str:
        """Extract a summary line from script output."""
        lines = output.strip().split('\n')

        # Look for common summary patterns
        for line in reversed(lines[-20:]):
            line_lower = line.lower()
            if any(word in line_lower for word in ['processed', 'generated', 'created', 'saved', 'synced', 'indexed', 'organized']):
                return line.strip()[:100]

        # Return last non-empty line
        for line in reversed(lines):
            if line.strip():
                return line.strip()[:100]

        return "Completed"

    def _count_items(self, output: str, stage_id: str) -> int:
        """Try to extract item count from output."""
        import re

        # Look for common patterns
        patterns = [
            r'(\d+)\s*(?:items?|emails?|videos?|transcripts?|repos?|files?)',
            r'processed[:\s]*(\d+)',
            r'generated[:\s]*(\d+)',
            r'Total[:\s]*(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 0

    def run_pipeline(self, stages_to_run: Optional[List[str]] = None, from_stage: Optional[str] = None) -> Dict[str, StageResult]:
        """Run the full pipeline or selected stages."""
        self.start_time = time.time()
        self.results = {}

        # Determine which stages to run
        if stages_to_run:
            stage_list = [self.get_stage(s) for s in stages_to_run if self.get_stage(s)]
        elif from_stage:
            stage_ids = [s.id for s in STAGES]
            if from_stage in stage_ids:
                start_idx = stage_ids.index(from_stage)
                stage_list = STAGES[start_idx:]
            else:
                print(f"Unknown stage: {from_stage}")
                return {}
        else:
            stage_list = STAGES

        total = len(stage_list)
        enabled_count = sum(1 for s in stage_list if self._should_run_stage(s))

        print("=" * 80)
        print("AI KNOWLEDGE BASE PIPELINE")
        print("=" * 80)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"LLM Extraction: {'DISABLED (--skip-llm)' if self.skip_llm else 'ENABLED'}")
        print(f"Stages: {enabled_count} of {total} enabled")
        print()

        for i, stage in enumerate(stage_list, 1):
            if not self._should_run_stage(stage):
                print(f"[{i}/{total}] {stage.description}...")
                print(f"       SKIPPED (--skip-llm flag set)")
                self.results[stage.id] = StageResult(
                    stage_id=stage.id,
                    status='skipped',
                    duration_seconds=0,
                    output_summary="Skipped via --skip-llm"
                )
                print()
                continue

            print(f"[{i}/{total}] {stage.description}...")

            result = self.run_stage(stage)
            self.results[stage.id] = result

            if result.status == 'success':
                if result.items_processed > 0:
                    print(f"       -> {result.output_summary}")
                print(f"       Completed in {result.duration_seconds:.1f}s")
            elif result.status == 'skipped':
                print(f"       {result.output_summary}")
            elif result.status == 'partial':
                print(f"       -> {result.output_summary}")
                print(f"       PARTIAL - some errors occurred")
            else:
                print(f"       FAILED: {result.errors[0] if result.errors else 'Unknown error'}")

            print()

        self.print_summary()
        self.save_state()

        return self.results

    def _should_run_stage(self, stage: Stage) -> bool:
        """Check if a stage should run based on settings."""
        if stage.id == 'llm':
            return not self.skip_llm
        return stage.default_enabled

    def print_summary(self):
        """Print pipeline execution summary."""
        total_time = time.time() - self.start_time if self.start_time else 0

        completed = sum(1 for r in self.results.values() if r.status == 'success')
        skipped = sum(1 for r in self.results.values() if r.status == 'skipped')
        failed = sum(1 for r in self.results.values() if r.status in ('failed', 'partial'))
        total_items = sum(r.items_processed for r in self.results.values())

        print("=" * 80)
        print(f"PIPELINE COMPLETE - Total: {self._format_duration(total_time)}")
        print("=" * 80)
        print(f"  Stages: {completed} completed, {skipped} skipped, {failed} failed")
        if total_items > 0:
            print(f"  Items processed: {total_items}")
        print(f"  Reports: {KNOWLEDGE_BASE / 'exports'}")
        print("=" * 80)

        if failed > 0:
            print("\nErrors:")
            for stage_id, result in self.results.items():
                if result.status in ('failed', 'partial') and result.errors:
                    print(f"  [{stage_id}] {result.errors[0]}")

    def _format_duration(self, seconds: float) -> str:
        """Format duration as human-readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"

    def save_state(self):
        """Save pipeline state for resume capability."""
        state = {
            'last_run': datetime.now().isoformat(),
            'results': {
                stage_id: {
                    'status': r.status,
                    'duration': r.duration_seconds,
                    'items': r.items_processed
                }
                for stage_id, r in self.results.items()
            }
        }

        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)


def show_status():
    """Show current knowledge base status."""
    print("\n" + "=" * 80)
    print("AI KNOWLEDGE BASE STATUS")
    print("=" * 80)

    # Check if knowledge base exists
    if not KNOWLEDGE_BASE.exists():
        print(f"\nKnowledge base not found: {KNOWLEDGE_BASE}")
        print("Run the pipeline first to initialize.")
        return

    # Load master database
    if MASTER_DB.exists():
        with open(MASTER_DB, 'r', encoding='utf-8') as f:
            db = json.load(f)

        print(f"\nLast updated: {db.get('metadata', {}).get('last_updated', 'Unknown')}")

        # Count items
        github_count = len(db.get('repositories', {}).get('github', []))
        hf_count = len(db.get('repositories', {}).get('huggingface', []))
        tutorial_count = len(db.get('tutorials', []))
        sref_count = len(db.get('styles', {}).get('midjourney_sref', []))

        transcripts_with = sum(1 for t in db.get('tutorials', []) if t.get('has_transcript'))
        analyzed = sum(1 for t in db.get('tutorials', []) if t.get('analyzed'))

        print(f"\n--- Content Summary ---")
        print(f"  GitHub repos:      {github_count}")
        print(f"  HuggingFace:       {hf_count}")
        print(f"  YouTube tutorials: {tutorial_count}")
        print(f"    With transcripts: {transcripts_with}")
        print(f"    Analyzed:         {analyzed}")
        print(f"  Midjourney sref:   {sref_count}")
    else:
        print("\nMaster database not found. Run the pipeline to initialize.")

    # Check directories
    print(f"\n--- Directory Status ---")
    dirs_to_check = [
        ('Transcripts', KNOWLEDGE_BASE / 'tutorials' / 'transcripts'),
        ('Analysis', KNOWLEDGE_BASE / 'tutorials' / 'analysis'),
        ('Extracted', KNOWLEDGE_BASE / 'extracted'),
        ('Exports', KNOWLEDGE_BASE / 'exports'),
        ('Course Materials', KNOWLEDGE_BASE / 'course_materials'),
    ]

    for name, path in dirs_to_check:
        if path.exists():
            count = len(list(path.glob('*')))
            print(f"  {name}: {count} files")
        else:
            print(f"  {name}: [not created]")

    # Check search index
    search_db = KNOWLEDGE_BASE / 'tutorials' / 'search_index.db'
    if search_db.exists():
        size_kb = search_db.stat().st_size / 1024
        print(f"\n--- Search Index ---")
        print(f"  Size: {size_kb:.1f} KB")

    # Last pipeline run
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
        print(f"\n--- Last Pipeline Run ---")
        print(f"  {state.get('last_run', 'Unknown')}")


def list_stages():
    """List all available pipeline stages."""
    print("\n" + "=" * 60)
    print("AVAILABLE PIPELINE STAGES")
    print("=" * 60)
    print()
    print(f"{'#':<3} {'ID':<12} {'Script':<30} {'Default':<8}")
    print("-" * 60)

    for i, stage in enumerate(STAGES, 1):
        default = "ON" if stage.default_enabled else "OFF ($)"
        print(f"{i:<3} {stage.id:<12} {stage.script:<30} {default:<8}")
        print(f"    {stage.description}")
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='AI Knowledge Base Pipeline - Run all scripts in order',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python run_pipeline.py                          # Full pipeline (includes LLM)
  python run_pipeline.py --skip-llm               # Skip LLM extraction to save $
  python run_pipeline.py --stage reports          # Run single stage
  python run_pipeline.py --stages youtube,analyze # Run specific stages
  python run_pipeline.py --from youtube           # Run from stage onwards
  python run_pipeline.py --dry-run                # Preview what would run
  python run_pipeline.py --list-stages            # List available stages
  python run_pipeline.py status                   # Show KB status
        '''
    )

    parser.add_argument('command', nargs='?', default=None,
                       help='Command: status, or leave empty for full pipeline')
    parser.add_argument('--dry-run', '-n', action='store_true',
                       help='Preview what would run without executing')
    parser.add_argument('--skip-llm', action='store_true',
                       help='Skip LLM knowledge extraction to save $')
    parser.add_argument('--stage', '-s', type=str,
                       help='Run a single stage by ID')
    parser.add_argument('--stages', type=str,
                       help='Run specific stages (comma-separated)')
    parser.add_argument('--from', dest='from_stage', type=str,
                       help='Run from this stage onwards')
    parser.add_argument('--list-stages', '-l', action='store_true',
                       help='List all available stages')
    parser.add_argument('--api-key', type=str,
                       help='Anthropic API key for LLM extraction')

    args = parser.parse_args()

    # Handle commands and flags
    if args.command == 'status':
        show_status()
        return

    if args.list_stages:
        list_stages()
        return

    # Set API key if provided
    if args.api_key:
        os.environ['ANTHROPIC_API_KEY'] = args.api_key

    # Create runner
    runner = PipelineRunner(
        dry_run=args.dry_run,
        skip_llm=args.skip_llm
    )

    # Determine stages to run
    stages_to_run = None
    from_stage = None

    if args.stage:
        stages_to_run = [args.stage]
    elif args.stages:
        stages_to_run = [s.strip() for s in args.stages.split(',')]
    elif args.from_stage:
        from_stage = args.from_stage

    # Run pipeline
    runner.run_pipeline(stages_to_run=stages_to_run, from_stage=from_stage)


if __name__ == '__main__':
    main()
