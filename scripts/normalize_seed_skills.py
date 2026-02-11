#!/usr/bin/env python3
"""Normalize `skills_text` values in a SQL seed file using canonical skills.

Writes a new SQL file with normalized, canonical-cased skills (comma + space separated),
and emits a JSON report with unmatched tokens and per-row changes.

Usage:
  python normalize_seed_skills.py \
    --input docker/seed/seed.sql \
    --skills scripts/skills.json \
    --output docker/seed/seed.normalized.sql \
    --report scripts/skills_normalization_report.json
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from typing import List, Tuple, Dict, Any


def load_canonical(skills_path: str) -> Dict[str, str]:
    with open(skills_path, "r", encoding="utf-8") as f:
        lst = json.load(f)

    def norm(s: str) -> str:
        s2 = s.lower()
        s2 = re.sub(r"[^0-9a-z ]+", "", s2)
        s2 = re.sub(r"\s+", " ", s2).strip()
        return s2

    d = {norm(s): s for s in lst}
    d_ci = {s.lower(): s for s in lst}
    d.update({k: v for k, v in d_ci.items() if k not in d})
    return d


def find_participants_insert(sql: str) -> Tuple[int, int, str]:
    m = re.search(
        r"INSERT\s+INTO\s+\"public\"\.\"participants\"\s*\((.*?)\)\s*VALUES",
        sql,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        raise RuntimeError("Could not find participants INSERT header")
    values_pos = sql.lower().find("values", m.end())
    if values_pos == -1:
        raise RuntimeError("Could not find VALUES keyword for participants INSERT")
    end_pos = sql.find(");", values_pos)
    if end_pos == -1:
        raise RuntimeError("Could not find end of participants INSERT block")
    block = sql[values_pos : end_pos + 2]
    return values_pos, end_pos + 2, block


def split_top_level_tuples(block: str) -> List[str]:
    tuples = []
    i = 0
    n = len(block)
    depth = 0
    in_quote = False
    start = None
    while i < n:
        ch = block[i]
        if ch == "'":
            if in_quote and i + 1 < n and block[i + 1] == "'":
                i += 2
                continue
            in_quote = not in_quote
            i += 1
            continue
        if not in_quote:
            if ch == "(":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and start is not None:
                    tuples.append(block[start : i + 1])
                    start = None
        i += 1
    return tuples


def split_fields(tuple_sql: str) -> List[str]:
    s = tuple_sql.strip()
    if s.startswith("(") and s.endswith(")"):
        s = s[1:-1]
    fields = []
    cur = []
    in_quote = False
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "'":
            cur.append(ch)
            if in_quote and i + 1 < n and s[i + 1] == "'":
                cur.append("'")
                i += 2
                continue
            in_quote = not in_quote
            i += 1
            continue
        if ch == "," and not in_quote:
            fields.append("".join(cur).strip())
            cur = []
            i += 1
            continue
        cur.append(ch)
        i += 1
    fields.append("".join(cur).strip())
    return fields


def unquote_sql_string(s: str) -> str:
    s = s.strip()
    if s.upper() == "NULL":
        return None
    if s.startswith("'") and s.endswith("'"):
        inner = s[1:-1]
        inner = inner.replace("''", "'")
        return inner
    return s


def quote_sql_string(s: str) -> str:
    if s is None:
        return "NULL"
    esc = s.replace("'", "''")
    return f"'{esc}'"


def split_skill_tokens(skills_str: str) -> List[str]:
    tokens = []
    cur = []
    depth = 0
    for ch in skills_str:
        if ch == "(":
            depth += 1
            cur.append(ch)
            continue
        if ch == ")":
            depth = max(0, depth - 1)
            cur.append(ch)
            continue
        if ch == "," and depth == 0:
            token = "".join(cur).strip()
            if token:
                tokens.append(token)
            cur = []
            continue
        cur.append(ch)
    last = "".join(cur).strip()
    if last:
        tokens.append(last)
    out = []
    for t in tokens:
        parts = [p.strip() for p in t.split(";") if p.strip()]
        out.extend(parts)
    return out


def normalize_key(s: str) -> str:
    s2 = s.lower()
    s2 = re.sub(r"[^0-9a-z ]+", "", s2)
    s2 = re.sub(r"\s+", " ", s2).strip()
    return s2


def map_tokens(
    tokens: List[str], canon_map: Dict[str, str], unmatched_counter: Counter
) -> List[str]:
    seen = set()
    out = []
    for tok in tokens:
        t = tok.strip()
        if not t:
            continue
        mapped = None
        low = t.lower()
        # direct lowercase match
        if low in canon_map:
            mapped = canon_map[low]
        if mapped is None:
            nk = normalize_key(t)
            mapped = canon_map.get(nk)
        if mapped is None and "/" in t:
            parts = [p.strip() for p in t.split("/") if p.strip()]
            mapped_parts = []
            any_mapped = False
            for p in parts:
                mp = canon_map.get(normalize_key(p))
                if mp:
                    mapped_parts.append(mp)
                    any_mapped = True
                else:
                    mapped_parts.append(p)
            if any_mapped:
                mapped = "/".join(mapped_parts)
        if mapped is None:
            unmatched_counter[t] += 1
            mapped = t
        if mapped not in seen:
            out.append(mapped)
            seen.add(mapped)
    return out


def process(sql_text: str, skills_path: str) -> Tuple[str, Dict[str, Any]]:
    canon_map = load_canonical(skills_path)
    values_pos, end_pos, block = find_participants_insert(sql_text)
    tuples = split_top_level_tuples(block)
    header_match = re.search(
        r"INSERT\s+INTO\s+\"public\"\.\"participants\"\s*\((.*?)\)\s*VALUES",
        sql_text,
        re.IGNORECASE | re.DOTALL,
    )
    if not header_match:
        raise RuntimeError("Could not parse participants columns header")
    cols_raw = header_match.group(1)
    cols = [c.strip().strip('"') for c in cols_raw.split(",")]
    try:
        skills_idx = cols.index("skills_text")
    except ValueError:
        raise RuntimeError("skills_text column not found in participants INSERT header")

    unmatched = Counter()
    per_row = []
    new_tuples = []
    for tup in tuples:
        fields = split_fields(tup)
        if skills_idx >= len(fields):
            new_tuples.append(tup)
            continue
        orig_field = fields[skills_idx]
        orig_val = unquote_sql_string(orig_field)
        if orig_val is None:
            per_row.append({"original": None, "transformed": None})
            new_tuples.append(tup)
            continue
        tokens = split_skill_tokens(orig_val)
        mapped = map_tokens(tokens, canon_map, unmatched)
        transformed = ", ".join(mapped)
        fields[skills_idx] = quote_sql_string(transformed)
        per_row.append({"original": orig_val, "transformed": transformed})
        new_tuples.append("(" + ", ".join(fields) + ")")

    new_block = ",\n".join(new_tuples)
    new_sql = sql_text[:values_pos] + new_block + sql_text[end_pos:]

    report = {
        "rows_processed": len(tuples),
        "per_row": per_row,
        "unmatched_tokens": dict(unmatched),
    }
    return new_sql, report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--skills", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--report", required=True)
    args = p.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        sql_text = f.read()

    new_sql, report = process(sql_text, args.skills)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(new_sql)

    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Wrote normalized SQL to {args.output}")
    print(f"Wrote report to {args.report}")


if __name__ == "__main__":
    main()
