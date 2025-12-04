#!/usr/bin/env python3
"""
search_by_tag.py

Small CLI to explore and search JSON records by dot-path fields.

Features:
- list available dot-path fields and sample types/values
- list unique values for a field
- search records where a field contains a substring (case-insensitive)
- show a full record by index

Usage examples in README.md
"""
import argparse
import json
import os
from collections import Counter
from typing import Any


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def walk_paths(obj: Any, prefix: str = ""):
    """Yield (path, sample_value) for nested dicts/lists."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            yield p, v
            yield from walk_paths(v, p)
    elif isinstance(obj, list) and obj:
        # show paths for first element to represent structure
        yield from walk_paths(obj[0], prefix)


def get_by_path(obj: Any, path: str):
    parts = path.split(".") if path else []
    cur = obj
    for p in parts:
        if cur is None:
            return None
        if isinstance(cur, list):
            # if list, try index if numeric, otherwise return list
            if p.isdigit():
                try:
                    cur = cur[int(p)]
                    continue
                except Exception:
                    return None
            else:
                # non-numeric next component — return list (caller will stringify)
                return cur
        if isinstance(cur, dict):
            cur = cur.get(p)
        else:
            return None
    return cur


def list_fields(records):
    paths = Counter()
    samples = {}
    for r in records:
        for p, v in walk_paths(r):
            paths[p] += 1
            if p not in samples:
                samples[p] = v
    # sort by frequency
    for p, cnt in paths.most_common():
        sample = samples.get(p)
        t = type(sample).__name__
        s = str(sample)
        if len(s) > 120:
            s = s[:117] + "..."
        print(f"{p} ({cnt} records) — type={t} sample={s}")


def list_values(records, path, limit=50):
    c = Counter()
    for r in records:
        v = get_by_path(r, path)
        if v is None:
            continue
        if isinstance(v, list):
            for x in v:
                c[str(x).strip()] += 1
        else:
            c[str(v).strip()] += 1
    for val, cnt in c.most_common(limit):
        print(f"{cnt:6d}  {val}")


def search(records, path, term, show=10, json_out=None):
    term = term.lower()
    matches = []
    for i, r in enumerate(records):
        v = get_by_path(r, path)
        if v is None:
            continue
        matched = False
        if isinstance(v, list):
            for x in v:
                if term in str(x).lower():
                    matched = True
                    break
        else:
            if term in str(v).lower():
                matched = True
        if matched:
            matches.append((i, r))
    print(f"Found {len(matches)} matching records for {path} containing '{term}'")
    for idx, rec in matches[:show]:
        title = get_by_path(rec, "job.title") or get_by_path(rec, "job.name") or "(no title)"
        company = get_by_path(rec, "job.company") or get_by_path(rec, "metadata.company") or "(no company)"
        print(f"[{idx}] {title} @ {company}")
    if json_out:
        out = [r for _, r in matches]
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"Wrote {len(out)} records to {json_out}")


def show_record(records, index):
    try:
        rec = records[index]
    except Exception:
        print("Index out of range")
        return
    print(json.dumps(rec, ensure_ascii=False, indent=2))


def main():
    p = argparse.ArgumentParser(description="Search JSON records by dot-field")
    p.add_argument("--file", "-f", default="matches_2025-12-03T15-36-21.json", help="JSON file path (array of records)")
    p.add_argument("--list-fields", action="store_true", help="List discovered dot-path fields and samples")
    p.add_argument("--list-values", help="List top values for a given dot-path (e.g. job.company)")
    p.add_argument("--search", nargs=2, metavar=("FIELD","TERM"), help="Search FIELD for TERM (substring, case-insensitive)")
    p.add_argument("--show", type=int, help="Show full record by index")
    p.add_argument("--json-out", help="When searching, write matched records to this file")
    p.add_argument("--limit", type=int, default=50, help="Limit for list-values")
    args = p.parse_args()

    path = args.file
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    records = load_json(path)
    if not isinstance(records, list):
        print("Expected top-level JSON array of records")
        return

    if args.list_fields:
        list_fields(records)
        return

    if args.list_values:
        list_values(records, args.list_values, limit=args.limit)
        return

    if args.search:
        field, term = args.search
        search(records, field, term, show=20, json_out=args.json_out)
        return

    if args.show is not None:
        show_record(records, args.show)
        return

    p.print_help()


if __name__ == "__main__":
    main()
