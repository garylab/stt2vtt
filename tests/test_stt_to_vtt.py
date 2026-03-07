"""Tests for STT to VTT conversion."""

import pytest
from pathlib import Path

from pydantic import ValidationError

from src.stt_to_vtt import stt_to_vtt, STOP_CHARS, _seconds_to_vtt_time, _end_with_stop_char

FILES_DIR = Path(__file__).parent / "test_data"


def _discover_input_expected_pairs():
    """Find all *-input.json under tests/test_data and pair with *-expected.vtt."""
    pairs = []
    ids = []
    for input_path in sorted(FILES_DIR.rglob("*-input.json")):
        stem = input_path.name.replace("-input.json", "")
        expected_path = input_path.parent / f"{stem}-expected.vtt"
        if expected_path.exists():
            pairs.append((input_path, expected_path))
            ids.append(f"{input_path.parent.name}/{stem}")
    return pairs, ids


_pairs, _ids = _discover_input_expected_pairs()


@pytest.mark.parametrize("input_path,expected_path", _pairs, ids=_ids)
def test_file_input_matches_expected(input_path, expected_path):
    """Convert each *-input.json and assert output equals *-expected.vtt."""
    raw = input_path.read_text(encoding="utf-8")
    vtt = stt_to_vtt(raw)
    expected = expected_path.read_text(encoding="utf-8")
    assert vtt.rstrip() == expected.rstrip(), f"{input_path.name} -> output differs from {expected_path.name}"


def test_stop_chars_defined():
    assert isinstance(STOP_CHARS, set)
    assert "." in STOP_CHARS
    assert "!" in STOP_CHARS
    assert "?" in STOP_CHARS


def test_seconds_to_vtt_time():
    assert _seconds_to_vtt_time(0) == "00:00:00.000"
    assert _seconds_to_vtt_time(1.5) == "00:00:01.500"
    assert _seconds_to_vtt_time(60) == "00:01:00.000"
    assert _seconds_to_vtt_time(3661.123) == "01:01:01.123"


def test_end_with_stop_char():
    assert _end_with_stop_char("hello.") is True
    assert _end_with_stop_char("hello") is False
    assert _end_with_stop_char("") is False


def test_fast_whisper_minimal():
    """Minimal fast-whisper style input."""
    data = [
        {
            "id": 1,
            "start": 0.0,
            "end": 1.0,
            "text": "Hello world.",
            "words": [
                {"start": 0.0, "end": 0.5, "word": "Hello", "probability": 0.99},
                {"start": 0.5, "end": 1.0, "word": " world.", "probability": 0.99},
            ],
        }
    ]
    vtt = stt_to_vtt(data)
    assert vtt.startswith("WEBVTT\n\n")
    assert "00:00:00.000 --> 00:00:01.000" in vtt
    assert "Hello world" in vtt


def test_fast_whisper_json_string():
    """Accept JSON string."""
    data = '[{"id":1,"start":0,"end":1,"text":"Hi.","words":[{"start":0,"end":1,"word":"Hi.","probability":0.9}]}]'
    vtt = stt_to_vtt(data)
    assert "WEBVTT" in vtt
    assert "00:00:00.000 --> 00:00:01.000" in vtt
    assert "Hi" in vtt


def test_unsupported_format_raises():
    with pytest.raises(ValueError, match="Input must be a list"):
        stt_to_vtt({"foo": "bar"})


def test_invalid_segment_raises_validation_error():
    """Invalid segment structure (missing required field) raises ValidationError."""
    # Missing required "start" and "end" on segment
    data = [{"id": 1, "text": "Hello"}]
    with pytest.raises(ValidationError):
        stt_to_vtt(data)
