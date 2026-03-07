#!/usr/bin/env python3
"""Command-line interface: read STT JSON, write VTT."""

import sys
import argparse
from pathlib import Path

from .stt_to_vtt import stt_to_vtt

__version__ = "0.1.0"


def main():
    parser = argparse.ArgumentParser(
        description="Convert fast-whisper STT result JSON to WebVTT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  stt2vtt result.json              # writes result.vtt in current dir
  stt2vtt /path/to/result.json     # writes result.vtt in current dir
  stt2vtt result.json -o out.vtt  # writes out.vtt
  cat result.json | stt2vtt -o output.vtt
        """,
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=str,
        default=None,
        help="Input JSON file (STT result). Omit to read from stdin.",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output VTT file (default: <input_stem>.vtt in current dir when input is a file, else stdout)",
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress messages",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args()

    try:
        if args.input:
            path = Path(args.input)
            if not path.exists():
                print(f"Error: Input file not found: {args.input}", file=sys.stderr)
                sys.exit(1)
            if not path.is_file():
                print(f"Error: Not a file: {args.input}", file=sys.stderr)
                sys.exit(1)
            content = path.read_text(encoding="utf-8")
        else:
            content = sys.stdin.read()

        vtt = stt_to_vtt(content)

        if args.output:
            out_path = Path(args.output)
        elif args.input:
            # Input from file: save as <stem>.vtt in current dir
            out_path = Path.cwd() / f"{Path(args.input).stem}.vtt"
        else:
            out_path = None

        if out_path is not None:
            out_path.write_text(vtt, encoding="utf-8")
            if not args.quiet:
                print(f"Written: {out_path}", file=sys.stderr)
        else:
            print(vtt)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if not args.quiet:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
