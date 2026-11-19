#!/usr/bin/env python3
"""Citation ledger for grounded answers and documents.

Owns the ``url -> [n]`` mapping used by the ``grounded-citations`` skill.
Ids are assigned at retrieval time and never change, so a draft's ``[3]``
always resolves to the same page.  The model only ever emits integers the
ledger handed it, which is what makes the citations verifiable.

Subcommands
-----------
  reset                            start a clean ledger
  add URL [URL ...]                register source(s), print their ids
  ingest FILE|-                    register every url found in JSON tool output
  quote ID --text T --from FILE|-  attach verbatim supporting evidence to a source
  list                             show the ledger
  render                           render a Sources block
  verify DRAFT                     check a draft's citations against the ledger

Fact-checking is evidence-backed citation: ``quote`` only accepts text that
literally appears in the fetched page text you point it at, ``verify
--evidence`` requires every cited source to carry at least one such quote, and
``render --style evidence`` prints the quotes under each source so the reader
can check the chain themselves.  Claims from model knowledge are declared with
an ``[unverified]`` marker rather than silently blended in.

Ledger path resolution (first wins):
  --ledger PATH        (before or after the subcommand)
  $SOURCES_LEDGER
  $HERMES_CITATION_LEDGER
  $HERMES_HOME/cache/citations/ledger.json

A per-document ledger (``--ledger out/.sources-<slug>-<date>.json``) needs no
``reset``: ``add`` creates it on first use.

``verify`` reports every problem with its draft line number and the offending
sentence, so a revision loop can fix it mechanically:
  - FAIL  ``[n]`` cited in prose but absent from the ledger (orphan citation)
  - FAIL  ``[[CITE_n]]`` placeholder left over from a protected rewrite pass
  - FAIL  ledger source never cited (only with ``--require-all-cited``;
          otherwise a warning)
  - warn  sentence with a statistic (percent, currency, magnitude, multiplier)
          but no ``[n]`` (a failure under ``--strict``)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _hermes_home import get_hermes_home  # noqa: E402

SCHEMA_VERSION = 1

# A citation marker in prose: [12].  Markdown links ([text](url)) and
# reference-style labels are excluded by requiring digits only and no
# following "(" or ":".
_CITE_RE = re.compile(r"\[(\d{1,4})\](?![(:])")
_SOURCES_HEADER_RE = re.compile(r"^\s*(?:#{1,6}\s*)?(?:\*\*)?sources:?(?:\*\*)?\s*$", re.IGNORECASE)
_SOURCE_LINE_RE = re.compile(r"^\s*\[(\d{1,4})\]\s*[-–:]?\s*(\S+)")
_URL_IN_TEXT_RE = re.compile(r"https?://[^\s\"'<>)\]}]+")
_FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
# Explicit declaration that a claim comes from model knowledge, not a source.
_UNVERIFIED_RE = re.compile(r"\[unverified\]", re.IGNORECASE)
# Placeholder a rewrite pass (e.g. humanizer) wraps citations in so it cannot
# drop or renumber them.  Must be restored to ``[n]`` before verify.
_CITE_TOKEN_RE = re.compile(r"\[\[CITE_(\d{1,4})\]\]")
_FRONTMATTER_RE = re.compile(r"^---\s*$")

# Statistic detectors for the uncited-number check.  Deliberately skip bare
# integers so years (2025), versions (GPT-4, Python 3.12) and list numbering
# never trip it; a number only counts when it carries a statistic's shape.
_NUM = r"\d(?:[\d.,]*\d)?"
_STAT_RES = (
    # 42%, 4.5 %, 30 percent, 30 persen
    re.compile(rf"{_NUM}\s?(?:%|percent\b|per cent\b|persen\b)", re.IGNORECASE),
    # $5, US$ 1.2, € 30, £4, Rp 15.000, Rp15jt, IDR 2.000
    re.compile(rf"(?:US\$|[$€£¥₹]|\bRp\.?|\bIDR|\bUSD|\bEUR)\s?{_NUM}"),
    # 1,200 USD, 300 dollars, 5000 rupiah
    re.compile(rf"{_NUM}\s?(?:USD|EUR|IDR|dollars?|euros?|rupiah)\b", re.IGNORECASE),
    # 3 million, 1.2 billion, 40 juta, 2 miliar.  Bare 70B / 3M are skipped:
    # they are as often model sizes and names as metrics ($1.5B is still caught).
    re.compile(
        rf"{_NUM}\s?(?:thousand|million|billion|trillion|ribu|juta|jt|miliar|milyar|triliun)\b",
        re.IGNORECASE,
    ),
    # 3x faster, 10× more
    re.compile(rf"{_NUM}\s?[x×](?![\w])"),
    # grouped thousands: 12,000 / 1,250,000 / 12.000 (id-ID)
    re.compile(r"(?<![\w.,])\d{1,3}(?:,\d{3})+(?![\d,])|(?<![\w.,])\d{1,3}(?:\.\d{3})+(?![\d.])"),
)
# Text that must not count as a statistic: citation markers, links, code.
_STAT_NOISE_RE = re.compile(r"\[\d{1,4}\]|\[\[CITE_\d{1,4}\]\]|https?://\S+|`[^`]*`|\]\([^)]*\)")


# ---------------------------------------------------------------------------
# Ledger I/O
# ---------------------------------------------------------------------------


def resolve_ledger_path(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit).expanduser()
    for var in ("SOURCES_LEDGER", "HERMES_CITATION_LEDGER"):
        env = os.environ.get(var, "").strip()
        if env:
            return Path(env).expanduser()
    return get_hermes_home() / "cache" / "citations" / "ledger.json"


def normalize_url(url: str) -> str:
    """Canonicalize a URL for ledger identity.

    Strips the fragment and a trailing slash so ``/page``, ``/page/`` and
    ``/page#section`` are one source.  Query strings are significant and are
    kept — they usually select different content.
    """
    u = (url or "").strip()
    if "#" in u:
        u = u.split("#", 1)[0]
    stripped = u.rstrip("/")
    return stripped or u


def load_ledger(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": SCHEMA_VERSION, "sources": []}
    try:
        raw = path.read_text(encoding="utf-8")
        # A zero-byte file (e.g. from mktemp/touch) is a fresh ledger, not damage.
        if not raw.strip():
            return {"version": SCHEMA_VERSION, "sources": []}
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"error: ledger at {path} is unreadable ({exc}); run `reset` to start over")
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise SystemExit(f"error: ledger at {path} has an unexpected shape; run `reset`")
    return data


def save_ledger(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


class _LedgerLock:
    """Best-effort cross-process lock (O_EXCL lockfile, stdlib only).

    Parallel subagents can share one ledger via --ledger; without a lock two
    concurrent ``add`` calls can assign the same id.  Falls through after the
    timeout rather than blocking a task forever — a stale lock must never
    wedge the ledger.
    """

    def __init__(self, path: Path, timeout: float = 5.0) -> None:
        self.lock_path = path.with_suffix(path.suffix + ".lock")
        self.timeout = timeout
        self.fd: int | None = None

    def __enter__(self) -> "_LedgerLock":
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            try:
                self.fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                return self
            except FileExistsError:
                if time.monotonic() >= deadline:
                    # Assume a stale lock from a crashed run.
                    try:
                        self.lock_path.unlink()
                    except OSError:
                        return self
                    continue
                time.sleep(0.05)

    def __exit__(self, *_exc: object) -> None:
        if self.fd is not None:
            try:
                os.close(self.fd)
            except OSError:
                pass
        try:
            self.lock_path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------


def _by_url(sources: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {s["url"]: s for s in sources}


def add_sources(
    path: Path,
    urls: Iterable[str],
    title: str | None = None,
    accessed: str | None = None,
) -> list[dict[str, Any]]:
    """Register urls, returning their ledger entries (existing or new)."""
    urls = [u for u in (str(u).strip() for u in urls) if u]
    if not urls:
        return []
    with _LedgerLock(path):
        data = load_ledger(path)
        sources = data["sources"]
        index = _by_url(sources)
        out: list[dict[str, Any]] = []
        changed = False
        for raw in urls:
            key = normalize_url(raw)
            existing = index.get(key)
            if existing is not None:
                if title and not existing.get("title"):
                    existing["title"] = title
                    changed = True
                out.append(existing)
                continue
            entry = {
                "id": len(sources) + 1,
                "url": key,
                "title": (title or "").strip(),
                "accessed": accessed or time.strftime("%Y-%m-%d"),
            }
            sources.append(entry)
            index[key] = entry
            out.append(entry)
            changed = True
        if changed:
            save_ledger(path, data)
    return out


def urls_from_json(payload: Any) -> list[tuple[str, str]]:
    """Walk arbitrary JSON tool output collecting (url, title) pairs.

    Handles web_search (``data.web[]``), web_extract (``results[]``) and any
    other nesting, in document order, deduped.
    """
    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            url = node.get("url") or node.get("link") or node.get("source_url")
            if isinstance(url, str) and url.startswith(("http://", "https://")):
                key = normalize_url(url)
                if key not in seen:
                    seen.add(key)
                    raw_title = node.get("title") or node.get("name") or ""
                    found.append((url, raw_title if isinstance(raw_title, str) else ""))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


# ---------------------------------------------------------------------------
# Evidence quotes (fact-checking)
# ---------------------------------------------------------------------------


def _normalize_ws(text: str) -> str:
    """Collapse all whitespace runs to single spaces for verbatim matching."""
    return " ".join((text or "").split())


# Markdown artifacts that retrieval tools inject into otherwise-identical prose.
# ``web_extract`` returns markdown, so the most citation-worthy sentences are
# exactly the ones carrying inline links and emphasis around terms:
#   "including _[ERAP1](https://…/erap1/)_, _[IL1A](…)_, have also been…"
# reads identically to the page a human sees.  Matching has to see through that
# markup, or the skill pushes the agent toward weaker evidence fragments.
_MD_LINK_RE = re.compile(r"\[([^\]]*)\]\((?:[^()\s]|\([^()]*\))*\)")
_MD_NOISE_RE = re.compile(r"[*_`~]|\\(?=[^\w\s])")


def _match_key(text: str) -> str:
    """Canonicalize text for verbatim comparison.

    Whitespace-, case-, and markdown-insensitive: inline links collapse to
    their label, emphasis/code markers and backslash escapes are dropped.  The
    stored quote keeps whatever the caller passed, so the rendered evidence
    block shows clean prose rather than extractor artifacts.
    """
    collapsed = _MD_LINK_RE.sub(r"\1", text or "")
    return _normalize_ws(_MD_NOISE_RE.sub("", collapsed)).casefold()


def quote_in_evidence(quote: str, evidence: str) -> bool:
    """True when ``quote`` appears verbatim in the fetched ``evidence`` text,
    ignoring whitespace, case, and markdown markup on either side."""
    q = _match_key(quote)
    return bool(q) and q in _match_key(evidence)


def attach_quote(path: Path, source_id: int, quote: str, evidence: str) -> dict[str, Any]:
    """Attach a verbatim quote to a ledger entry after checking it against
    the evidence text.  Raises SystemExit on unknown id or non-verbatim text —
    a quote the page does not contain is exactly the fabrication this guards
    against."""
    quote = (quote or "").strip()
    if len(_normalize_ws(quote).split()) < 3:
        raise SystemExit("error: quote too short — use at least 3 words of verbatim text")
    if not quote_in_evidence(quote, evidence):
        raise SystemExit(
            "error: quote not found verbatim in the evidence text — "
            "copy the exact wording from the fetched page, do not paraphrase"
        )
    with _LedgerLock(path):
        data = load_ledger(path)
        entry = next((s for s in data["sources"] if s["id"] == source_id), None)
        if entry is None:
            raise SystemExit(f"error: no source [{source_id}] in the ledger")
        quotes = entry.setdefault("quotes", [])
        norm = _match_key(quote)
        if not any(_match_key(q.get("text", "")) == norm for q in quotes):
            quotes.append({"text": quote, "added": time.strftime("%Y-%m-%d")})
            save_ledger(path, data)
    return entry


def render_sources(
    sources: list[dict[str, Any]],
    style: str = "markdown",
    only: set[int] | None = None,
) -> str:
    picked = [s for s in sources if only is None or s["id"] in only]
    picked.sort(key=lambda s: s["id"])
    if not picked:
        return ""
    lines: list[str] = []
    if style == "bibtex":
        for s in picked:
            key = f"source{s['id']}"
            title = s.get("title") or s["url"]
            lines.append(
                "@misc{%s,\n  title = {%s},\n  howpublished = {\\url{%s}},\n  note = {Accessed %s}\n}"
                % (key, title, s["url"], s.get("accessed", ""))
            )
        return "\n".join(lines)
    if style == "footnotes":
        for s in picked:
            title = s.get("title")
            suffix = f" — {title}" if title else ""
            lines.append(f"[^{s['id']}]: {s['url']}{suffix}")
        return "\n".join(lines)
    header = "Sources:" if style == "plain" else "## Sources"
    lines.append(header)
    if style != "plain":
        lines.append("")
    for s in picked:
        title = s.get("title")
        suffix = f" — {title}" if title else ""
        lines.append(f"[{s['id']}] {s['url']}{suffix}")
        if style == "evidence":
            for q in s.get("quotes", []):
                lines.append(f'    > "{q.get("text", "")}"')
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def _body_lines(text: str) -> tuple[list[tuple[int, str]], dict[int, str]]:
    """Split a draft into (numbered body lines, sources_block_map).

    The sources block is everything after the last ``Sources`` header; its
    ``[n] url`` lines are parsed out so they aren't counted as prose citations.
    A leading YAML frontmatter block, fenced code blocks and HTML comments are
    dropped from the body.  Line numbers are 1-based draft line numbers.
    """
    lines = text.splitlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if _SOURCES_HEADER_RE.match(line):
            header_idx = i
    listed: dict[int, str] = {}
    if header_idx >= 0:
        for line in lines[header_idx + 1:]:
            m = _SOURCE_LINE_RE.match(line)
            if m:
                url_match = _URL_IN_TEXT_RE.search(line)
                listed[int(m.group(1))] = url_match.group(0) if url_match else m.group(2)
        end = header_idx
    else:
        end = len(lines)
    start = 0
    if lines and _FRONTMATTER_RE.match(lines[0]):
        for j in range(1, end):
            if _FRONTMATTER_RE.match(lines[j]):
                start = j + 1
                break
    body: list[tuple[int, str]] = []
    in_fence = False
    in_comment = False
    for i in range(start, end):
        line = lines[i]
        if not in_comment and _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # Drop HTML comments (template instructions), possibly multi-line.
        kept = ""
        rest = line
        while rest:
            if in_comment:
                close = rest.find("-->")
                if close < 0:
                    rest = ""
                else:
                    in_comment = False
                    rest = rest[close + 3:]
            else:
                open_ = rest.find("<!--")
                if open_ < 0:
                    kept += rest
                    rest = ""
                else:
                    kept += rest[:open_]
                    in_comment = True
                    rest = rest[open_ + 4:]
        body.append((i + 1, kept))
    return body, listed


def _split_draft(text: str) -> tuple[str, dict[int, str]]:
    """Split a draft into (prose, sources_block_map); see ``_body_lines``."""
    body, listed = _body_lines(text)
    return "\n".join(line for _, line in body), listed


def _strip_sources_block(text: str) -> str:
    """Return the draft with its trailing Sources block removed.

    Everything from the last Sources header onward goes; a draft with no such
    header is returned unchanged.  This is what makes ``render --replace-in``
    idempotent instead of stacking duplicate blocks.
    """
    lines = text.splitlines()
    header_idx = -1
    for i, line in enumerate(lines):
        if _SOURCES_HEADER_RE.match(line):
            header_idx = i
    if header_idx < 0:
        return text
    return "\n".join(lines[:header_idx])


_LIST_ITEM_RE = re.compile(r"^(?:[-*+]|\d{1,3}[.)])\s+")
# Sentence end: terminal punctuation, then any trailing citation markers, then
# whitespace or end of text.  "fact.[1] Next" splits after "[1]", so a
# citation stays with the sentence it supports.
_SENT_END_RE = re.compile(r"[.!?]+(?:\[\d{1,4}\]|\[\[CITE_\d{1,4}\]\])*(?=\s|$)")
_ABBREV = {"e.g", "i.e", "vs", "etc", "dr", "mr", "mrs", "ms", "no", "dll", "dsb", "dst", "yth", "approx", "ca"}


def _units(body: list[tuple[int, str]]) -> list[tuple[int, str, str]]:
    """Group body lines into located units: (line, text, kind).

    ``kind`` is ``heading``, ``table`` or ``prose``.  Prose lines are joined
    into paragraphs (a list item or blockquote line starts a new one) and split
    into sentences; each sentence carries the draft line it starts on.
    """
    units: list[tuple[int, str, str]] = []
    para: list[tuple[int, str]] = []

    def flush() -> None:
        if not para:
            return
        text = ""
        offsets: list[tuple[int, int]] = []  # (char offset, line number)
        for ln, seg in para:
            if text:
                text += " "
            offsets.append((len(text), ln))
            text += seg
        para.clear()

        def line_at(pos: int) -> int:
            ln = offsets[0][1]
            for off, num in offsets:
                if off <= pos:
                    ln = num
            return ln

        start = 0
        for m in _SENT_END_RE.finditer(text):
            prev_word = text[start:m.start()].rsplit(None, 1)[-1:] or [""]
            if prev_word[0].casefold().rstrip(".") in _ABBREV:
                continue
            chunk = text[start:m.end()]
            lead = len(chunk) - len(chunk.lstrip())
            if chunk.strip():
                units.append((line_at(start + lead), chunk.strip(), "prose"))
            start = m.end()
        tail = text[start:]
        if tail.strip():
            lead = len(tail) - len(tail.lstrip())
            units.append((line_at(start + lead), tail.strip(), "prose"))

    for ln, line in body:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("#"):
            flush()
            units.append((ln, stripped, "heading"))
            continue
        if stripped.startswith("|"):
            flush()
            units.append((ln, stripped, "table"))
            continue
        if stripped.startswith(">"):
            flush()
            stripped = stripped.lstrip("> ").strip()
        elif _LIST_ITEM_RE.match(stripped):
            flush()
            stripped = _LIST_ITEM_RE.sub("", stripped, count=1)
        if stripped:
            para.append((ln, stripped))
    flush()
    return units


def _has_statistic(sentence: str) -> bool:
    """True when the sentence states a number in a statistic's shape."""
    text = _STAT_NOISE_RE.sub(" ", sentence)
    return any(r.search(text) for r in _STAT_RES)


def _sentences(prose: str) -> list[str]:
    """Prose sentences of at least 4 words (headings and tables skipped)."""
    body = [(i + 1, line) for i, line in enumerate(prose.splitlines())]
    return [t for _, t, kind in _units(body) if kind == "prose" and len(t.split()) >= 4]


def _clip(text: str, limit: int = 240) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def verify_draft(
    draft_path: Path,
    sources: list[dict[str, Any]],
    strict: bool = False,
    min_coverage: float | None = None,
    require_evidence: bool = False,
    require_all_cited: bool = False,
) -> tuple[int, list[str], list[str]]:
    """Return (exit_code, errors, warnings).

    Line-level findings are formatted ``line N: <problem>: "<sentence>"`` so a
    revision loop can locate and fix each one.
    """
    text = draft_path.read_text(encoding="utf-8")
    body, listed = _body_lines(text)
    units = _units(body)
    by_id = {s["id"]: s for s in sources}

    errors: list[str] = []
    warnings: list[str] = []

    cited_set: set[int] = set()
    for ln, unit, _kind in units:
        for m in _CITE_RE.finditer(unit):
            sid = int(m.group(1))
            cited_set.add(sid)
            if sid not in by_id:
                errors.append(
                    f'line {ln}: orphan citation [{sid}] is not in the ledger '
                    f'(hallucinated or renumbered): "{_clip(unit)}"'
                )
        for m in _CITE_TOKEN_RE.finditer(unit):
            errors.append(
                f"line {ln}: unrestored placeholder [[CITE_{m.group(1)}]] — "
                f'turn it back into [{m.group(1)}]: "{_clip(unit)}"'
            )

    if cited_set and not listed:
        errors.append("draft cites sources but has no `Sources:` block — run `render --cited-in`")

    missing_from_block = sorted(cited_set - set(listed)) if listed else []
    if missing_from_block:
        errors.append(
            "cited but absent from the Sources block: "
            + ", ".join(f"[{i}]" for i in missing_from_block)
        )

    for sid, url in sorted(listed.items()):
        entry = by_id.get(sid)
        if entry is None:
            errors.append(f"Sources block lists [{sid}], which is not in the ledger")
            continue
        if normalize_url(url) != entry["url"]:
            errors.append(
                f"Sources block URL for [{sid}] does not match the ledger "
                f"(block: {url} / ledger: {entry['url']}) — re-run `render`"
            )

    extra_in_block = sorted(set(listed) - cited_set)
    if extra_in_block:
        warnings.append(
            "listed in Sources but never cited inline: "
            + ", ".join(f"[{i}]" for i in extra_in_block)
        )

    registered_uncited = sorted(set(by_id) - cited_set)
    if registered_uncited:
        if require_all_cited:
            for sid in registered_uncited:
                entry = by_id[sid]
                title = f" — {entry['title']}" if entry.get("title") else ""
                errors.append(
                    f"ledger source [{sid}] {entry['url']}{title} is never cited in the "
                    "draft — cite it where it supports or disputes a claim (e.g. as a "
                    "counter-source)"
                )
        else:
            warnings.append(
                "registered in the ledger but not cited in this draft: "
                + ", ".join(f"[{i}]" for i in registered_uncited)
            )

    for ln, unit, kind in units:
        if kind == "prose" and not _CITE_RE.search(unit) and _has_statistic(unit):
            # --strict promotes this to a failure; report it as one directly.
            (errors if strict else warnings).append(
                f'line {ln}: statistic without a [n] citation: "{_clip(unit)}"'
            )

    sentences = [u for _, u, kind in units if kind == "prose" and len(u.split()) >= 4]
    cited_sentences = [s for s in sentences if _CITE_RE.search(s)]
    unverified_sentences = [s for s in sentences if _UNVERIFIED_RE.search(s)]
    covered = [s for s in sentences if _CITE_RE.search(s) or _UNVERIFIED_RE.search(s)]
    coverage = (len(covered) / len(sentences)) if sentences else 0.0
    if min_coverage is not None and sentences and coverage < min_coverage:
        errors.append(
            f"citation coverage {coverage:.0%} is below the required {min_coverage:.0%} "
            f"({len(covered)}/{len(sentences)} sentences cited or marked [unverified])"
        )

    if require_evidence:
        unevidenced = sorted(
            i for i in cited_set if i in by_id and not by_id[i].get("quotes")
        )
        if unevidenced:
            errors.append(
                "cited sources carry no verbatim evidence quote (run `quote` with the "
                "fetched page text): " + ", ".join(f"[{i}]" for i in unevidenced)
            )

    over_cited = [s for s in sentences if len(_CITE_RE.findall(s)) > 3]
    if over_cited:
        warnings.append(f"{len(over_cited)} sentence(s) carry more than 3 citations")

    code = 1 if errors else (1 if (strict and warnings) else 0)
    quoted = sum(1 for s in sources if s.get("quotes"))
    stats = (
        f"{len(sentences)} prose sentence(s), {len(covered)} with declared provenance "
        f"({coverage:.0%}) — {len(cited_sentences)} cited, "
        f"{len(unverified_sentences)} marked [unverified] (a sentence may be both); "
        f"{len(cited_set)} distinct source(s) cited, "
        f"{len(by_id)} in ledger ({quoted} with evidence quotes)"
    )
    warnings.insert(0, f"stats: {stats}")
    return code, errors, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_only(spec: str | None) -> set[int] | None:
    if not spec:
        return None
    out: set[int] = set()
    for chunk in spec.replace(" ", "").split(","):
        if not chunk:
            continue
        if "-" in chunk:
            lo, _, hi = chunk.partition("-")
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(chunk))
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sources.py", description="Citation ledger for grounded answers and documents."
    )
    ledger_help = "ledger file path (overrides $SOURCES_LEDGER / $HERMES_CITATION_LEDGER / default)"
    parser.add_argument("--ledger", help=ledger_help)
    # Every subcommand also takes --ledger after its name.  SUPPRESS keeps an
    # omitted sub-level flag from clobbering one given before the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--ledger", default=argparse.SUPPRESS, help=ledger_help)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("reset", help="start a clean ledger", parents=[common])

    p_add = sub.add_parser("add", parents=[common], help="register source url(s), print their ids")
    p_add.add_argument("urls", nargs="+")
    p_add.add_argument("--title", help="title for the source (single-url calls)")
    p_add.add_argument("--accessed", help="access date (default: today)")
    p_add.add_argument("--json", action="store_true", help="emit JSON instead of ids")

    p_ing = sub.add_parser("ingest", parents=[common], help="register every url in JSON tool output")
    p_ing.add_argument("file", help="JSON file, or - for stdin")

    p_q = sub.add_parser("quote", parents=[common], help="attach verbatim supporting evidence to a source")
    p_q.add_argument("id", type=int, help="ledger id of the source the quote supports")
    p_q.add_argument("--text", required=True, help="the exact quote, copied from the page")
    p_q.add_argument(
        "--from",
        dest="evidence",
        required=True,
        help="file with the fetched page text (or - for stdin) the quote must appear in",
    )

    p_list = sub.add_parser("list", parents=[common], help="show the ledger")
    p_list.add_argument("--json", action="store_true")

    p_render = sub.add_parser("render", parents=[common], help="render a Sources block")
    p_render.add_argument(
        "--style", default="markdown", choices=["markdown", "plain", "footnotes", "bibtex", "evidence"]
    )
    p_render.add_argument("--only", help="ids to include, e.g. 1,3,5-7")
    p_render.add_argument("--cited-in", help="include only ids cited in this draft file")
    p_render.add_argument(
        "--replace-in",
        help="rewrite this draft's Sources block in place (implies --cited-in on it)",
    )

    p_ver = sub.add_parser("verify", parents=[common], help="check a draft's citations against the ledger")
    p_ver.add_argument("draft")
    p_ver.add_argument("--strict", action="store_true", help="treat warnings as failures")
    p_ver.add_argument("--min-coverage", type=float, help="required cited-sentence share, e.g. 0.5")
    p_ver.add_argument(
        "--evidence",
        action="store_true",
        help="require every cited source to carry at least one verbatim quote",
    )
    p_ver.add_argument(
        "--require-all-cited",
        action="store_true",
        help="fail when a ledger source is never cited (use with a per-document ledger)",
    )

    args = parser.parse_args(argv)
    path = resolve_ledger_path(args.ledger)

    if args.cmd == "reset":
        with _LedgerLock(path):
            save_ledger(path, {"version": SCHEMA_VERSION, "sources": []})
        print(f"ledger reset: {path}")
        return 0

    if args.cmd == "add":
        title = args.title if len(args.urls) == 1 else None
        entries = add_sources(path, args.urls, title=title, accessed=args.accessed)
        if args.json:
            print(json.dumps(entries, indent=2, ensure_ascii=False))
        else:
            for e in entries:
                print(f"[{e['id']}] {e['url']}")
        return 0

    if args.cmd == "ingest":
        raw = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"error: input is not valid JSON ({exc})", file=sys.stderr)
            return 2
        pairs = urls_from_json(payload)
        if not pairs:
            print("no urls found in input", file=sys.stderr)
            return 1
        for url, title in pairs:
            entry = add_sources(path, [url], title=title or None)[0]
            print(f"[{entry['id']}] {entry['url']}")
        return 0

    if args.cmd == "quote":
        raw = (
            sys.stdin.read()
            if args.evidence == "-"
            else Path(args.evidence).read_text(encoding="utf-8")
        )
        entry = attach_quote(path, args.id, args.text, raw)
        print(f"[{entry['id']}] evidence attached ({len(entry.get('quotes', []))} quote(s))")
        return 0

    data = load_ledger(path)
    sources = sorted(data["sources"], key=lambda s: s["id"])

    if args.cmd == "list":
        if args.json:
            print(json.dumps(sources, indent=2, ensure_ascii=False))
        elif not sources:
            print(f"ledger is empty: {path}")
        else:
            for s in sources:
                title = f"  {s['title']}" if s.get("title") else ""
                nq = len(s.get("quotes", []))
                mark = f"  ({nq} quote{'s' if nq != 1 else ''})" if nq else ""
                print(f"[{s['id']}] {s['url']}{title}{mark}")
        return 0

    if args.cmd == "render":
        only = _parse_only(args.only)
        draft_for_ids = args.replace_in or args.cited_in
        if draft_for_ids:
            draft = Path(draft_for_ids).read_text(encoding="utf-8")
            prose, _ = _split_draft(draft)
            cited = {int(m) for m in _CITE_RE.findall(prose)}
            only = cited if only is None else (only & cited)
        block = render_sources(sources, style=args.style, only=only)
        if not block:
            print("no sources to render", file=sys.stderr)
            return 1
        if args.replace_in:
            target = Path(args.replace_in)
            body = _strip_sources_block(target.read_text(encoding="utf-8"))
            target.write_text(body.rstrip("\n") + "\n\n" + block + "\n", encoding="utf-8")
            print(f"Sources block rewritten in {target}")
            return 0
        print(block)
        return 0

    if args.cmd == "verify":
        draft_path = Path(args.draft)
        if not draft_path.is_file():
            print(f"error: no such draft: {draft_path}", file=sys.stderr)
            return 2
        code, errors, warnings = verify_draft(
            draft_path,
            sources,
            strict=args.strict,
            min_coverage=args.min_coverage,
            require_evidence=args.evidence,
            require_all_cited=args.require_all_cited,
        )
        for w in warnings:
            prefix = "info" if w.startswith("stats: ") else "warn"
            print(f"{prefix}: {w}")
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        print("citations OK" if code == 0 else "verification failed")
        return code

    return 2


if __name__ == "__main__":
    sys.exit(main())
