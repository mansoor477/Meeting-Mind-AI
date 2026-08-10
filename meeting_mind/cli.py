"""
Command Line Interface (CLI) for Meeting Mind AI.
"""

import argparse
import sys
import os
from pathlib import Path

# Ensure UTF-8 stdout handling for Windows terminals with emoji indicators
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from meeting_mind.preprocessor import Preprocessor
from meeting_mind.engine import MeetingMindEngine
from meeting_mind.exporters import JSONExporter, MarkdownExporter


def main():
    parser = argparse.ArgumentParser(
        description="Meeting Mind AI: Transcript-to-Action Item & Decision Intelligence Engine"
    )
    parser.add_argument("input_file", help="Path to raw meeting transcript text file (.txt)")
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Directory where output JSON and Markdown digests will be saved (default: ./output)"
    )
    parser.add_argument(
        "-f", "--format",
        choices=["json", "md", "all"],
        default="all",
        help="Output format to generate (default: all)"
    )
    parser.add_argument(
        "-p", "--provider",
        choices=["auto", "azure_openai", "anthropic", "mock"],
        default="auto",
        help="LLM Engine provider choice (default: auto)"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Disable pre-processing (timestamp stripping and filler word removal)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force offline mock provider engine for local testing"
    )
    parser.add_argument(
        "--model",
        default="claude-3-5-sonnet-20241022",
        help="Model string (default: claude-3-5-sonnet-20241022)"
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ Error: Input file '{args.input_file}' not found.")
        sys.exit(1)

    print(f"📖 Reading raw transcript from: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Step 1: Pre-processing
    if not args.no_clean:
        print("🧹 Pre-processing transcript (stripping timestamps, filler words, resolving speakers)...")
        preprocessor = Preprocessor()
        pre_result = preprocessor.process(raw_text)
        cleaned_text = pre_result["cleaned_transcript"]
        print(f"   ✓ Timestamps removed: {pre_result['timestamps_removed']}")
        print(f"   ✓ Filler words removed: {pre_result['fillers_removed']}")
        print(f"   ✓ Identified speakers: {list(pre_result['speaker_mappings'].values()) or 'None'}")
    else:
        print("⏩ Skipping pre-processing step (--no-clean flag passed)")
        cleaned_text = raw_text

    # Step 2: Extraction via Engine
    provider_name = "mock" if args.mock else args.provider
    print(f"🧠 Running Meeting Mind Intelligence Engine (Provider: {provider_name})...")
    engine = MeetingMindEngine(provider=provider_name, model=args.model, force_mock=args.mock)
    intelligence_output = engine.process_transcript(cleaned_text)

    print(f"\n✅ Intelligence Extraction Complete! (Active Provider: {engine.active_provider})")
    print(f"   - Title: {intelligence_output.meeting_title}")
    print(f"   - Executive Summary Takeaways: {len(intelligence_output.summary.key_takeaways)}")
    print(f"   - Action Items Extracted: {len(intelligence_output.action_items)}")
    print(f"   - Architecture Decisions Logged: {len(intelligence_output.decisions)}")
    print(f"   - Project Risks Identified: {len(intelligence_output.risks)}")

    # Step 3: Exporting Outputs
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = input_path.stem

    if args.format in ["json", "all"]:
        json_file = output_dir / f"{base_name}_intelligence.json"
        JSONExporter.export_file(intelligence_output, str(json_file))
        print(f"💾 Exported Schema JSON -> {json_file}")

    if args.format in ["md", "all"]:
        md_file = output_dir / f"{base_name}_digest.md"
        MarkdownExporter.export_file(intelligence_output, str(md_file))
        print(f"📝 Exported Markdown Digest -> {md_file}")

    print("\n🎉 Process finished successfully!")


if __name__ == "__main__":
    main()
