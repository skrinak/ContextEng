#!/usr/bin/env python3
"""Repo reference checker + root-taxonomy lint.

Guards the taxonomy in `docs/PRD.md` §15: a path written down anywhere in the
repo should resolve, records under `decisions/` should carry a status header,
and root markdown should be exactly the three sanctioned files.

WHY THIS IS NOT A MARKDOWN LINK CHECKER
---------------------------------------
The version this replaces walked `git ls-files '*.md'` and matched one regex for
inline `[…](…)` syntax. It reported `doc links OK` throughout the 2026-07 root
restructure and that was read as evidence the sweep was complete. It was not:
a markdown-only checker structurally cannot see the ~282 stale `docs/` paths the
restructure left in `.py` / `.ts` / `.tsx` / `.sh` / `.yml` source comments,
which was the largest class of breakage by an order of magnitude. It also failed
in the other direction — red-lighting correct documents — because it had no
code-fence awareness, truncated targets at the first `(`, and choked on git's
C-quoting of non-ASCII paths. Every one of those defects has a fixture in
`utils/tests/test_check_doc_links.py`. Rationale for the taxonomy this enforces:
https://github.com/skrinak/ContextEng/blob/main/docs/REPOSITORY_TAXONOMY.md

WHAT IT CHECKS
--------------
Every *tracked text file*, selected with `git ls-files -z` so non-ASCII paths
arrive as real bytes rather than C-quoted escapes.

  markdown (`.md`, `.mdx`)
      - inline links and images, including nested image-links (`[![a](i)](t)`),
        with balanced-paren target parsing and URL-decoding
      - reference-style definitions (`[id]: target`)
      - HTML `src=` / `href=` attributes, which is how several architecture
        diagrams are embedded
      - backticked link *labels*: when a label is itself a path, it must resolve
        too. Agents copy the visible label rather than following the href, so a
        label pointing at a path that no longer exists misdirects them silently.
      Fenced blocks and inline code spans are blanked before any of this, so a
      document that merely *shows* link syntax as an example is not a finding.

  every other text file
      - repo-root-relative paths in comments and strings, matched conservatively:
        the first segment must be a real top-level directory, and the candidate
        must carry a file extension or resolve to a directory. Escape a genuine
        exception with a `doclink: ignore` marker on the same line.

  taxonomy
      - `decisions/**.md` carries `> **Status:**` (generated artifacts under
        `decisions/evals/` are exempt — they are data, not records)
      - root-level markdown is exactly README.md, CLAUDE.md, tasks.md

DELIBERATE SCOPE LIMIT (stated, not silent)
-------------------------------------------
Path-shaped strings in markdown *prose* are not checked — only link targets and
labels. Reviews, postmortems and migration records legitimately quote paths that
no longer exist, as evidence of what moved; flagging those would make CI red on
the very documents whose job is to record history, and the pressure would then
be to weaken the checker. Source comments have no such use case, which is why
they are checked and prose is not.

Usage:
    uv run --no-project python3 utils/check_doc_links.py [--root PATH] [--json]

Exit codes: 0 clean, 1 findings. Stdlib only; runs anywhere git is available.
CI wiring in `.github/workflows/docs-links.yml`.
"""

from __future__ import annotations

import argparse
import bisect
import json
import re
import subprocess
import sys
import posixpath
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

# --- Configuration -------------------------------------------------------

MARKDOWN_SUFFIXES = {".md", ".mdx"}

# Binary or generated-blob suffixes: never worth scanning, and some are large.
SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".pdf", ".zip",
    ".gz", ".tgz", ".woff", ".woff2", ".ttf", ".otf", ".eot", ".mp4", ".mov",
    ".mp3", ".wav", ".jar", ".so", ".dylib", ".pyc", ".pptx", ".xlsx", ".docx",
    ".lock", ".pack", ".idx", ".webmanifest",
}

# Trees whose contents are vendored, generated, or third-party.
SKIP_PREFIXES = ("node_modules/", "dist/", "build/", "cdk.out/", ".venv/", "out/")

# Files whose whole point is to name paths that do NOT exist, or that are
# captured data rather than authored source:
#   *ignore   — an ignore pattern names what must never be committed. The
#               `docs/tmp.md` pin restored after the 2026-07 secret leak is  doclink: ignore
#               precisely a rule about a file that should not exist.
#   recorded fixtures — captured production data. A path inside a user's recorded
#               text is their prose, not a reference this repo is making. Add such
#               trees to NO_SOURCE_REF_PREFIXES below.
SKIP_BASENAMES = (".gitignore", ".dockerignore", ".npmignore", ".eslintignore", ".prettierignore")
NO_SOURCE_REF_PREFIXES: tuple[str, ...] = ()

ROOT_MARKDOWN_ALLOWED = {"README.md", "CLAUDE.md", "tasks.md"}

STATUS_LINT_DIR = "decisions"
# Generated eval artifacts are machine-written data, not decision records: they
# carry a `> **Generated artifact**` provenance line instead of a status.
# See decisions/evals/README.md.
STATUS_LINT_EXEMPT_PREFIXES = ("decisions/evals/",)

# Paths that describe the *generated customer repository* xact.ai seeds at the
# end of Inception, not this repo. They are contract strings — rewriting them to
# match this repo's tree would corrupt every repo we seed. Kept as an explicit
# list rather than a blanket file exemption so that adding a new seeded path is
# a deliberate edit here, not a silent pass.
GENERATED_REPO_PATHS: tuple[str, ...] = (
    # Populate ONLY if this project writes files into a repository it scaffolds
    # for someone else. Those path strings describe the GENERATED repo, not this
    # one — a sweep that "fixes" them to match your tree corrupts every repo you
    # have ever seeded. Example:
    #     "docs/architecture/",
    #     "docs/deploy-plan.md",
)

NOQA = "doclink: ignore"
# Whole-file opt-out, for files whose every path is synthetic (see run()).
IGNORE_FILE = "doclink: ignore-file"

IGNORED_SCHEMES = ("http://", "https://", "mailto:", "tel:", "data:", "ftp://", "//")

_STATUS_RE = re.compile(r"^>\s*\*\*Status:\*\*", re.MULTILINE)
_REF_DEF_RE = re.compile(r"^[ ]{0,3}\[([^\]]+)\]:[ \t]*(\S+)", re.MULTILINE)
_HTML_REF_RE = re.compile(
    r"""<(?:img|a|source|embed|iframe)\b[^>]*?\b(?:src|href)\s*=\s*["']([^"']+)["']""",
    re.IGNORECASE,
)
_FENCE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})(.*)$")
# A path-shaped token: first segment is filled in from the repo's real top-level
# directories, so `foo/bar.py` in a log-format string is not a candidate.
_PATH_TAIL = r"[A-Za-z0-9_.\-/]*[A-Za-z0-9_\-/]"
_TRAILING_PUNCT = ".,;:!?)]}'\"`"


# --- Findings ------------------------------------------------------------


@dataclass
class Finding:
    kind: str
    file: str
    line: int
    detail: str

    def render(self) -> str:
        return f"  {self.file}:{self.line}: {self.detail}"


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, kind: str, file: str, line: int, detail: str) -> None:
        self.findings.append(Finding(kind, file, line, detail))

    def by_kind(self) -> dict[str, list[Finding]]:
        out: dict[str, list[Finding]] = {}
        for f in self.findings:
            out.setdefault(f.kind, []).append(f)
        return out


# --- File selection (R5: -z, so non-ASCII paths are real bytes) ----------


def tracked_names(root: Path) -> list[str]:
    """Every tracked path, as repo-relative strings.

    `-z` because git C-quotes any path with non-ASCII bytes otherwise, and this
    repo already tracks one (`images/Screenshot … PM.png`, with a U+202F).
    """
    out = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    return [
        raw.decode("utf-8", errors="surrogateescape")
        for raw in out.stdout.split(b"\0")
        if raw
    ]


class PathIndex:
    """Existence oracle built from the git index, NOT the working tree.

    This is a correctness requirement, not an optimization. Resolving against
    the filesystem makes the checker environment-dependent in two ways that both
    bit in practice:

      * a gitignored file present on a developer's disk (`migration/new-account.env`)
        resolves locally and 404s in CI, so `make check-links` passes and the
        identical CI job fails on the same commit;
      * macOS is case-insensitive and the CI runner is not, so a path whose case
        does not match would pass locally and fail on Linux.

    A guard that answers differently depending on where it runs teaches people
    to disbelieve it. Membership in the index is the same answer everywhere.
    """

    def __init__(self, names: list[str]) -> None:
        self.files = set(names)
        self.dirs: set[str] = set()
        for n in names:
            parts = n.split("/")
            for i in range(1, len(parts)):
                self.dirs.add("/".join(parts[:i]))

    def exists(self, rel: str) -> bool:
        rel = rel.rstrip("/")
        return rel in self.files or rel in self.dirs


def resolve_rel(from_file: str, target: str) -> str | None:
    """Join `target` onto the directory of `from_file`, normalized, repo-relative.

    Pure string math (`posixpath.normpath`) rather than `Path.resolve()`, which
    would consult the filesystem and reintroduce the divergence above. Returns
    None if the result escapes the repo root.
    """
    base = posixpath.dirname(from_file)
    joined = posixpath.normpath(posixpath.join(base, target))
    if joined.startswith("..") or joined == ".":
        return None
    return joined


def is_scannable(rel: str) -> bool:
    if rel.startswith(SKIP_PREFIXES) or any(f"/{p}" in f"/{rel}" for p in SKIP_PREFIXES):
        return False
    return PurePosixPath(rel).suffix.lower() not in SKIP_SUFFIXES


def read_text(path: Path) -> str | None:
    """Return decoded text, or None for anything that is not usefully text."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def line_index(text: str) -> list[int]:
    idx, pos = [], 0
    while True:
        nl = text.find("\n", pos)
        if nl == -1:
            break
        idx.append(nl)
        pos = nl + 1
    return idx


def line_of(idx: list[int], offset: int) -> int:
    return bisect.bisect_left(idx, offset) + 1


# --- Markdown: blank out code so examples are not findings (R2) ----------


def blank_code(text: str) -> str:
    """Replace fenced blocks and inline code spans with spaces of equal length.

    Offsets and line numbers are preserved, so a finding still reports the line
    it was found on.
    """
    lines = text.split("\n")
    fence: tuple[str, int] | None = None
    for i, line in enumerate(lines):
        m = _FENCE_RE.match(line)
        if fence is None:
            if m:
                fence = (m.group(2)[0], len(m.group(2)))
                lines[i] = " " * len(line)
            continue
        # inside a fence
        closes = m and m.group(2)[0] == fence[0] and len(m.group(2)) >= fence[1] and not m.group(3).strip()
        lines[i] = " " * len(line)
        if closes:
            fence = None
    out = "\n".join(lines)

    # Inline spans: a run of N backticks closes on the next run of exactly N.
    result = list(out)
    i, n = 0, len(out)
    while i < n:
        if out[i] != "`":
            i += 1
            continue
        run = 1
        while i + run < n and out[i + run] == "`":
            run += 1
        j, close = i + run, -1
        while j < n:
            if out[j] == "`":
                r2 = 1
                while j + r2 < n and out[j + r2] == "`":
                    r2 += 1
                if r2 == run:
                    close = j
                    break
                j += r2
                continue
            j += 1
        if close == -1:
            i += run
            continue
        for k in range(i, close + run):
            if result[k] != "\n":
                result[k] = " "
        i = close + run
    return "".join(result)


# --- Markdown: link extraction (R3 nesting, R4 balanced parens) ----------


def _parse_paren_target(text: str, open_idx: int) -> tuple[str | None, int]:
    """Parse `(target "title")` starting at the '('. Returns (target, end_index).

    Depth-counted so a filename containing parentheses — this repo really has
    `decisions/2026-07-15 - Code Review - xact-API Refactor (Round 3).md` — is
    not truncated at the first inner '('.
    """
    n = len(text)
    i, depth = open_idx + 1, 1
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                break
        elif c == "\n" and text[i - 1 : i] == "\n":
            return None, open_idx + 1  # blank line: not a link
        i += 1
    if i >= n or depth != 0:
        return None, open_idx + 1
    content = text[open_idx + 1 : i].strip()
    if content.startswith("<"):
        gt = content.find(">")
        if gt != -1:
            return content[1:gt], i + 1
    # CommonMark: the destination ends at the first whitespace; the remainder is
    # an optional title. Spaces inside a real target are %20-encoded or <>-wrapped.
    target = content.split(maxsplit=1)[0] if content.split() else ""
    return target, i + 1


def iter_markdown_links(text: str):
    """Yield (label_start, label_end, target, offset) for inline links/images.

    Bracket-matched rather than regex'd, because a character class cannot span
    the inner `]` of a nested image-link and so never sees the outer target.

    The label is returned as a *span*, not a string, because this runs over the
    code-blanked text (so link syntax quoted as an example is not a finding)
    while the label check needs the original bytes — link labels in this repo
    are conventionally backticked, i.e. they are themselves code spans. Offsets
    are identical in both texts by construction.
    """
    stack: list[int] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "[":
            stack.append(i)
        elif c == "]" and stack:
            start = stack.pop()
            if i + 1 < n and text[i + 1] == "(":
                target, end = _parse_paren_target(text, i + 1)
                if target is not None:
                    yield start + 1, i, target, start
                    i = end
                    continue
        i += 1


def normalize_target(raw: str) -> str | None:
    raw = raw.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    if not raw or raw.startswith("#"):
        return None
    if raw.lower().startswith(IGNORED_SCHEMES):
        return None
    # A leading '/' is a site-absolute URL, not a repo path (CommonMark, and on
    # GitHub it resolves against the domain). docs-site/ is a Nextra app whose
    # pages link each other by route — `/streaming`, `/api-reference/v1`. Those
    # are validated by that site's own build, not by a filesystem check here.
    if raw.startswith("/"):
        return None
    raw = raw.split("#", 1)[0].split("?", 1)[0]
    if not raw:
        return None
    return urllib.parse.unquote(raw)


# --- Source files: conservative repo-path matcher (R1) -------------------


# Always-checked first segments, even when the directory currently holds no
# tracked file. Discovering top-level dirs purely from the tree would mean that
# emptying a bucket silently stops the checker from noticing references to it —
# which is the exact failure mode (a guard that goes quiet instead of loud) this
# rewrite exists to remove.
TAXONOMY_DIRS = frozenset(
    {"docs", "specs", "runbooks", "decisions", "vision", ".claude", ".github"}
)


def top_level_dirs(names: list[str]) -> set[str]:
    out = set(TAXONOMY_DIRS)
    for rel in names:
        head, sep, _ = rel.partition("/")
        if sep:
            out.add(head)
    return out


def source_path_re(tops: set[str]) -> re.Pattern[str]:
    alt = "|".join(sorted((re.escape(t) for t in tops), key=len, reverse=True))
    return re.compile(rf"(?<![A-Za-z0-9_.\-/])({alt})/{_PATH_TAIL}")


def iter_source_paths(text: str, pattern: re.Pattern[str]):
    for m in pattern.finditer(text):
        cand = m.group(0)
        # A URL that happens to contain a repo-shaped tail is not a repo path.
        before = text[max(0, m.start() - 12) : m.start()]
        if "://" in before or before.endswith(("http", "https", "@")):
            continue
        cand = cand.rstrip(_TRAILING_PUNCT)
        if not cand or any(ch in cand for ch in "*{}<>$"):
            continue
        yield cand, m.start()


# --- Checks --------------------------------------------------------------


def is_generated_repo_path(rel_target: str) -> bool:
    return any(
        rel_target == p or rel_target.startswith(p) for p in GENERATED_REPO_PATHS
    )


def looks_like_path(label: str) -> bool:
    """True for a backticked label that is trying to be a filesystem path."""
    if not label or " " in label:
        return False
    if "/" not in label and not Path(label).suffix:
        return False
    return not label.lower().startswith(IGNORED_SCHEMES)


def _label_resolves(rel: str, label: str, index: PathIndex) -> bool:
    """A label may be written relative to its own file or repo-root-relative."""
    from_file = resolve_rel(rel, label)
    if from_file and index.exists(from_file):
        return True
    return index.exists(label.lstrip("/"))


def check_markdown(rel: str, text: str, index: PathIndex, report: Report) -> None:
    idx = line_index(text)
    stripped = blank_code(text)

    seen: set[tuple[str, int]] = set()

    def flag_target(target: str, offset: int, kind: str, detail_prefix: str) -> None:
        norm = normalize_target(target)
        if norm is None:
            return
        resolved = resolve_rel(rel, norm)
        if resolved is None:
            return
        if is_generated_repo_path(resolved):
            return
        if index.exists(resolved):
            return
        line = line_of(idx, offset)
        if (norm, line) in seen:
            return
        seen.add((norm, line))
        report.add(kind, rel, line, f"{detail_prefix} -> {norm}")

    for lab_start, lab_end, target, offset in iter_markdown_links(stripped):
        flag_target(target, offset, "broken-link", "broken link")

        # A backticked label that is itself a path must resolve too. Read from
        # the ORIGINAL text: the blanked copy has erased the backticks.
        lab = text[lab_start:lab_end].strip()
        if lab.startswith("`") and lab.endswith("`") and len(lab) > 2:
            inner = lab[1:-1].strip()
            if looks_like_path(inner):
                norm_lab = normalize_target(inner)
                norm_tgt = normalize_target(target)
                if (
                    norm_lab
                    and norm_tgt
                    and norm_lab != norm_tgt
                    # A bare filename matching the target's basename is a display
                    # name, not a path claim — `[`End2End.md`](decisions/End2End.md)`
                    # misdirects nobody. Only a label that *asserts a location*
                    # can send a reader somewhere that does not exist.
                    and not (
                        "/" not in norm_lab
                        and PurePosixPath(norm_lab).name == PurePosixPath(norm_tgt).name
                    )
                    # Accept either convention: relative to this file, or
                    # repo-root-relative (which is unambiguous and often clearer).
                    and not _label_resolves(rel, norm_lab, index)
                ):
                    report.add(
                        "label-mismatch",
                        rel,
                        line_of(idx, offset),
                        f"link label `{inner}` does not resolve (target is {norm_tgt})",
                    )

    for m in _REF_DEF_RE.finditer(stripped):
        flag_target(m.group(2), m.start(2), "broken-link", "broken reference definition")

    for m in _HTML_REF_RE.finditer(stripped):
        flag_target(m.group(1), m.start(1), "broken-link", "broken HTML reference")


def check_source(
    rel: str, text: str, index: PathIndex, pattern: re.Pattern[str], report: Report
) -> None:
    idx = line_index(text)
    lines = text.split("\n")
    seen: set[tuple[str, int]] = set()
    for cand, offset in iter_source_paths(text, pattern):
        line = line_of(idx, offset)
        if NOQA in lines[line - 1]:
            continue
        if is_generated_repo_path(cand):
            continue
        if index.exists(cand):
            continue
        # Require an extension or an existing-directory shape; a bare
        # `backend/whatever` with no suffix is too likely to be prose.
        if not PurePosixPath(cand).suffix:
            continue
        if (cand, line) in seen:
            continue
        seen.add((cand, line))
        report.add("stale-source-ref", rel, line, f"stale path reference -> {cand}")


def check_taxonomy(root: Path, names: list[str], report: Report) -> None:
    for rel in names:
        if PurePosixPath(rel).suffix.lower() not in MARKDOWN_SUFFIXES:
            continue

        if "/" not in rel and rel not in ROOT_MARKDOWN_ALLOWED:
            report.add(
                "root-markdown",
                rel,
                1,
                "root markdown must be exactly "
                + ", ".join(sorted(ROOT_MARKDOWN_ALLOWED))
                + " — file it into a taxonomy bucket (docs.PRD.md §15)",
            )

        if rel.split("/")[0] == STATUS_LINT_DIR:
            if rel.startswith(STATUS_LINT_EXEMPT_PREFIXES):
                continue
            # A bucket's own README is a usage guide, not a record. It explains
            # what belongs in the directory; it does not record a decision.
            if PurePosixPath(rel).name == "README.md":
                continue
            text = read_text(root / rel)
            # Blank code first: an example status header inside a fenced block
            # must not satisfy the lint. Every bucket README shows the syntax,
            # so without this the check passes on documents that quote it.
            if text is not None and not _STATUS_RE.search(blank_code(text)):
                report.add(
                    "missing-status",
                    rel,
                    1,
                    "decisions/ record is missing its `> **Status:**` header",
                )


# --- Driver --------------------------------------------------------------


def run(root: Path) -> Report:
    report = Report()
    names = tracked_names(root)
    index = PathIndex(names)
    scannable = [n for n in names if is_scannable(n)]
    pattern = source_path_re(top_level_dirs(scannable))

    for rel in scannable:
        text = read_text(root / rel)
        if text is None:
            continue
        # A file that is ENTIRELY synthetic fixtures opts out wholesale. The
        # checker's own test suite is the motivating case: every path in it is
        # deliberately fictional, so line-by-line markers would be ~30 of them.
        if IGNORE_FILE in text:
            continue
        if PurePosixPath(rel).suffix.lower() in MARKDOWN_SUFFIXES:
            check_markdown(rel, text, index, report)
        elif PurePosixPath(rel).name not in SKIP_BASENAMES and not rel.startswith(
            NO_SOURCE_REF_PREFIXES
        ):
            check_source(rel, text, index, pattern, report)

    check_taxonomy(root, names, report)
    return report


KIND_HEADINGS = {
    "broken-link": "BROKEN RELATIVE LINKS",
    "label-mismatch": "LINK LABELS THAT DO NOT RESOLVE",
    "stale-source-ref": "STALE PATH REFERENCES IN SOURCE",
    "missing-status": "decisions/ RECORDS MISSING `> **Status:**` HEADER",
    "root-markdown": "MARKDOWN AT THE REPO ROOT",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Repo reference checker + taxonomy lint.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repo root (default: this repo)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--only",
        action="append",
        choices=sorted(KIND_HEADINGS),
        help="restrict output to one or more finding kinds (repeatable)",
    )
    args = parser.parse_args()

    report = run(args.root.resolve())
    grouped = report.by_kind()
    if args.only:
        grouped = {k: v for k, v in grouped.items() if k in args.only}

    if args.json:
        print(
            json.dumps(
                [
                    {"kind": f.kind, "file": f.file, "line": f.line, "detail": f.detail}
                    for fs in grouped.values()
                    for f in fs
                ],
                indent=2,
            )
        )
        return 1 if grouped else 0

    for kind, heading in KIND_HEADINGS.items():
        found = grouped.get(kind)
        if not found:
            continue
        print(f"{heading} ({len(found)}):")
        for f in sorted(found, key=lambda x: (x.file, x.line)):
            print(f.render())
        print()

    if grouped:
        print(f"{sum(len(v) for v in grouped.values())} finding(s).")
        return 1
    print("doc links OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
