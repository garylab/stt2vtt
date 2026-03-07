"""Convert STT (speech-to-text) results with timestamps to WebVTT.

Supports input from Azure Speech-to-Text or fast-whisper style JSON.
"""

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


def _normalize_azure(data: Any) -> List[SimpleNamespace]:
    """Normalize Azure Speech-to-Text result to internal format."""
    phrases = data.get("phrases") or data.get("recognizedPhrases") or []
    if not phrases and isinstance(data, list):
        phrases = data
    out = []
    for p in phrases:
        words = []
        for w in p.get("words", []):
            offset_ms = w.get("offsetMilliseconds", w.get("offset", 0))
            duration_ms = w.get("durationMilliseconds", w.get("duration", 0))
            start = offset_ms / 1000.0
            end = start + duration_ms / 1000.0
            word = w.get("text", w.get("word", ""))
            words.append(SimpleNamespace(start=start, end=end, word=word))
        offset_ms = p.get("offsetMilliseconds", p.get("offset", 0))
        duration_ms = p.get("durationMilliseconds", p.get("duration", 0))
        start = offset_ms / 1000.0
        end = start + duration_ms / 1000.0
        if words and (duration_ms == 0 or end <= start):
            start = words[0].start
            end = words[-1].end
        out.append(
            SimpleNamespace(
                start=start,
                end=end,
                text=p.get("text", p.get("display", "")),
                words=words,
            )
        )
    return out


def _detect_and_normalize(data: Any) -> List[SimpleNamespace]:
    """Detect input format and return normalized segments."""
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        seg = data[0]
        if "words" in seg and seg["words"]:
            w = seg["words"][0]
            if "start" in w and "end" in w and "word" in w:
                return _normalize_fast_whisper(data)
        if "offsetMilliseconds" in seg or "offset" in seg:
            return _normalize_azure(data)
        return _normalize_fast_whisper(data)
    if isinstance(data, dict):
        if "phrases" in data or "recognizedPhrases" in data:
            return _normalize_azure(data)
        if "segments" in data:
            return _detect_and_normalize(data["segments"])
    raise ValueError("Unsupported STT result format: expected list of segments or Azure-style dict with 'phrases'.")


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
    """Convert STT result (Azure or fast-whisper style) to WebVTT text.

    Args:
        stt_result: JSON string, parsed list of segments, or Azure-style dict.

    Returns:
        WebVTT subtitle content as a string.
    """
    if isinstance(stt_result, bytes):
        stt_result = stt_result.decode("utf-8")
    segments = _detect_and_normalize(stt_result)
    subtitles = _segments_to_subtitle(segments)
    return _format_vtt(subtitles)
