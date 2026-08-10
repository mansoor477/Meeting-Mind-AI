"""
Preprocessor module for Meeting Mind AI.
Strips timestamps, removes conversational filler words, and resolves generic speaker tags.
"""

import re
from typing import Dict, List, Optional, Tuple


DEFAULT_FILLER_WORDS = [
    r"\bum\b", r"\buh\b", r"\ber\b", r"\bah\b",
    r"\byou know\b", r"\bkind of\b", r"\bsort of\b",
    r"\bi mean\b", r"\bllike\b" # handled carefully to avoid stripping 'like' in context
]

# Patterns for timestamp extraction
TIMESTAMP_PATTERNS = [
    r"\[\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?\]",   # [00:12:34] or [12:34] or [00:12:34.123]
    r"\(\d{1,2}:\d{2}(?::\d{2})?\)",             # (00:12:34) or (12:34)
    r"\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\s*[-–—]\s*", # 10:15 AM -
    r"^\d{1,2}:\d{2}\s+"                         # 00:12  at start of line
]

# Known default speaker disambiguation hints if present in transcript text
COMMON_NAME_ROLE_PATTERNS = [
    (r"Rahul", "Rahul (Backend Lead)"),
    (r"Priya", "Priya (Product Manager)"),
    (r"Alex", "Alex (DevOps Lead)"),
    (r"Sneha", "Sneha (Frontend Engineer)"),
    (r"David", "David (QA Lead)"),
    (r"Vikram", "Vikram (Engineering Manager)"),
    (r"Sarah", "Sarah (Security Architect)")
]


class Preprocessor:
    def __init__(
        self,
        strip_timestamps_enabled: bool = True,
        clean_fillers_enabled: bool = True,
        custom_speaker_map: Optional[Dict[str, str]] = None
    ):
        self.strip_timestamps_enabled = strip_timestamps_enabled
        self.clean_fillers_enabled = clean_fillers_enabled
        self.custom_speaker_map = custom_speaker_map or {}

    def strip_timestamps(self, text: str) -> Tuple[str, int]:
        """Strips timestamp annotations from transcript lines."""
        count = 0
        cleaned_text = text
        for pattern in TIMESTAMP_PATTERNS:
            matches = len(re.findall(pattern, cleaned_text, flags=re.MULTILINE))
            count += matches
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.MULTILINE)
        
        # Clean up any residual double spaces or empty line artifacts
        cleaned_lines = []
        for line in cleaned_text.splitlines():
            line_str = re.sub(r"^[ \t]+", "", line)
            cleaned_lines.append(line_str)
        return "\n".join(cleaned_lines), count

    def clean_filler_words(self, text: str) -> Tuple[str, int]:
        """
        Strips common conversational filler words ('um', 'uh', 'you know', 'sort of', etc.)
        while keeping sentence structure intact.
        """
        count = 0
        cleaned_text = text
        
        # Specific filler phrases
        fillers = [
            (r"\b[Uu]m,?\s*", ""),
            (r"\b[Uu]h,?\s*", ""),
            (r"\b[Aa]h,?\s*", ""),
            (r"\b[Ee]r,?\s*", ""),
            (r",?\s*\byou know,?\s*", " "),
            (r",?\s*\bsort of\b", ""),
            (r",?\s*\bkind of\b", ""),
            (r"\b[Ii] mean,?\s*", ""),
            (r"\b[Lld]ike,?\s+(?=[a-z])", "") # filler 'like,' or 'like' before word
        ]

        for pattern, repl in fillers:
            matches = len(re.findall(pattern, cleaned_text))
            count += matches
            cleaned_text = re.sub(pattern, repl, cleaned_text)

        # Normalize multiple spaces
        cleaned_text = re.sub(r"[ \t]{2,}", " ", cleaned_text)
        return cleaned_text, count

    def infer_speaker_mappings(self, text: str) -> Dict[str, str]:
        """
        Scans raw text to infer who 'Speaker 1', 'Speaker 2', 'Speaker A' might be
        based on self-introductions or contextual references.
        e.g., 'Speaker 1: Hi everyone, I'm Rahul, Backend Lead.'
        """
        inferred = dict(self.custom_speaker_map)

        # Look for explicit introductions: Speaker 1: Hi, Rahul here... / I'm Rahul (Backend Lead)
        generic_speakers = set(re.findall(r"^(Speaker\s+\d+|Speaker\s+[A-Z]|Person\s+\d+):", text, flags=re.MULTILINE))

        for speaker in generic_speakers:
            if speaker in inferred:
                continue
            
            # Find lines spoken by this generic speaker
            lines = re.findall(rf"^{re.escape(speaker)}:(.*)$", text, flags=re.MULTILINE)
            speech = " ".join(lines)
            
            # Check for self-introductions or name mentions
            # e.g., "I'm Rahul, Backend Lead", "Sneha here!", "Alex from DevOps here", "This is David", "representing Frontend"
            intro_match = re.search(
                r"(?:I'm|I am|This is|My name is|here's|([A-Z][a-z]+)\s+here|([A-Z][a-z]+)\s+from\s+([A-Za-z\s]+)|([A-Z][a-z]+)\s+(?:speaking|representing))\s+([A-Z][a-z]+)?(?:\s*,?\s*([A-Za-z\s]+ Lead|Product Manager|Manager|Engineer|Architect))?",
                speech,
                re.IGNORECASE
            )
            
            found_name = None
            found_role = None

            # 1. Try explicit regex intro matching
            if intro_match:
                # Check groups from regex
                for g in [intro_match.group(1), intro_match.group(2), intro_match.group(4), intro_match.group(5)]:
                    if g and g.capitalize() not in ["Here", "From", "This", "Good", "Hey", "Hi", "Also", "The"]:
                        found_name = g.capitalize()
                        break

            # 2. If name not found yet, check common name role patterns in speech
            if not found_name:
                for pattern, full_spec in COMMON_NAME_ROLE_PATTERNS:
                    if re.search(rf"\b{pattern}\b", speech, re.IGNORECASE):
                        inferred[speaker] = full_spec
                        break

            if speaker in inferred:
                continue

            # 3. If found name, look up role or pattern
            if found_name:
                for pattern, full_spec in COMMON_NAME_ROLE_PATTERNS:
                    if re.search(rf"\b{pattern}\b", found_name, re.IGNORECASE):
                        inferred[speaker] = full_spec
                        break
                if speaker not in inferred:
                    inferred[speaker] = found_name

        return inferred

    def disambiguate_speakers(self, text: str, speaker_map: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, str]]:
        """
        Replaces generic speaker tags with resolved names & roles.
        """
        active_map = self.infer_speaker_mappings(text)
        if speaker_map:
            active_map.update(speaker_map)

        cleaned_text = text
        for generic_tag, resolved_name in active_map.items():
            pattern = rf"^{re.escape(generic_tag)}:"
            cleaned_text = re.sub(pattern, f"{resolved_name}:", cleaned_text, flags=re.MULTILINE)
        
        return cleaned_text, active_map

    def process(self, raw_transcript: str, speaker_map: Optional[Dict[str, str]] = None) -> Dict:
        """
        Executes full preprocessing pipeline.
        Returns a dict containing:
        - 'cleaned_transcript': The preprocessed text
        - 'timestamps_removed': Count of timestamps stripped
        - 'fillers_removed': Count of filler words stripped
        - 'speaker_mappings': Dict of generic tags -> resolved identities
        """
        working_text = raw_transcript
        ts_count = 0
        filler_count = 0

        if self.strip_timestamps_enabled:
            working_text, ts_count = self.strip_timestamps(working_text)

        if self.clean_fillers_enabled:
            working_text, filler_count = self.clean_filler_words(working_text)

        working_text, resolved_speakers = self.disambiguate_speakers(working_text, speaker_map)

        return {
            "cleaned_transcript": working_text.strip(),
            "timestamps_removed": ts_count,
            "fillers_removed": filler_count,
            "speaker_mappings": resolved_speakers
        }
