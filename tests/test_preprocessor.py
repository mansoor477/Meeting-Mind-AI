"""
Unit tests for Meeting Mind AI Preprocessor.
"""

from meeting_mind.preprocessor import Preprocessor


def test_strip_timestamps():
    preprocessor = Preprocessor()
    raw = "[00:12:34] Rahul: Let's discuss Redis caching.\n(10:15) Priya: Sounds good."
    cleaned, count = preprocessor.strip_timestamps(raw)
    assert count == 2
    assert "[00:12:34]" not in cleaned
    assert "(10:15)" not in cleaned
    assert "Rahul: Let's discuss Redis caching." in cleaned


def test_clean_filler_words():
    preprocessor = Preprocessor()
    raw = "Um, Rahul: So uh, you know, we should sort of implement JWT refresh tokens, I mean."
    cleaned, count = preprocessor.clean_filler_words(raw)
    assert count >= 3
    assert "Um," not in cleaned
    assert "uh," not in cleaned
    assert "you know," not in cleaned


def test_speaker_disambiguation():
    preprocessor = Preprocessor()
    raw = "Speaker 1: Hi everyone, I'm Rahul, Backend Lead.\nSpeaker 2: Hey Rahul! Priya here from Product."
    cleaned, mapped = preprocessor.disambiguate_speakers(raw)
    assert "Rahul (Backend Lead)" in mapped.values() or "Rahul" in str(mapped)
    assert "Rahul" in cleaned
    assert "Priya" in cleaned


def test_full_preprocessing_pipeline():
    preprocessor = Preprocessor()
    raw = "[00:01:15] Speaker 1: Um, I'm Rahul (Backend Lead). Let me explain the Redis plan."
    res = preprocessor.process(raw)
    assert res["timestamps_removed"] == 1
    assert res["fillers_removed"] >= 1
    assert "cleaned_transcript" in res
    assert "[00:01:15]" not in res["cleaned_transcript"]
