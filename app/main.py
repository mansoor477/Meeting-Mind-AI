"""
Main CLI Entry point for Meeting Mind AI.
Orchestrates: Preprocessing -> Azure OpenAI Extraction -> Pydantic Validation -> JSON/Markdown Export.
"""

import argparse
import sys
from pathlib import Path
from app.config import get_config
from app.preprocessing import TranscriptPreprocessor
from app.azure_engine import AzureOpenAIEngine
from app.exporters import JSONExporter, MarkdownExporter


def run_pipeline(input_path: str, json_output: str, md_output: str) -> None:
    """Run full meeting intelligence pipeline."""
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"Error: Input file '{input_path}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Reading transcript from: {input_path}")
    raw_text = input_file.read_text(encoding="utf-8")

    print("Preprocessing transcript...")
    preprocessor = TranscriptPreprocessor()
    cleaned_text, stats = preprocessor.preprocess(raw_text)
    print(f"Transcript cleaned ({stats['original_char_count']} chars -> {stats['cleaned_char_count']} chars)")

    print("Extracting intelligence using Azure OpenAI...")
    engine = AzureOpenAIEngine(get_config())
    result = engine.extract(cleaned_text)

    print(f"Exporting JSON to: {json_output}")
    JSONExporter.export(result, json_output)

    print(f"Exporting Markdown Digest to: {md_output}")
    MarkdownExporter.export(result, md_output)

    print("\nMeeting Mind AI Pipeline Executed Successfully!")


def main():
    parser = argparse.ArgumentParser(description="Meeting Mind AI - Decision Intelligence Engine")
    parser.add_argument(
        "--input",
        "-i",
        default="input/meeting_transcript.txt",
        help="Path to input meeting transcript text file (default: input/meeting_transcript.txt)"
    )
    parser.add_argument(
        "--json-output",
        default="output/meeting_result.json",
        help="Path for generated JSON output (default: output/meeting_result.json)"
    )
    parser.add_argument(
        "--md-output",
        default="output/meeting_digest.md",
        help="Path for generated Markdown digest (default: output/meeting_digest.md)"
    )

    args = parser.parse_args()
    run_pipeline(args.input, args.json_output, args.md_output)


if __name__ == "__main__":
    main()
