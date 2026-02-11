# Normalize seed skills

This script normalizes `skills_text` values in the SQL seed file using the canonical
skills list in `skills.json`.

Usage:

```bash
python scripts/normalize_seed_skills.py \
  --input docker/seed/seed.sql \
  --skills scripts/skills.json \
  --output docker/seed/seed.normalized.sql \
  --report scripts/skills_normalization_report.json
```

Behavior:

- Uses `scripts/skills.json` as canonical skill names.
- Replaces tokens with canonical casing, joins with `, `, removes duplicates (preserving order).
- Leaves unmatched tokens unchanged and records them in the JSON report.
- Does not overwrite original `seed.sql` by default.

If you want to apply alias mappings, edit `scripts/skill_aliases.json` and re-run.
