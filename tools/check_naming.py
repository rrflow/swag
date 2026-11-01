#!/usr/bin/env python3
"""check_naming.py - validate RRFLOW keys against config/rrflow.naming.yaml.

Stdlib only. Never creates folders or files.

Layers (later wins): shipped defaults (<repo>/config) -> user override
(<user config dir>/rrflow.naming.yaml, resolved per platform from
config/swag.paths.yaml) -> any --config files given on the command line.
"""
from __future__ import annotations

import argparse
import fnmatch
import os
import re
import sys
from pathlib import Path

SHIPPED_DIR_ENV = "SWAG_SHIPPED_CONFIG_DIR"
DEFAULT_SHIPPED_DIR = Path(__file__).resolve().parent.parent / "config"
NAMING_FILE = "rrflow.naming.yaml"
PATHS_FILE = "swag.paths.yaml"
KINDS = ("lane_key", "api_seam_key", "payload_field")


# --------------------------------------------------------------------------
# Minimal YAML subset reader (block maps, block lists, [a, b] flow lists,
# {} empty maps, quoted / plain scalars, comments).
# --------------------------------------------------------------------------
class YamlSubsetError(ValueError):
    pass


def _strip_comment(line: str) -> str:
    out, quote, i = [], None, 0
    while i < len(line):
        c = line[i]
        if quote:
            if c == "\\" and quote == '"' and i + 1 < len(line):
                out.append(line[i:i + 2]); i += 2; continue
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(c); i += 1
    return "".join(out).rstrip()


def _split_flow(s: str) -> list[str]:
    parts, buf, quote = [], [], None
    for c in s:
        if quote:
            buf.append(c)
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c; buf.append(c)
        elif c == ",":
            parts.append("".join(buf).strip()); buf = []
        else:
            buf.append(c)
    if "".join(buf).strip():
        parts.append("".join(buf).strip())
    return parts


def _scalar(s: str):
    s = s.strip()
    if s == "" or s in ("~", "null"):
        return None
    if s == "{}":
        return {}
    if s.startswith("[") and s.endswith("]"):
        return [_scalar(p) for p in _split_flow(s[1:-1])]
    if len(s) >= 2 and s[0] == s[-1] == '"':
        body = s[1:-1]
        return re.sub(r'\\(.)', lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), body)
    if len(s) >= 2 and s[0] == s[-1] == "'":
        return s[1:-1].replace("''", "'")
    if s in ("true", "True"):
        return True
    if s in ("false", "False"):
        return False
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    return s


def _split_key(text: str, where: str):
    m = re.match(r'^("[^"]*"|\'[^\']*\'|[^:]+?)\s*:(\s+(.*))?$', text)
    if not m:
        raise YamlSubsetError(f"{where}: expected 'key: value', got {text!r}")
    return _scalar(m.group(1)), (m.group(3) or "")


def load_yaml_subset(text: str, name: str = "<yaml>"):
    lines = []
    for n, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise YamlSubsetError(f"{name}:{n}: tabs are not allowed for indentation")
        s = _strip_comment(raw)
        if s.strip() and s.strip() not in ("---", "..."):
            lines.append((len(s) - len(s.lstrip(" ")), s.strip(), n))
    if not lines:
        return {}
    pos = 0

    def block(indent):
        nonlocal pos
        if lines[pos][1].startswith("- ") or lines[pos][1] == "-":
            out = []
            while pos < len(lines) and lines[pos][0] == indent and (lines[pos][1].startswith("- ") or lines[pos][1] == "-"):
                _, t, n = lines[pos]; pos += 1
                item = t[1:].strip()
                if item == "":
                    out.append(block(lines[pos][0]) if pos < len(lines) and lines[pos][0] > indent else None)
                elif re.match(r'^[^"\'\[{][^:]*:(\s|$)', item):
                    raise YamlSubsetError(f"{name}:{n}: maps inside lists are not supported by the subset reader")
                else:
                    out.append(_scalar(item))
            return out
        out = {}
        while pos < len(lines) and lines[pos][0] == indent:
            _, t, n = lines[pos]
            if t.startswith("- "):
                raise YamlSubsetError(f"{name}:{n}: unexpected list item")
            pos += 1
            k, v = _split_key(t, f"{name}:{n}")
            if v == "":
                out[k] = block(lines[pos][0]) if pos < len(lines) and lines[pos][0] > indent else None
            else:
                out[k] = _scalar(v)
        if pos < len(lines) and lines[pos][0] > indent:
            raise YamlSubsetError(f"{name}:{lines[pos][2]}: unexpected indentation")
        return out

    result = block(lines[0][0])
    if pos != len(lines):
        raise YamlSubsetError(f"{name}:{lines[pos][2]}: could not parse line")
    return result


def load_yaml_file(path: Path):
    return load_yaml_subset(path.read_text(encoding="utf-8"), str(path))


# --------------------------------------------------------------------------
# Layering and path resolution
# --------------------------------------------------------------------------
def deep_merge(base, over):
    """Mappings merge key by key; anything else (lists, scalars) replaces."""
    if isinstance(base, dict) and isinstance(over, dict):
        out = dict(base)
        for k, v in over.items():
            out[k] = deep_merge(base.get(k), v) if k in base else v
        return out
    return over


_PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:-)?")


def expand(template: str, env: dict) -> str:
    """Expand ${VAR} and ${VAR:-fallback} (fallbacks may nest). Unset -> '<unset:VAR>'."""
    out, i = [], 0
    while i < len(template):
        m = _PLACEHOLDER.match(template, i)
        if not m:
            out.append(template[i]); i += 1; continue
        var, has_default = m.group(1), m.group(2)
        j, depth = m.end(), 1
        while j < len(template) and depth:
            if template.startswith("${", j):
                depth += 1; j += 2; continue
            if template[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        if depth:
            raise ValueError(f"unterminated placeholder in {template!r}")
        default = template[m.end():j] if has_default else None
        val = env.get(var)
        if val:
            out.append(val)
        elif default is not None:
            out.append(expand(default, env))
        else:
            out.append(f"<unset:{var}>")
        i = j + 1
    return "".join(out)


def detect_platform(name: str | None = None) -> str:
    if name:
        return name
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def resolve_paths(paths_cfg: dict, platform: str, env: dict) -> dict:
    plats = paths_cfg.get("platforms") or {}
    if platform not in plats:
        raise SystemExit(f"config error: platform {platform!r} not in {PATHS_FILE} (have {sorted(plats)})")
    env = dict(env)
    env["APP"] = str(paths_cfg.get("app_name", ""))
    resolved = {kind: expand(str(tpl), env) for kind, tpl in plats[platform].items()}
    override_env = paths_cfg.get("config_dir_env_override")
    if override_env and env.get(override_env):
        resolved["config"] = env[override_env]
        resolved["_config_source"] = f"env {override_env}"
    else:
        resolved["_config_source"] = f"{PATHS_FILE} platforms.{platform}.config"
    return resolved


def load_layers(shipped_dir: Path, platform: str, env: dict, extra: list[Path], use_user: bool):
    paths_cfg = load_yaml_file(shipped_dir / PATHS_FILE)
    resolved = resolve_paths(paths_cfg, platform, env)
    override_name = paths_cfg.get("naming_override_file", NAMING_FILE)
    layers = [("shipped", shipped_dir / NAMING_FILE)]
    if use_user:
        layers.append(("user", Path(resolved["config"]) / override_name))
    layers += [("cli", p) for p in extra]
    cfg, report = {}, []
    for label, p in layers:
        if p.is_file():
            cfg = deep_merge(cfg, load_yaml_file(p))
            report.append((label, p, "loaded"))
        elif label == "shipped" or label == "cli":
            raise SystemExit(f"config error: {label} config not found: {p}")
        else:
            report.append((label, p, "absent (shipped defaults apply)"))
    return cfg, resolved, report


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def validate_config(cfg: dict) -> list[str]:
    """Return config warnings; raise SystemExit on hard config errors."""
    warns = []
    rw = cfg.get("reserved_words") or {}
    words = [str(w) for w in rw.get("words") or []]
    repl = rw.get("replacements") or {}
    lanes = [str(k) for k in (cfg.get("lanes") or {}).get("keys") or []]
    for k in rw.get("applies_to") or []:
        if k not in KINDS:
            raise SystemExit(f"config error: reserved_words.applies_to has unknown kind {k!r}; known: {KINDS}")
    for w in words:
        if w not in repl:
            warns.append(f"reserved word {w!r} has no replacement mapping")
        elif lanes and repl[w] not in lanes:
            warns.append(f"replacement {w!r} -> {repl[w]!r} is not a lane key")
    if rw.get("report_replacement_collisions", True):
        by_target = {}
        for w, t in repl.items():
            by_target.setdefault(t, []).append(w)
        for t, ws in by_target.items():
            if len(ws) > 1:
                warns.append(f"replacement collision: {' and '.join(sorted(ws))} both map to {t!r}")
    mode = (cfg.get("on_violation") or {}).get("mode", "error")
    if mode not in ("error", "warn"):
        raise SystemExit(f"config error: on_violation.mode must be error|warn, got {mode!r}")
    return warns


def check_key(key: str, kind: str, cfg: dict) -> list[dict]:
    hits = []
    pats = cfg.get("patterns") or {}
    rule = pats.get(kind) or {}
    if rule.get("regex") and not re.fullmatch(rule["regex"], key):
        hits.append({"rule": "pattern", "detail": f"does not match {kind} pattern ({rule.get('description', rule['regex'])})"})

    anti = pats.get("anti_names") or {}
    if kind in (anti.get("applies_to") or KINDS):
        cs = anti.get("case_sensitive", False)
        for g in anti.get("globs") or []:
            if (fnmatch.fnmatchcase(key, g) if cs else fnmatch.fnmatchcase(key.lower(), g.lower())):
                hits.append({"rule": "anti_name", "detail": f"matches anti-name {g!r}"})

    lanes_cfg = cfg.get("lanes") or {}
    if kind == "lane_key" and lanes_cfg.get("enforce_closed_set") and key not in (lanes_cfg.get("keys") or []):
        hits.append({"rule": "unknown_lane", "detail": f"not in closed lane set {lanes_cfg.get('keys')}"})

    rw = cfg.get("reserved_words") or {}
    if kind in (rw.get("applies_to") or []):
        m = rw.get("match") or {}
        if m.get("mode", "whole_segment") != "whole_segment":
            raise SystemExit(f"config error: unsupported match.mode {m.get('mode')!r}")
        cs = bool(m.get("case_sensitive", False))
        sep = m.get("segment_separator", "_")
        norm = (lambda s: s) if cs else (lambda s: s.lower())
        forms = {}
        for w in rw.get("words") or []:
            forms[norm(str(w))] = str(w)
            for f in ((m.get("extra_forms") or {}).get(w) or []):
                forms[norm(str(f))] = str(w)
        segs = key.split(sep)
        repl = rw.get("replacements") or {}
        for i, seg in enumerate(segs):
            word = forms.get(norm(seg))
            if word is None:
                continue
            target = repl.get(word)
            suggestion = sep.join(segs[:i] + [target] + segs[i + 1:]) if target else None
            hits.append({"rule": "reserved_word", "word": word, "segment": seg,
                         "detail": f"segment {seg!r} is reserved word {word!r}",
                         "suggest": suggestion})
    return hits


def read_keys(path: Path, kind_default: str) -> list[tuple[str, str]]:
    """Text: one key per line (# comments). YAML (.yaml/.yml): a list, a 'keys:' list,
    or a mapping of kind -> list."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        data = load_yaml_subset(text, str(path))
        if isinstance(data, list):
            return [(str(k), kind_default) for k in data]
        if isinstance(data, dict):
            if "keys" in data:
                return [(str(k), kind_default) for k in data["keys"] or []]
            out = []
            for kind, ks in data.items():
                if kind not in KINDS:
                    raise SystemExit(f"input error: unknown kind {kind!r} in {path}")
                out += [(str(k), kind) for k in ks or []]
            return out
        raise SystemExit(f"input error: unsupported YAML structure in {path}")
    out = []
    for line in text.splitlines():
        s = _strip_comment(line).strip()
        if s:
            out.append((s, kind_default))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Validate RRFLOW keys against rrflow.naming.yaml (shipped defaults + user override).")
    ap.add_argument("inputs", nargs="*", type=Path, help="key files (.txt one per line, or .yaml)")
    ap.add_argument("--kind", choices=KINDS, default="api_seam_key", help="kind for plain key lists (default: api_seam_key)")
    ap.add_argument("--shipped-dir", type=Path, default=None,
                    help=f"shipped config dir (default: ${SHIPPED_DIR_ENV} or <repo>/config)")
    ap.add_argument("--config", type=Path, action="append", default=[], help="extra override file(s), applied last")
    ap.add_argument("--no-user", action="store_true", help="ignore the per-user override")
    ap.add_argument("--platform", choices=("windows", "linux", "macos"), help="resolve paths as this platform")
    ap.add_argument("--on-violation", choices=("error", "warn"), help="override on_violation.mode")
    ap.add_argument("--summary", action="store_true", help="print per-word counts and only the first N violations")
    ap.add_argument("--limit", type=int, default=0, help="with --summary, max violations to list (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="show resolved paths and config layers, then exit; creates nothing")
    a = ap.parse_args(argv)

    shipped = a.shipped_dir or Path(os.environ.get(SHIPPED_DIR_ENV) or DEFAULT_SHIPPED_DIR)
    platform = detect_platform(a.platform)
    cfg, resolved, report = load_layers(shipped, platform, dict(os.environ), a.config, not a.no_user)
    warns = validate_config(cfg)

    if a.dry_run:
        print(f"platform: {platform}")
        print(f"shipped config dir: {shipped}")
        for k in ("config", "data", "state", "cache"):
            if k in resolved:
                p = Path(resolved[k])
                print(f"  {k:<6} {resolved[k]}  [{'exists' if p.is_dir() else 'not created'}]")
        print(f"  config dir source: {resolved['_config_source']}")
        print("layers (later wins):")
        for label, p, status in report:
            print(f"  {label:<8} {p}  [{status}]")
        for w in warns:
            print(f"config warning: {w}")
        print("dry run: nothing validated, nothing created")
        return 0

    if not a.inputs:
        ap.error("no input files (or use --dry-run)")

    for w in warns:
        print(f"config warning: {w}")
    mode = a.on_violation or (cfg.get("on_violation") or {}).get("mode", "error")
    total_keys, violations = 0, []
    for p in a.inputs:
        for key, kind in read_keys(p, a.kind):
            total_keys += 1
            for h in check_key(key, kind, cfg):
                violations.append((p, key, kind, h))

    per_word = {}
    for _, _, _, h in violations:
        if h["rule"] == "reserved_word":
            per_word[h["word"]] = per_word.get(h["word"], 0) + 1
    flagged_keys = len({(str(p), k) for p, k, _, _ in violations})

    shown = violations if not (a.summary and a.limit) else violations[: a.limit]
    for p, key, kind, h in shown:
        line = f"{'ERROR' if mode == 'error' else 'WARN'} {p.name}: {key} [{kind}] {h['rule']}: {h['detail']}"
        if h.get("suggest"):
            line += f" -> suggest {h['suggest']}"
        print(line)
    if len(shown) < len(violations):
        print(f"... {len(violations) - len(shown)} more not shown")
    print(f"checked {total_keys} keys: {len(violations)} violations on {flagged_keys} keys (mode={mode})")
    if per_word:
        print("reserved-word hits: " + ", ".join(f"{w}={n}" for w, n in sorted(per_word.items(), key=lambda x: (-x[1], x[0]))))
    return 1 if violations and mode == "error" else 0


if __name__ == "__main__":
    sys.exit(main())
