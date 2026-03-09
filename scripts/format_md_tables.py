#!/usr/bin/env python3

# Copyright © 2026 Xavier Beheydt <xavier.beheydt@gmail.com> - All Rights Reserved

"""Format Markdown tables across a repository.

This script finds Markdown tables (pipe-delimited) outside fenced code
blocks and aligns columns for readability. It can print diffs and apply
changes in-place.

Usage:
  python3 scripts/format_md_tables.py [--apply] [--path PATH]

Examples:
  # Show diffs for all .md files (no writes)
  python3 scripts/format_md_tables.py

  # Apply changes in-place under the current directory
  python3 scripts/format_md_tables.py --apply
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from typing import List, Tuple


def is_fence_line(line: str) -> bool:
    return re.match(r"^\s*(`{3,}|~{3,})", line) is not None


def is_separator_line(line: str) -> bool:
    """Return True if the line looks like a markdown table separator."""
    if "|" not in line:
        return False
    s = line.strip()
    inner = s.strip().strip("|")
    if inner == "":
        return False
    parts = [p.strip() for p in inner.split("|")]
    if not parts:
        return False
    ok = True
    seen_dash = False
    for p in parts:
        if p == "":
            ok = False
            break
        if re.fullmatch(r":?-+:?", p) is None:
            ok = False
            break
        if "-" in p:
            seen_dash = True
    return ok and seen_dash


def split_row(line: str) -> List[str]:
    s = line.rstrip("\n")
    parts = s.split("|")
    if s.strip().startswith("|") and parts and parts[0] == "":
        parts = parts[1:]
    if s.strip().endswith("|") and parts and parts[-1] == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


def detect_table_block(lines: List[str], start: int) -> Tuple[int, int]:
    """Detect a markdown table starting at index `start`.

    Returns (start_index, end_index) of the block (end exclusive), or
    (start, start) if no table detected.
    """
    if "|" not in lines[start]:
        return start, start
    if start + 1 >= len(lines):
        return start, start
    if not is_separator_line(lines[start + 1]):
        return start, start
    j = start
    while j < len(lines) and ("|" in lines[j]):
        j += 1
    return start, j


def format_table_block(block_lines: List[str]) -> List[str]:
    """Format a table block (list of lines) and return formatted lines."""
    token_rows = [split_row(line) for line in block_lines]
    sep_idx = None
    for idx, tokens in enumerate(token_rows):
        if tokens and all(re.fullmatch(r":?-+:?", t) for t in tokens):
            sep_idx = idx
            break
    if sep_idx is None:
        return block_lines

    header_rows = token_rows[:sep_idx]
    sep_tokens = token_rows[sep_idx]
    data_rows = token_rows[sep_idx + 1 :]

    col_count = max(len(r) for r in token_rows)

    def norm_row(r: List[str]) -> List[str]:
        return r + [""] * (col_count - len(r))

    header_rows = [norm_row(r) for r in header_rows]
    data_rows = [norm_row(r) for r in data_rows]
    sep_tokens = norm_row(sep_tokens)

    aligns: List[str] = []
    for t in sep_tokens:
        tt = t.strip()
        if tt.startswith(":") and tt.endswith(":"):
            aligns.append("center")
        elif tt.startswith(":"):
            aligns.append("left")
        elif tt.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("left")

    widths = [0] * col_count
    for row in header_rows + data_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    widths = [max(3, w) for w in widths]

    out: List[str] = []

    def format_row(row: List[str]) -> str:
        cells = []
        for i, cell in enumerate(row):
            a = aligns[i] if i < len(aligns) else "left"
            w = widths[i]
            if a == "right":
                padded = cell.rjust(w)
            elif a == "center":
                padded = cell.center(w)
            else:
                padded = cell.ljust(w)
            cells.append(" " + padded + " ")
        return "|" + "|".join(cells) + "|"

    for hr in header_rows:
        out.append(format_row(hr))

    sep_cells = []
    for i, a in enumerate(aligns):
        internal_w = widths[i]
        if a == "center":
            colon_count = 2
        elif a in ("left", "right"):
            colon_count = 1
        else:
            colon_count = 0
        dash_count = max(1, internal_w - colon_count)
        if a == "center":
            tok = ":" + ("-" * dash_count) + ":"
        elif a == "left":
            tok = ":" + ("-" * dash_count)
        elif a == "right":
            tok = ("-" * dash_count) + ":"
        else:
            tok = "-" * dash_count
        sep_cells.append(" " + tok + " ")

    out.append("|" + "|".join(sep_cells) + "|")

    for dr in data_rows:
        out.append(format_row(dr))

    return out


def process_text(text: str) -> Tuple[str, List[Tuple[int, int]]]:
    """Return (new_text, list_of_modified_ranges_as_line_indices)."""
    lines = text.splitlines()
    out_lines: List[str] = []
    i = 0
    in_fence = False
    fence_marker = None
    modified_ranges: List[Tuple[int, int]] = []
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if m:
            fence = m.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = fence
            elif fence == fence_marker:
                in_fence = False
                fence_marker = None
            out_lines.append(line)
            i += 1
            continue

        if in_fence:
            out_lines.append(line)
            i += 1
            continue

        start, end = detect_table_block(lines, i)
        if end > start:
            block = lines[start:end]
            formatted = format_table_block(block)
            if formatted != block:
                modified_ranges.append((start, end))
            out_lines.extend(formatted)
            i = end
            continue

        out_lines.append(line)
        i += 1

    new_text = "\n".join(out_lines)
    if text.endswith("\n"):
        new_text += "\n"
    return new_text, modified_ranges


def find_md_files(root: str, excludes: List[str] | None = None) -> List[str]:
    md_files: List[str] = []
    excludes = excludes or []
    for dirpath, _dirnames, filenames in os.walk(root):
        parts = dirpath.split(os.sep)
        if ".git" in parts or "node_modules" in parts:
            continue
        for fn in filenames:
            if not fn.lower().endswith(".md"):
                continue
            full = os.path.join(dirpath, fn)
            skip = False
            for pat in excludes:
                if pat and (pat in full or pat in fn):
                    skip = True
                    break
            if skip:
                continue
            md_files.append(full)
    return sorted(md_files)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="Write changes in-place")
    p.add_argument("--path", default=".", help="Root path to search (default: .)")
    p.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Substring to exclude (repeatable)",
    )
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()

    files = find_md_files(args.path, excludes=args.exclude)
    if args.verbose:
        print(f"Found {len(files)} markdown files under {args.path}")

    modified_any = False
    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                orig = f.read()
        except Exception as e:
            print(f"[skip] {fp}: read error: {e}")
            continue

        new_text, _ranges = process_text(orig)
        if new_text != orig:
            modified_any = True
            print("\n--- Diff for:", fp)
            for line in difflib.unified_diff(
                orig.splitlines(True),
                new_text.splitlines(True),
                fromfile=fp,
                tofile=fp + " (formatted)",
            ):
                sys.stdout.write(line)
            if args.apply:
                with open(fp, "w", encoding="utf-8", newline="\n") as f:
                    f.write(new_text)
                print(f"\n[updated] {fp}")
            else:
                print(f"\n[would update] {fp} (run with --apply to write)")

    if not modified_any:
        print("No markdown tables needed reformatting.")
    else:
        if not args.apply:
            print("\nRun with --apply to write changes in-place.")
        else:
            print("\nAll changes applied.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
