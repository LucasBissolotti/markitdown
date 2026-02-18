#!/usr/bin/env python3
"""Batch convert files to Markdown using MarkItDown.

Usage examples:
  python scripts/batch_convert.py --input packages/markitdown/tests/test_files --output converted/batch_demo --recursive
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from markitdown import MarkItDown
from markitdown._exceptions import FileConversionException


def iter_files(root: Path, extensions: list[str] | None, recursive: bool):
    if recursive:
        it = root.rglob("*")
    else:
        it = root.iterdir()
    for p in it:
        if not p.is_file():
            continue
        if extensions:
            if p.suffix.lower() in extensions:
                yield p
        else:
            yield p


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Batch convert files to Markdown using MarkItDown")
    parser.add_argument("--input", "-i", required=True, help="Input directory containing files to convert")
    parser.add_argument("--output", "-o", required=True, help="Output directory for generated .md files")
    parser.add_argument("--extensions", "-e", nargs="*", help="Optional list of file extensions to include (e.g. .pdf .xlsx). If omitted, all files are attempted.")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recurse into subdirectories")
    args = parser.parse_args(argv)

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Input directory does not exist: {input_dir}", file=sys.stderr)
        return 2
    output_dir.mkdir(parents=True, exist_ok=True)

    exts = None
    if args.extensions:
        exts = [e.lower() if e.startswith('.') else f'.{e.lower()}' for e in args.extensions]

    converter = MarkItDown()
    total = 0
    success = 0
    for path in iter_files(input_dir, exts, args.recursive):
        total += 1
        out_name = f"{path.stem}.md"
        out_path = output_dir / out_name
        try:
            result = converter.convert(str(path))
            text = getattr(result, 'text_content', None)
            if text is None:
                text = str(result)
            out_path.write_text(text, encoding="utf-8")
            print(f"Converted: {path} -> {out_path}")
            success += 1
        except FileConversionException as e:
            print(f"Failed to convert {path}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error converting {path}: {e}", file=sys.stderr)

    print(f"Finished: {success}/{total} files converted successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
