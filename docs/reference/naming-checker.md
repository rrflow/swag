# RRFLOW naming checker

Shipped defaults and a stdlib-only checker for RRFLOW key naming, derived from the
**Clyffy 09 Glossary ADR (Canonical Naming)**, section 2 rule 3 ("Absorb jargon, don't dump it").

```
config/rrflow.naming.yaml    naming rules (shipped defaults)
config/swag.paths.yaml       per-platform user config/data/state/cache folders
tools/check_naming.py        checker (Python 3.10+, stdlib only)
tests/fixtures/*.txt         sample key lists (lane keys, sample seams, Doc 10 seam snapshot)
```

## Layering

Later layers win:

1. **Shipped defaults**: `config/` in this repo (or `--shipped-dir`, or env `SWAG_SHIPPED_CONFIG_DIR`).
2. **User override**: `<user config dir>/rrflow.naming.yaml`. The dir comes from `swag.paths.yaml`
   for the current platform, or from env `SWAG_CONFIG_DIR` if set.
3. **CLI overrides**: each `--config FILE`, in order.

Merge rule: mappings merge key by key; **lists and scalars replace**. So a user file that only sets
`reserved_words:` / `  words: [security]` bans only `security`, and every other field keeps the shipped value.
If the user file is missing, the shipped defaults apply. `--no-user` skips layer 2.

## Per-user folders (app name `swag`)

| platform | config | data | state | cache |
|---|---|---|---|---|
| Windows | `%APPDATA%\swag` | `%LOCALAPPDATA%\swag` | `%LOCALAPPDATA%\swag\state` | `%LOCALAPPDATA%\swag\cache` |
| Linux | `$XDG_CONFIG_HOME/swag` (`~/.config/swag`) | `$XDG_DATA_HOME/swag` (`~/.local/share/swag`) | `$XDG_STATE_HOME/swag` (`~/.local/state/swag`) | `$XDG_CACHE_HOME/swag` (`~/.cache/swag`) |
| macOS | `~/Library/Application Support/swag` | same as config | `.../Application Support/swag/state` | `~/Library/Caches/swag` |

Templates use `${VAR}` and `${VAR:-fallback}`. `${APP}` is `app_name`. The checker only
**resolves** these paths and never creates folders. Deployment creates them.

## rrflow.naming.yaml fields

| field | meaning |
|---|---|
| `schema_version` | config format version (1) |
| `source.*` | the ADR this file implements |
| `lanes.keys` | closed lane set (ADR section 5). Replacement targets must be in it |
| `lanes.enforce_closed_set` | `lane_key` values outside the set are violations (fail closed, section 2 rule 4) |
| `reserved_words.words` | banned capability words (section 2 rule 3) |
| `reserved_words.citation` | the ADR rule text |
| `reserved_words.applies_to` | key kinds the ban covers: `lane_key`, `api_seam_key` (`payload_field` is also allowed) |
| `reserved_words.match.mode` | `whole_segment`: the key is split on `segment_separator` (`_`) and a segment must equal a word |
| `reserved_words.match.case_sensitive` | `false`, so `Security_x` is also a hit |
| `reserved_words.match.extra_forms` | optional extra spellings per word (e.g. `testing: [test]`). Empty by default |
| `reserved_words.replacements` | suggested lane key per word (used to build the suggested key) |
| `reserved_words.report_replacement_collisions` | warn when two words map to one lane |
| `on_violation.mode` | `error` (exit 1, default) or `warn` (exit 0). CLI `--on-violation` overrides it |
| `patterns.<kind>.regex` | allowed shape: snake_case for lane/seam keys, lowerCamel for payload fields |
| `patterns.anti_names.globs` | never-mint names: `*_v2`, `new_*` (section 3) |

**Known collision:** `design` and `implementation` both map to `shape`. The ADR says shape
absorbs "implementation + design form", but orient also absorbs "design framing". The checker
prints a config warning about this until the mapping is decided.

## Running the checker

```powershell
# show resolved paths and loaded layers (creates nothing)
python tools\check_naming.py --dry-run

# lane keys (also enforces the closed lane set)
python tools\check_naming.py --kind lane_key tests\fixtures\lane_keys.txt

# API seam keys (the default kind)
python tools\check_naming.py tests\fixtures\sample_seam_keys.txt

# large lists: per-word counts plus the first 10 violations
python tools\check_naming.py --summary --limit 10 tests\fixtures\doc10_seam_keys.txt
```

Input: a `.txt` file with one key per line (`#` comments allowed), or a `.yaml` file holding
a list, a `keys:` list, or a block mapping of kind to list
(`lane_key:` / `api_seam_key:` / `payload_field:`, each with a list under it).
Output: one line per violation, with a suggested replacement for reserved-word hits.
Exit code: 1 when there are violations in `error` mode, otherwise 0.

The config reader supports a YAML subset only (block maps and lists, `[a, b]` inline lists,
quoted or plain scalars, comments) so the checker stays stdlib-only. Keep user overrides in that subset.
