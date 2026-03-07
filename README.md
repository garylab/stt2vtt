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

### fast-whisper

A JSON array of segments. Each segment has `start`, `end`, `text` (seconds), and `words`: list of `{start, end, word}`. Optional: `id`, `probability` on words.

```json
[
  {
    "id": 1,
    "start": 0.0,
    "end": 1.5,
    "text": " Hello world.",
    "words": [
      { "start": 0.0, "end": 0.5, "word": " Hello" },
      { "start": 0.5, "end": 1.5, "word": " world." }
    ]
  }
]
```

### Azure Speech-to-Text

A JSON object with `phrases` (or `recognizedPhrases`). Each phrase has `text`, `offsetMilliseconds`, `durationMilliseconds`, and `words` with `text`, `offsetMilliseconds`, `durationMilliseconds`.

```json
{
  "phrases": [
    {
      "text": "Hello world.",
      "offsetMilliseconds": 0,
      "durationMilliseconds": 1500,
      "words": [
        { "text": "Hello", "offsetMilliseconds": 0, "durationMilliseconds": 500 },
        { "text": " world.", "offsetMilliseconds": 500, "durationMilliseconds": 1000 }
      ]
    }
  ]
}
```

## Output

WebVTT subtitle content: a `WEBVTT` header plus timestamped cues. Sentence boundaries are split on punctuation; the first letter of each cue is capitalized.

Example (from the fast-whisper or Azure input examples above):

```
WEBVTT

00:00:00.000 --> 00:00:01.500
Hello world
```

## License

MIT — see [LICENSE](LICENSE).
