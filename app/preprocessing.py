"""
Transcript Preprocessor module.
Cleans raw meeting transcripts by stripping timestamps, removing filler words,
standardizing speaker headers, and normalizing formatting.
"""

import re
from typing import Dict, List, Tuple


class TranscriptPreprocessor:
    """Preprocesses raw transcript text for LLM intelligence extraction."""

    # Timestamp patterns: [00:12:34], [12:34], (00:12:34), 12:34:56, 12:34 PM
    TIMESTAMP_PATTERNS: List[re.Pattern] = [
        re.compile(r"\[?\b\d{1,2}:\d{2}(?::\d{2})?\b\]?"),
        re.compile(r"\(\b\d{1,2}:\d{2}(?::\d{2})?\b\)"),
        re.compile(r"\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)\b"),
    ]

    # Filler words regex pattern (case-insensitive word boundaries)
    FILLER_WORDS: List[str] = [
        r"\bum\b",
        r"\buh\b",
        r"\blike\b",
        r"\byou know\b",
        r"\bbasically\b",
        r"\bsort of\b",
        r"\bkind of\b",
        r"\bi mean\b",
    ]

    def __init__(self, remove_timestamps: bool = True, remove_fillers: bool = True):
        self.remove_timestamps_flag = remove_timestamps
        self.remove_fillers_flag = remove_fillers
        self._filler_regex = re.compile(
            "|".join(self.FILLER_WORDS), re.IGNORECASE
        )

    def remove_timestamps(self, text: str) -> str:
        """Strip timestamp annotations from transcript."""
        cleaned = text
        for pattern in self.TIMESTAMP_PATTERNS:
            cleaned = pattern.sub("", cleaned)
        return cleaned

    def remove_filler_words(self, text: str) -> str:
        """Strip common verbal filler words."""
        cleaned = self._filler_regex.sub("", text)
        # Clean up multiple spaces left behind
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        # Clean up space before punctuation
        cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
        return cleaned

    def clean_speaker_labels(self, text: str) -> str:
        """Normalize speaker labels (e.g. 'Rahul (Backend Lead):')."""
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            # Standardize colon spacing after speaker labels
            line = re.sub(r"^([A-Za-z0-9\s()._-]+):\s*", r"\1: ", line)
            lines.append(line)
        return "\n".join(lines)

    def preprocess(self, raw_text: str) -> Tuple[str, Dict[str, int]]:
        """
        Full preprocessing pipeline.
        Returns clean text and metadata statistics.
        """
        raw_char_count = len(raw_text)
        cleaned = raw_text

        if self.remove_timestamps_flag:
            cleaned = self.remove_timestamps(cleaned)

        if self.remove_fillers_flag:
            cleaned = self.remove_filler_words(cleaned)

        cleaned = self.clean_speaker_labels(cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        stats = {
            "original_char_count": raw_char_count,
            "cleaned_char_count": len(cleaned),
            "lines_processed": len(cleaned.splitlines()),
        }

        return cleaned, stats
