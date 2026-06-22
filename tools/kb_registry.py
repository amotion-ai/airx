#!/usr/bin/env python3
"""airx kb_registry — deterministic Java registry generator (the opt-in token-lever KB layer).

Scans a target Spring/JPA repo's *.java files (regex-light, NO LLM) and emits per-stack registries
under <wiki>/ai_knowledge_base/registry/:

  endpoints.json — @RestController/@Controller classes + their @*Mapping HTTP paths
  entities.json  — @Entity classes (+ @Table name)
  services.json  — @Service/@Component beans (+ explicit bean id)

Each file is a JSON envelope:
  {"_meta": {generated, code_ref, generator:"airx kb_registry", source:"auto-generated", count}, "<items>": [...]}

Deterministic by design: regenerate, never hand-edit. This is OPT-IN — it only runs when invoked, and is
justified per-repo by /airx:benchmark (the KB win = fewer tokens per lookup than grepping the source).

    python3 kb_registry.py <wiki-dir>

The wiki's .ai-readiness.yml supplies target.repo_path (resolved relative to the wiki) and target.code_ref.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

# Reuse init.py's skip style: never walk build output, VCS, tooling, or the airx layers themselves.
_IGNORE_DIRS = {".git", ".github", ".idea", ".vscode", ".mvn", ".gradle", "target", "build", "dist",
                "out", "bin", "node_modules", "__pycache__", "venv", ".venv", "ai_memory",
                "ai_documentation", "ai_knowledge_base"}

GENERATOR = "airx kb_registry"

# --- regexes (compiled once; deliberately conservative — match the common Spring/JPA shapes) ----------
# Annotation with an optional argument list, capturing the raw args, e.g. @RequestMapping("/x"), @Service("id").
_CLASS_RE = re.compile(r"\b(?:class|interface|enum)\s+([A-Za-z_$][\w$]*)")
_REST_RE = re.compile(r"@(RestController|Controller)\b")
_ENTITY_RE = re.compile(r"@Entity\b")
_SERVICE_RE = re.compile(r"@(Service|Component)\b(?:\s*\(([^)]*)\))?")
_TABLE_RE = re.compile(r"@Table\b\s*\(([^)]*)\)")
_MAPPING_RE = re.compile(r"@(Get|Post|Put|Delete|Patch|Request)Mapping\b(?:\s*\(([^)]*)\))?")
# A double-quoted string literal (first one in an annotation's args is the path / id).
_STR_RE = re.compile(r'"([^"]*)"')
# value = "..."  /  path = "..."  /  name = "..."  (named annotation attributes)
_ATTR_RE = re.compile(r'(\w+)\s*=\s*"([^"]*)"')

_HTTP = {"Get": "GET", "Post": "POST", "Put": "PUT", "Delete": "DELETE", "Patch": "PATCH",
         "Request": "ANY"}

# --- JAX-RS (Jersey / RESTEasy / CXF) — the legacy-Java REST style (e.g. Apache Fineract). The HTTP verb
# and the path are SEPARATE adjacent annotations: `@GET @Path("/{id}")` (in either order). -------------
_JAXRS_VERB_RE = re.compile(r"@(GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH)\b")
_JAXRS_PATH_RE = re.compile(r'@Path\b\s*\(\s*"([^"]*)"')

# --- entity-engine XML (Apache OFBiz & similar) — entities/services declared in XML, not JPA/Spring
# annotations: <entity entity-name="X" table-name="Y">, <service name="..." engine="..." invoke="...">. ---
_XATTR_RE = re.compile(r'([\w.-]+)\s*=\s*"([^"]*)"')          # hyphen-aware XML attribute reader
# (?=[\s>]) so the tag name must end here — `<entity ` matches but `<entity-one`/`<service-group` do NOT
# (OFBiz has many `<entity-*>` reference tags that would otherwise be miscounted as definitions).
_ENTITY_XML_TAG = re.compile(r"<(entity|view-entity)(?=[\s>])([^>]*)>", re.I)
_SERVICE_XML_TAG = re.compile(r"<service(?=[\s>])([^>]*)>", re.I)


def parse_manifest(wiki: Path) -> dict:
    """Flat key:value read of .ai-readiness.yml (same shape init.py writes / check.py reads)."""
    out: dict[str, str] = {}
    f = wiki / ".ai-readiness.yml"
    if f.is_file():
        for line in f.read_text(errors="ignore").splitlines():
            m = re.match(r"^\s*([a-z_]+):\s*(\S.*)$", line)
            if m:
                out[m.group(1)] = m.group(2).strip()
    return out


def iter_java(repo: Path):
    """Walk repo for *.java, skipping build/VCS/airx dirs (init.py style, one pass)."""
    stack = [repo]
    while stack:
        d = stack.pop()
        try:
            for p in d.iterdir():
                if p.is_dir():
                    if p.name not in _IGNORE_DIRS and not p.name.startswith("."):
                        stack.append(p)
                elif p.suffix == ".java":
                    yield p
        except OSError:
            continue


def _first_string(args: str | None) -> str:
    """First quoted literal in an annotation arg list (the positional value), or ""."""
    if not args:
        return ""
    m = _STR_RE.search(args)
    return m.group(1) if m else ""


def _attr(args: str | None, *names: str) -> str:
    """Value of the first matching named attribute (value=/path=/name=), or the positional string."""
    if not args:
        return ""
    found = {k: v for k, v in _ATTR_RE.findall(args)}
    for n in names:
        if n in found:
            return found[n]
    # positional form, e.g. @Service("id") or @RequestMapping("/x") — but only if not a named attr.
    if "=" not in args:
        return _first_string(args)
    return ""


def _join(base: str, leaf: str) -> str:
    """Join a class-level base path with a method path into one HTTP path."""
    b, l = base.strip("/"), leaf.strip("/")
    if not b:
        return "/" + l
    if not l:
        return "/" + b
    return "/" + b + "/" + l


def scan_file(path: Path, rel: str, endpoints: list, entities: list, services: list) -> None:
    try:
        text = path.read_text(errors="ignore")
    except OSError:
        return
    cm = _CLASS_RE.search(text)
    cls = cm.group(1) if cm else path.stem

    is_spring = bool(_REST_RE.search(text))
    if is_spring:
        # A class-level @RequestMapping (the first @*Mapping, sitting above the class declaration)
        # sets the base path and is NOT itself an endpoint.
        rm = _MAPPING_RE.search(text)
        base = ""
        base_at = -1
        cls_at = cm.start() if cm else len(text)
        if rm and rm.group(1) == "Request" and rm.start() < cls_at:
            base = _attr(rm.group(2), "value", "path")
            base_at = rm.start()
        seen = set()
        for m in _MAPPING_RE.finditer(text):
            verb, args = m.group(1), m.group(2)
            if m.start() == base_at:
                continue  # the class-level @RequestMapping is the base, not an endpoint
            leaf = _attr(args, "value", "path")
            http = _HTTP.get(verb, "ANY")
            full = _join(base, leaf)
            key = (http, full)
            if key in seen:
                continue
            seen.add(key)
            endpoints.append({"class": cls, "method": http, "path": full, "file": rel,
                              "framework": "spring-mvc"})
    elif _JAXRS_VERB_RE.search(text) or _JAXRS_PATH_RE.search(text):
        # JAX-RS: class-level @Path (before the class decl) is the base; each HTTP-verb annotation is an
        # endpoint, with its path taken from the nearest @Path within a small window (verb & @Path stack).
        cls_at = cm.start() if cm else len(text)
        base, base_at = "", -1
        pm = _JAXRS_PATH_RE.search(text)
        if pm and pm.start() < cls_at:
            base, base_at = pm.group(1), pm.start()
        seen = set()
        for m in _JAXRS_VERB_RE.finditer(text):
            verb = m.group(1)
            win_start = max(0, m.start() - 160)
            window = text[win_start: m.start() + 160]
            leaf = ""
            for pmm in _JAXRS_PATH_RE.finditer(window):
                if win_start + pmm.start() != base_at:   # skip the class-level @Path (the base)
                    leaf = pmm.group(1)
                    break
            full = _join(base, leaf)
            key = (verb, full)
            if key in seen:
                continue
            seen.add(key)
            endpoints.append({"class": cls, "method": verb, "path": full, "file": rel,
                              "framework": "jax-rs"})

    if _ENTITY_RE.search(text):
        tm = _TABLE_RE.search(text)
        table = _attr(tm.group(1), "name") if tm else ""
        entities.append({"class": cls, "table": table, "file": rel, "source": "jpa"})

    sm = _SERVICE_RE.search(text)
    if sm:
        bean_id = _attr(sm.group(2), "value", "name")
        services.append({"id": bean_id, "class": cls, "file": rel, "source": "spring-bean"})


def iter_xml(repo: Path):
    """Walk repo for entity-engine XML (entitymodel*.xml / services*.xml), skipping build/VCS/airx dirs."""
    stack = [repo]
    while stack:
        d = stack.pop()
        try:
            for p in d.iterdir():
                if p.is_dir():
                    if p.name not in _IGNORE_DIRS and not p.name.startswith("."):
                        stack.append(p)
                elif p.suffix == ".xml" and ("entitymodel" in p.name or "services" in p.name):
                    yield p
        except OSError:
            continue


def scan_entity_engine(repo: Path, entities: list, services: list) -> int:
    """Extract OFBiz-style entity-engine declarations from XML (no JPA/Spring annotations). Returns the
    number of XML files scanned. <entity entity-name=.. table-name=..>, <service name=.. engine=.. invoke=..>."""
    n = 0
    for p in iter_xml(repo):
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        n += 1
        rel = p.relative_to(repo).as_posix()
        if "entitymodel" in p.name:
            for m in _ENTITY_XML_TAG.finditer(text):
                attrs = dict(_XATTR_RE.findall(m.group(2)))
                name = attrs.get("entity-name")
                if name:
                    entities.append({"class": name, "table": attrs.get("table-name", ""),
                                     "file": rel, "source": "entity-engine"})
        if "services" in p.name:
            for m in _SERVICE_XML_TAG.finditer(text):
                attrs = dict(_XATTR_RE.findall(m.group(1)))
                name = attrs.get("name")
                # OFBiz service-engine signature (engine=/invoke=/location=) — avoids matching unrelated
                # <service> tags (e.g. Spring/SCA bean files) that happen to be named services*.xml.
                if name and (attrs.keys() & {"engine", "invoke", "location"}):
                    services.append({"id": name, "class": attrs.get("location", ""),
                                     "file": rel, "source": "service-engine",
                                     "invoke": attrs.get("invoke", "")})
    return n


def envelope(items: list, key: str, code_ref: str, generated: str) -> dict:
    return {
        "_meta": {
            "generated": generated,
            "code_ref": code_ref,
            "generator": GENERATOR,
            "source": "auto-generated",
            "count": len(items),
        },
        key: items,
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: kb_registry.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2

    man = parse_manifest(wiki)
    if not man:
        print(f"error: {wiki} is not an airx wiki (no .ai-readiness.yml). Run /airx:init first — "
              f"refusing to scaffold/scan an unconfirmed directory.", file=sys.stderr)
        return 2
    rp = man.get("repo_path", ".")
    if rp == "TBD" or not rp:
        rp = "."
    repo = Path(rp) if Path(rp).is_absolute() else (wiki / rp).resolve()
    if not repo.is_dir():
        print(f"error: target repo {repo} (from .ai-readiness.yml repo_path) not found", file=sys.stderr)
        return 2
    code_ref = man.get("code_ref", "TBD") or "TBD"
    generated = date.today().isoformat()

    endpoints: list[dict] = []
    entities: list[dict] = []
    services: list[dict] = []
    n_files = 0
    for p in iter_java(repo):  # ONE walk
        n_files += 1
        rel = p.relative_to(repo).as_posix()
        scan_file(p, rel, endpoints, entities, services)

    # second pass: entity-engine XML (OFBiz & similar) — for repos that declare entities/services in XML.
    n_xml = scan_entity_engine(repo, entities, services)

    endpoints.sort(key=lambda e: (e["class"], e["path"], e["method"]))
    entities.sort(key=lambda e: e["class"])
    services.sort(key=lambda e: (e["class"]))

    out_dir = wiki / "ai_knowledge_base" / "registry"
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "endpoints.json": ("endpoints", endpoints),
        "entities.json": ("entities", entities),
        "services.json": ("services", services),
    }
    for fname, (key, items) in files.items():
        (out_dir / fname).write_text(
            json.dumps(envelope(items, key, code_ref, generated), indent=2) + "\n")

    def _by_fw(items, field, key):
        from collections import Counter
        c = Counter(i.get(field, "?") for i in items)
        return "  ".join(f"{c[k]} {k}" for k in sorted(c)) if items else ""

    print(f"airx kb_registry ✓  {out_dir}  (code_ref={code_ref})")
    print(f"  scanned {n_files} *.java + {n_xml} entity-engine *.xml file(s) under {repo}")
    ep = _by_fw(endpoints, "framework", "method")
    print(f"  endpoints.json : {len(endpoints)} HTTP endpoints" + (f"  ({ep})" if ep else ""))
    en = _by_fw(entities, "source", "class")
    print(f"  entities.json  : {len(entities)} entities" + (f"  ({en})" if en else ""))
    sv = _by_fw(services, "source", "class")
    print(f"  services.json  : {len(services)} services/beans" + (f"  ({sv})" if sv else ""))
    if not endpoints and not entities and not services:
        print("  note: 0 found — this generator covers Spring-MVC/JAX-RS + JPA/entity-engine. This repo may "
              "use another stack (JSF/Struts/MyBatis); memory still applies — only the KB lever is per-stack.")
    print()
    print("  This is the OPT-IN KB layer (the per-stack token-lever). Deterministic:")
    print("  regenerate, never hand-edit. Prove the per-query token win on THIS repo with /airx:benchmark.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
