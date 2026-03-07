# stt2vtt

Convert STT (speech-to-text) results with timestamps to WebVTT. Input can be JSON from **Azure Speech-to-Text** or **fast-whisper** (or compatible segment + word timestamps). Output is VTT text.

No audio processing or ML models — this repo only converts existing STT JSON to VTT.

## Installation

```bash
pip install stt2vtt
```

Dev dependencies:

```bash
pip install stt2vtt[dev]
```

## Usage

### CLI

```bash
# From file
stt2vtt result.json -o output.vtt

# To stdout
stt2vtt result.json

# From stdin
cat result.json | stt2vtt -o output.vtt
```

### Python

```python
from src.stt_to_vtt import stt_to_vtt

# JSON string or parsed list/dict
vtt = stt_to_vtt('{"phrases": [...]}')   # Azure style
vtt = stt_to_vtt([{"id": 1, "start": 0, "end": 1, "text": "...", "words": [...]}])  # fast-whisper style

print(vtt)  # "WEBVTT\n\n00:00:00.000 --> ..."
```

## Input formats

- **fast-whisper**: List of segments, each with `start`, `end`, `text`, and `words` (list of `{start, end, word}`).
- **Azure**: Object with `phrases` (or `recognizedPhrases`), each phrase with `offsetMilliseconds`, `durationMilliseconds`, and `words` with `text`, `offsetMilliseconds`, `durationMilliseconds`.

## Output

WebVTT subtitle content: `WEBVTT` header plus timestamped cues with capitalized text.

## License

MIT — see [LICENSE](LICENSE).
