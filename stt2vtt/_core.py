"""Convert fast-whisper STT results with timestamps to WebVTT."""

import json
from types import SimpleNamespace
from typing import Any, List, Union

from pydantic import ValidationError

from .schemas import Segment


def _validate_input(data: Any) -> List[Segment]:
    """Parse and validate input. Input must be a list of segments or a JSON string of that list.
    Raises ValueError if not a list; ValidationError if segment structure is invalid.
    """
    if isinstance(data, str):
        data = json.loads(data)
    if not isinstance(data, list):
        raise ValueError("Input must be a list of segments or a JSON string of that list.")
    if not data:
        raise ValueError("Input list must not be empty.")
    return [Segment.model_validate(seg) for seg in data]


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


def _end_with_stop_char(text: str) -> bool:
    if not text:
        return False
    return any(text.endswith(c) for c in STOP_CHARS)


def _segments_to_internal(segments: List[Segment]) -> List[SimpleNamespace]:
    """Convert validated Segment models to internal format."""
    out = []
    for seg in segments:
        words = [
            SimpleNamespace(start=w.start, end=w.end, word=w.word)
            for w in seg.words
        ]
        start = seg.start
        end = seg.end
        if words and start == 0 and end == 0:
            start = words[0].start
            end = words[-1].end
        out.append(
            SimpleNamespace(
                start=start,
                end=end,
                text=seg.text,
                words=words,
            )
        )
    return out


def _segments_to_subtitle(segments: List[SimpleNamespace]) -> List[dict]:
    subtitles = []
    for segment in segments:
        # No word-level timestamps: use segment start/end and text as one cue
        if not segment.words:
            text = (segment.text or "").strip()
            if text and segment.start < segment.end:
                subtitles.append(
                    {"msg": text, "start_time": segment.start, "end_time": segment.end}
                )
            continue

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
                    # Break at punctuation for short lines; strip punctuation from output
                    seg_text = seg_text[:-1]
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
        text = msg.strip()
        lines.append(f"{start_str} --> {end_str}\n{text}\n")
    return "WEBVTT\n\n" + "\n".join(lines)


def stt_to_vtt(stt_result: Union[str, bytes, list, dict]) -> str:
    """Convert fast-whisper STT result to WebVTT text.

    Input must be a list of segments or a JSON string of that list (see tests/test_data/jp2-input.json).
    Raises ValueError if input is not a list; pydantic.ValidationError if segment structure is invalid.

    Args:
        stt_result: List of segments, or JSON string of that list (fast-whisper format).

    Returns:
        WebVTT subtitle content as a string.
    """
    if isinstance(stt_result, bytes):
        stt_result = stt_result.decode("utf-8")
    segments = _validate_input(stt_result)
    internal = _segments_to_internal(segments)
    subtitles = _segments_to_subtitle(internal)
    return _format_vtt(subtitles)
