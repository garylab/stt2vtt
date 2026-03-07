# stt2vtt

Convert **fast-whisper** STT results with timestamps to WebVTT. Input is a list of segments (or a JSON string of that list) from [faster-whisper](https://github.com/SYSTRAN/faster-whisper) or compatible segment + word timestamps. Output is VTT text.

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
# From file (writes <stem>.vtt in current directory by default)
stt2vtt result.json
# → result.vtt

# Custom output path
stt2vtt result.json -o output.vtt

# From stdin
cat result.json | stt2vtt -o output.vtt
```

### Python

```python
import stt2vtt

# Call the package: list of segments, or JSON string of that list (fast-whisper format)
vtt = stt2vtt('[{"start": 0, "end": 1.5, "text": " Hello world.", "words": [{"start": 0, "end": 0.5, "word": " Hello"}, {"start": 0.5, "end": 1.5, "word": " world."}]}]')

print(vtt)  # "WEBVTT\n\n00:00:00.000 --> ..."
```

## Input format (fast-whisper)

Input must be a **list** of segments or a **JSON string** of that list (no wrapper object).

Minimal schema:

- **Segment**: `start`, `end` (seconds), `text`, `words` (list, default `[]`).
- **Word** (each item in `words`): `start`, `end`, `word`.

Extra fields in the JSON are ignored. See [tests/test_data/jp2-input.json](tests/test_data/jp2-input.json) for the formal format.

Example:

```json
[
  {
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

Segments without `words` are allowed; one VTT cue is emitted per segment using segment `start`, `end`, and `text`.

## Output

WebVTT subtitle content: a `WEBVTT` header plus timestamped cues. Sentence boundaries are split on punctuation; the first letter of each cue is capitalized.

Example (from the input above):

```
WEBVTT

00:00:00.000 --> 00:00:01.500
Hello world
```

## License

MIT — see [LICENSE](LICENSE).
