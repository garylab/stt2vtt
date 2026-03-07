"""Convert fast-whisper STT results with timestamps to WebVTT."""

import json
from types import SimpleNamespace
from typing import Any, List, Union

STOP_CHARS = set(
    ".!?,:;…‥"
    "。！？，、；："
    "।"
    "܀።፧"
    "؟؛"
    "၊။"
    "⸮⁇⁈⁉"
)


def _seconds_to_vtt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    seconds = seconds % 3600
    minutes = int(seconds // 60)
    milliseconds = int(seconds * 1000) % 1000
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def _capitalize_text(text: str) -> str:
    text = text.strip()
    return text[0].upper() + text[1:] if text else text


def _end_with_stop_char(text: str) -> bool:
    if not text:
        return False
    return any(text.endswith(c) for c in STOP_CHARS)


def _normalize_fast_whisper(segments: List[Any]) -> List[SimpleNamespace]:
    """Normalize fast-whisper style segments to internal format."""
    out = []
    for seg in segments:
        words = []
        for w in seg.get("words", []):
            start = float(w.get("start", 0))
            end = float(w.get("end", 0))
            word = w.get("word", "")
            words.append(SimpleNamespace(start=start, end=end, word=word))
        start = float(seg.get("start", 0))
        end = float(seg.get("end", 0))
        if words and start == 0 and end == 0:
            start = words[0].start
            end = words[-1].end
        out.append(
            SimpleNamespace(
                start=start,
                end=end,
                text=seg.get("text", ""),
                words=words,
            )
        )
    return out


def _parse_and_normalize(data: Any) -> List[SimpleNamespace]:
    """Parse input and return normalized segments (fast-whisper format only)."""
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, dict) and "segments" in data:
        data = data["segments"]
    if not isinstance(data, list) or not data:
        raise ValueError("Expected a non-empty list of segments (fast-whisper format).")
    if not isinstance(data[0], dict):
        raise ValueError("Expected a list of segment objects with start, end, text, words.")
    return _normalize_fast_whisper(data)


def _segments_to_subtitle(segments: List[SimpleNamespace]) -> List[dict]:
    subtitles = []
    for segment in segments:
        words_idx = 0
        words_len = len(segment.words)
        seg_start = 0.0
        seg_end = 0.0
        seg_text = ""

        if segment.words:
            is_segmented = False
            for word in segment.words:
                if not is_segmented:
                    seg_start = word.start
                    is_segmented = True
                seg_end = word.end
                seg_text += word.word

                if _end_with_stop_char(word.word):
                    seg_text = seg_text[:-1]
                    if not seg_text:
                        continue
                    if seg_start < seg_end and seg_text.strip():
                        subtitles.append(
                            {"msg": seg_text, "start_time": seg_start, "end_time": seg_end}
                        )
                    is_segmented = False
                    seg_text = ""

                if words_idx == 0 and segment.start < word.start:
                    seg_start = word.start
                if words_idx == (words_len - 1) and segment.end > word.end:
                    seg_end = segment.end
                words_idx += 1

        if not seg_text:
            continue
        if seg_start < seg_end and seg_text.strip():
            subtitles.append(
                {"msg": seg_text, "start_time": seg_start, "end_time": seg_end}
            )
    return subtitles


def _format_vtt(subtitles: List[dict]) -> str:
    lines = []
    for sub in subtitles:
        msg = sub.get("msg")
        if not msg:
            continue
        start = sub.get("start_time", 0)
        end = sub.get("end_time", 0)
        start_str = _seconds_to_vtt_time(start)
        end_str = _seconds_to_vtt_time(end)
        text = _capitalize_text(msg)
        lines.append(f"{start_str} --> {end_str}\n{text}\n")
    return "WEBVTT\n\n" + "\n".join(lines)


def stt_to_vtt(stt_result: Union[str, bytes, list, dict]) -> str:
    """Convert fast-whisper STT result to WebVTT text.

    Args:
        stt_result: JSON string or parsed list of segments (fast-whisper format).

    Returns:
        WebVTT subtitle content as a string.
    """
    if isinstance(stt_result, bytes):
        stt_result = stt_result.decode("utf-8")
    segments = _parse_and_normalize(stt_result)
    subtitles = _segments_to_subtitle(segments)
    return _format_vtt(subtitles)
