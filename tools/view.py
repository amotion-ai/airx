#!/usr/bin/env python3
"""airx view — a static, no-server viewer over whatever AI-readiness layers a wiki has.

Walks a wiki and emits ONE self-contained HTML file (zero JS, zero CDN, fully offline — open it with a
`file://` URL). This is the "browse what you've built" layer: NOT a worker or a port (the roadmap's
explicit non-goal), just a generated artifact you regenerate on demand.

What it differentiates on is airx's discipline, not markdown fidelity: per note it shows the frontmatter
card + **citations resolved vs dangling** + TBD count, and across the wiki the Coverage·Depth·Trust
headline. It COMPOSES the existing deterministic surface — `verify-citations.py` for per-note resolution
and `score.py` for the headline — rather than re-deriving either (the repo's "compose, don't clone" rule).

Layers are opt-in: a section is rendered only if that layer exists on disk. Nothing is stamped empty.

    python3 view.py <wiki-dir>
Exit: 0 on a real wiki; 2 if the wiki dir is missing/usage error. Stdlib only, no LLM.
Writes: <wiki>/ai_view.html (regenerable; added to <wiki>/.gitignore — it's a generated artifact).
"""
from __future__ import annotations

import html
import importlib.util
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


HERE = Path(__file__).resolve().parent
vc = _load("airx_vc", HERE / "verify-citations.py")
init = _load("airx_init", HERE / "init.py")

# A file:line citation or a bare durable symbol — used only to VISUALLY highlight the verification
# discipline inside a note body. Resolution itself is done by verify-citations, never re-implemented here.
_CITE_RE = re.compile(r"\b[\w./-]+\.(?:java|kt|py|go|ts|js|rb|cs|xml|xhtml|sql|yml|yaml|properties):\d+\b")
_TBD_RE = re.compile(r"\bTBD\b")


def read(p: Path) -> str:
    try:
        return p.read_text(errors="ignore")
    except Exception:
        return ""


def frontmatter(text: str):
    """Return (meta dict, body). Minimal YAML-ish key: value parse (no PyYAML — stdlib only)."""
    meta: dict = {}
    if not text.startswith("---"):
        return meta, text
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    block = text[3:end]
    body = text[end + 4:].lstrip("\n")
    for line in block.splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            k, _, v = line.partition(":")
            k = k.strip()
            if k and not line.startswith((" ", "\t")):       # top-level keys only (skip nested/block scalars)
                meta[k] = v.strip()
    return meta, body


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def body_html(body: str) -> str:
    """Escape, then highlight citations (green) and TBD (red) so the verify discipline is visible at a
    glance. Deliberately NOT a markdown renderer — raw text is honest and never renders tables broken."""
    out = esc(body)
    out = _CITE_RE.sub(lambda m: f'<span class="cite">{m.group(0)}</span>', out)
    out = _TBD_RE.sub('<span class="tbd">TBD</span>', out)
    return out


def note_stats(repo, idx, md: Path):
    """Per-note (file:line total/resolved, symbol total/resolved, symbol external, TBD count) — via
    verify-citations' own functions, so resolution logic is never cloned. External symbols (framework
    classes) are surfaced so the caller can exclude them, matching verify-citations' advisory treatment.
    repo/idx are None when the wiki has no resolvable repo."""
    text = read(md)
    tbd = len(_TBD_RE.findall(text))
    if repo is None or idx is None:
        return None, None, None, None, None, tbd
    try:
        t, r, _ = vc.note_citations(repo, md)
        by, _ = vc.note_symbols(idx, md)
        st = sum(v["total"] for v in by.values())
        sr = sum(v["resolved"] for v in by.values())
        sx = sum(v.get("external", 0) for v in by.values())
        return t, r, st, sr, sx, tbd
    except Exception:
        return None, None, None, None, None, tbd


def badge(label: str, kind: str) -> str:
    return f'<span class="badge {kind}">{esc(label)}</span>'


def cite_badge(total, resolved):
    if total is None:
        return badge("unverified", "muted")
    if total == 0:
        return badge("0 cites", "muted")
    kind = "ok" if resolved == total else "warn"
    return badge(f"{resolved}/{total} resolve", kind)


def render_notes(mem: Path, repo, idx) -> str:
    notes = sorted(p for p in mem.glob("**/*.md")
                   if not p.name.startswith("_") and p.name not in vc.NON_NOTES
                   and ".cache" not in p.parts and "_seed" not in p.parts)
    if not notes:
        return ('<p class="empty">No authored notes yet. Run <code>/airx:memory</code> to capture a '
                'hot module — that is the day-1 win.</p>')
    cards = []
    for md in notes:
        meta, body = frontmatter(read(md))
        t, r, st, sr, sx, tbd = note_stats(repo, idx, md)
        # exclude external symbols (framework classes) from the denominator — verify-citations treats
        # them as advisory, not drift, so they must not turn the badge amber.
        ft = (t or 0) + (st or 0) - (sx or 0) if t is not None else None
        fr = (r or 0) + (sr or 0) if r is not None else None
        name = meta.get("name") or md.stem
        title = name.split("\n")[0].strip() or md.stem
        chips = [cite_badge(ft, fr)]
        if tbd:
            chips.append(badge(f"{tbd} TBD", "tbd-b"))
        status = meta.get("status")
        if status:
            chips.append(badge(status, "muted"))
        rows = "".join(
            f"<tr><th>{esc(k)}</th><td>{esc(meta[k])}</td></tr>"
            for k in ("type", "status", "last_verified", "code_ref", "owner", "updated_date")
            if meta.get(k))
        cards.append(
            f'<details class="card"><summary><span class="t">{esc(title)}</span>'
            f'<span class="path">{esc(md.relative_to(mem).as_posix())}</span>'
            f'<span class="chips">{"".join(chips)}</span></summary>'
            f'{f"<table class=meta>{rows}</table>" if rows else ""}'
            f'<pre class="body">{body_html(body)}</pre></details>')
    return "\n".join(cards)


def render_docs(docs_dir: Path) -> str:
    files = sorted(p for p in docs_dir.glob("*.md") if p.name != "README.md")
    readme = docs_dir / "README.md"
    if readme.is_file():
        files = [readme] + files
    cards = []
    for md in files:
        meta, body = frontmatter(read(md))
        title = (meta.get("name") or md.stem).split("\n")[0].strip()
        st = meta.get("status")
        chip = badge(st, "muted") if st else ""
        cards.append(
            f'<details class="card"><summary><span class="t">{esc(title)}</span>'
            f'<span class="path">{esc(md.name)}</span><span class="chips">{chip}</span></summary>'
            f'<pre class="body">{body_html(body)}</pre></details>')
    return "\n".join(cards)


def render_registry(reg_dir: Path) -> str:
    blocks = []
    for jf in sorted(reg_dir.glob("*.json")):
        try:
            data = json.loads(read(jf))
        except Exception:
            continue
        meta = data.get("_meta", {}) if isinstance(data, dict) else {}
        items = next((v for k, v in data.items() if k != "_meta" and isinstance(v, list)), []) \
            if isinstance(data, dict) else []
        sub = (f' · {meta.get("count", len(items))} items · code_ref '
               f'{esc(str(meta.get("code_ref", "TBD")))}') if meta else ""
        if not items:
            blocks.append(f'<h3>{esc(jf.stem)}<span class="sub">{sub}</span></h3>'
                          f'<p class="empty">empty registry</p>')
            continue
        cols = []
        for it in items:
            for k in it:
                if k not in cols:
                    cols.append(k)
        head = "".join(f"<th>{esc(c)}</th>" for c in cols)
        body = "".join(
            "<tr>" + "".join(f"<td>{esc(str(it.get(c, '')))}</td>" for c in cols) + "</tr>"
            for it in items)
        blocks.append(f'<h3>{esc(jf.stem)}<span class="sub">{sub}</span></h3>'
                      f'<table class="reg"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>')
    return "\n".join(blocks)


def score_headline(wiki: Path) -> str:
    """Compose score.py (don't re-derive the Coverage·Depth·Trust formula) — capture its text verbatim.
    score.py appends a row to score-trend.tsv on every run; the viewer must NOT author memory (it only
    reflects it — and the trend is meant to be per-COMMIT), so we snapshot and restore that file."""
    trend = wiki / "ai_memory" / ".cache" / "score-trend.tsv"
    saved = trend.read_text() if trend.is_file() else None
    try:
        r = subprocess.run([sys.executable, str(HERE / "score.py"), str(wiki)],
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout or "").strip()
        return esc(out) if out else "(score unavailable)"
    except Exception:
        return "(score unavailable)"
    finally:
        try:
            if saved is None:
                if trend.is_file():
                    trend.unlink()
            else:
                trend.write_text(saved)
        except Exception:
            pass


def trend_table(mem: Path) -> str:
    tsv = mem / ".cache" / "score-trend.tsv"
    if not tsv.is_file():
        return ""
    rows = [ln.split("\t") for ln in read(tsv).splitlines() if ln.strip()]
    rows = [r for r in rows if len(r) >= 5][-10:]
    if not rows:
        return ""
    body = "".join(
        f"<tr><td>{esc(r[0])}</td><td>{esc(r[1])}</td><td>{esc(r[2])}</td>"
        f"<td>{esc(r[3])}</td><td>{esc(r[4])}</td></tr>" for r in rows)
    return ('<h3>Score trend <span class="sub">last 10 runs</span></h3>'
            '<table class="reg"><thead><tr><th>when</th><th>overall</th><th>coverage</th>'
            f'<th>depth</th><th>trust</th></tr></thead><tbody>{body}</tbody></table>')


CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1f;--mut:#6b6b70;--line:#e6e6e3;--ok:#1a7f37;--warn:#b35900;--red:#b3261e;--card:#fff}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:var(--fg);background:var(--bg)}
.wrap{max-width:980px;margin:0 auto;padding:28px 20px 80px}
h1{font-size:22px;margin:0 0 2px}h2{font-size:16px;margin:34px 0 12px;padding-bottom:6px;border-bottom:1px solid var(--line)}
h3{font-size:14px;margin:20px 0 8px}.sub{color:var(--mut);font-weight:400;font-size:12px;margin-left:8px}
.lead{color:var(--mut);margin:0 0 18px;font-size:13px}
.headline{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.headline pre{margin:0;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;margin:8px 0;padding:0 14px}
.card[open]{padding-bottom:12px}summary{cursor:pointer;padding:12px 0;list-style:none;display:flex;flex-wrap:wrap;align-items:center;gap:8px}
summary::-webkit-details-marker{display:none}summary .t{font-weight:600}
.path{color:var(--mut);font:11.5px ui-monospace,Menlo,monospace}
.chips{margin-left:auto;display:flex;gap:6px;flex-wrap:wrap}
.badge{font-size:11px;padding:2px 8px;border-radius:999px;font-weight:600;white-space:nowrap}
.badge.ok{background:#e7f6ec;color:var(--ok)}.badge.warn{background:#fdf0e3;color:var(--warn)}
.badge.muted{background:#f0f0ee;color:var(--mut)}.badge.tbd-b{background:#fbe9e7;color:var(--red)}
table.meta{border-collapse:collapse;margin:4px 0 10px;font-size:12.5px}
table.meta th{text-align:left;color:var(--mut);font-weight:500;padding:2px 14px 2px 0;vertical-align:top}
pre.body{background:#f7f7f5;border:1px solid var(--line);border-radius:8px;padding:12px;overflow:auto;white-space:pre-wrap;font:12.5px/1.55 ui-monospace,Menlo,monospace}
.cite{color:var(--ok);font-weight:600}.tbd{color:var(--red);font-weight:700}
table.reg{border-collapse:collapse;width:100%;font-size:12.5px;margin:4px 0}
table.reg th,table.reg td{border:1px solid var(--line);padding:5px 9px;text-align:left;vertical-align:top}
table.reg thead th{background:#f4f4f2}
.empty{color:var(--mut);font-size:13px;font-style:italic}
code{font:12.5px ui-monospace,Menlo,monospace;background:#f0f0ee;padding:1px 5px;border-radius:4px}
footer{margin-top:46px;color:var(--mut);font-size:12px;border-top:1px solid var(--line);padding-top:14px}
"""


def build_html(wiki: Path) -> str:
    repo = vc.repo_from_manifest(wiki)
    mem = wiki / "ai_memory"
    idx = None
    if repo is not None and repo.is_dir() and mem.is_dir():
        try:
            idx = vc.build_index(repo, cache_dir=mem / ".cache")
        except Exception:
            idx = None

    parts = [f'<!doctype html><html lang="en"><head><meta charset="utf-8">',
             f'<meta name="viewport" content="width=device-width,initial-scale=1">',
             f'<title>airx view — {esc(wiki.name)}</title><style>{CSS}</style></head><body><div class="wrap">']
    repo_lbl = esc(str(repo)) if repo else "TBD (no resolvable repo_path)"
    parts.append(f'<h1>airx view <span class="sub">{esc(wiki.name)}</span></h1>')
    parts.append(f'<p class="lead">repo: <code>{repo_lbl}</code> · generated {date.today().isoformat()} '
                 f'· static, no-server · regenerate with <code>/airx:view</code></p>')

    # Quality headline — composes score.py + the trend tsv. Always shown (memory is the entry layer).
    parts.append('<h2>Quality — Coverage · Depth · Trust</h2>')
    parts.append(f'<div class="headline"><pre>{score_headline(wiki)}</pre></div>')
    tt = trend_table(mem)
    if tt:
        parts.append(tt)

    # Memory (entry layer — always a section; empty-state nudge if no notes).
    parts.append('<h2>Memory <span class="sub">ai_memory/</span></h2>')
    parts.append(render_notes(mem, repo, idx) if mem.is_dir()
                 else '<p class="empty">No ai_memory/ — run <code>/airx:init</code> first.</p>')

    # Optional layers: render ONLY if present on disk (no layer stamped empty by default).
    docs_dir = wiki / "ai_documentation"
    if docs_dir.is_dir() and any(docs_dir.glob("*.md")):
        parts.append('<h2>Documentation <span class="sub">ai_documentation/</span></h2>')
        parts.append(render_docs(docs_dir))

    reg_dir = wiki / "ai_knowledge_base" / "registry"
    if reg_dir.is_dir() and any(reg_dir.glob("*.json")):
        parts.append('<h2>Knowledge base <span class="sub">ai_knowledge_base/registry/</span></h2>')
        parts.append(render_registry(reg_dir))

    parts.append('<footer>Generated by <code>airx view</code> — deterministic, stdlib-only, no LLM. '
                 'Citations highlighted <span class="cite">green</span>; gaps shown as '
                 '<span class="tbd">TBD</span>. A static file: no server, no port.</footer>')
    parts.append('</div></body></html>')
    return "\n".join(parts)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: view.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2
    out = wiki / "ai_view.html"
    out.write_text(build_html(wiki))
    try:                                                     # it's a regenerable artifact — keep the tree clean
        init.update_gitignore(wiki, ["ai_view.html"])
    except Exception:
        pass
    print(f"airx view ✓  {out}")
    print(f"  open it:  file://{out}")
    print("  static, no-server · regenerate anytime with /airx:view")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
