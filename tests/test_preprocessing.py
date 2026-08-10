"""
Unit tests for TranscriptPreprocessor in app/preprocessing.py.
"""

import pytest
from app.preprocessing import TranscriptPreprocessor


def test_remove_timestamps():
    preprocessor = TranscriptPreprocessor()
    text = "[00:12:34] Rahul: Let's discuss session caching at 12:34 PM."
    cleaned = preprocessor.remove_timestamps(text)
    assert "[00:12:34]" not in cleaned
    assert "12:34 PM" not in cleaned
    assert "Rahul: Let's discuss session caching at ." in cleaned or "Rahul: Let's discuss session caching at" in cleaned


def test_remove_filler_words():
    preprocessor = TranscriptPreprocessor()
    text = "Um, basically, we should, like, migrate to Redis, you know?"
    cleaned = preprocessor.remove_filler_words(text)
    assert "Um" not in cleaned
    assert "basically" not in cleaned
    assert "like" not in cleaned
    assert "you know" not in cleaned
    assert "migrate to Redis" in cleaned


def test_clean_speaker_labels():
    preprocessor = TranscriptPreprocessor()
    text = "  Rahul (Backend Lead):    We need Redis.\n  Amit (DevOps Lead):Agree.  "
    cleaned = preprocessor.clean_speaker_labels(text)
    lines = cleaned.splitlines()
    assert lines[0] == "Rahul (Backend Lead): We need Redis."
    assert lines[1] == "Amit (DevOps Lead): Agree."


def test_full_preprocessing_pipeline():
    preprocessor = TranscriptPreprocessor()
    raw = "[00:01:15] Rahul (Backend Lead): Um, basically, we need to upgrade Helm charts."
    cleaned, stats = preprocessor.preprocess(raw)
    assert "[00:01:15]" not in cleaned
    assert "basically" not in cleaned
    assert "Rahul (Backend Lead):" in cleaned
    assert stats["original_char_count"] == len(raw)
    assert stats["cleaned_char_count"] < stats["original_char_count"]
