"""Fixture suite for the repo reference checker.

One case per defect in `decisions/2026-07-28 - Code Review.md`. The checker it
replaces had no tests, which is precisely why it could report `doc links OK`
through a restructure that broke ~282 references: nothing ever asserted what it
could and could not see. Every test here is a reproduction — a scratch git repo
built to trip one specific historical failure — not a unit test of an internal.

Every path written below is deliberately fictional — `docs/gone.md`, `utils/thing.py`,
`vision/pitch.md` — so this file opts out of the reference check wholesale:

    doclink: ignore-file

That marker exists because of this file. The first CI run after it was committed
produced 40+ findings against its own fixtures, which never appeared locally: the
file was still untracked when the checker was run by hand, and the checker only
reads tracked files.

Run:
    uv run --project backend/lambda pytest utils/tests/test_check_doc_links.py
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_MODULE = Path(__file__).resolve().parents[1] / "check_doc_links.py"
_spec = importlib.util.spec_from_file_location("check_doc_links", _MODULE)
assert _spec and _spec.loader
cdl = importlib.util.module_from_spec(_spec)
sys.modules["check_doc_links"] = cdl
_spec.loader.exec_module(cdl)


def make_repo(tmp_path: Path, files: dict[str, str | bytes]) -> Path:
    """Init a git repo containing exactly `files` and stage them all."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for rel, content in files.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    return tmp_path


def kinds(report) -> list[str]:
    return [f.kind for f in report.findings]


def details(report, kind: str) -> list[str]:
    return [f.detail for f in report.findings if f.kind == kind]


# --- F12: code fences and inline spans must not be scanned -----------------


def test_fenced_example_is_not_a_finding(tmp_path):
    """A document that merely SHOWS link syntax must not turn CI red.

    Reproduces the state of `decisions/2026-07-28 - Code Review.md` itself,
    which tripped the old checker on the sentence describing the old checker.
    """
    root = make_repo(
        tmp_path,
        {
            "docs/example.md": (
                "# Guide\n\n"
                "```markdown\n"
                "[label](totally/made/up.md)\n"
                "```\n\n"
                "The old pattern matched only inline `[…](…)` syntax.\n"
                "Inline code like `docs/does-not-exist.md` is prose, not a link.\n"
            )
        },
    )
    assert kinds(cdl.run(root)) == []


def test_real_link_outside_a_fence_is_still_caught(tmp_path):
    """Blanking fences must not blank the whole document."""
    root = make_repo(
        tmp_path,
        {
            "docs/example.md": (
                "```\n[x](inside/fence.md)\n```\n\n[y](outside/gone.md)\n"
            )
        },
    )
    report = cdl.run(root)
    assert kinds(report) == ["broken-link"]
    assert "outside/gone.md" in details(report, "broken-link")[0]


# --- F13: balanced-paren targets -------------------------------------------


def test_parenthesized_filename_is_not_truncated(tmp_path):
    """`… Refactor (Round 3).md` is a real file in this repo.

    The old regex stopped the target at the first '(', producing a path that
    does not exist and failing CI on a link that resolves fine on GitHub.
    """
    name = "2026-07-15 - Code Review - xact-API Refactor (Round 3).md"
    encoded = name.replace(" ", "%20")
    root = make_repo(
        tmp_path,
        {
            f"decisions/{name}": "> **Status:** Shipped (2026-07-16)\n",
            "docs/index.md": f"See [the round-3 review](../decisions/{encoded}).\n",
        },
    )
    assert kinds(cdl.run(root)) == []


def test_angle_bracket_target_still_works(tmp_path):
    root = make_repo(
        tmp_path,
        {
            "docs/a b.md": "hi\n",
            "docs/index.md": "See [it](<a b.md>).\n",
        },
    )
    assert kinds(cdl.run(root)) == []


# --- F11: reference-style, HTML, and nested image-links --------------------


def test_reference_style_definition_is_checked(tmp_path):
    root = make_repo(
        tmp_path,
        {"docs/index.md": "Text with a [ref][id].\n\n[id]: missing/target.md\n"},
    )
    report = cdl.run(root)
    assert kinds(report) == ["broken-link"]
    assert "missing/target.md" in details(report, "broken-link")[0]


def test_html_img_is_checked(tmp_path):
    """Several architecture diagrams are embedded as HTML, not markdown."""
    root = make_repo(
        tmp_path,
        {"docs/index.md": '<img src="images/gone.png" alt="diagram">\n'},
    )
    assert kinds(cdl.run(root)) == ["broken-link"]


def test_nested_image_link_outer_target_is_seen(tmp_path):
    """`[![alt](img)](target)` — the old character class could not span the
    inner ']', so the outer target was never checked at all."""
    root = make_repo(
        tmp_path,
        {
            "docs/badge.png": b"\x89PNG\r\n",
            "docs/index.md": "[![badge](badge.png)](gone/page.md)\n",
        },
    )
    report = cdl.run(root)
    assert kinds(report) == ["broken-link"]
    assert "gone/page.md" in details(report, "broken-link")[0]


# --- F15: git C-quoting of non-ASCII paths ---------------------------------


def test_non_ascii_filename_is_read_not_reported_unreadable(tmp_path):
    """`git ls-files` C-quotes non-ASCII paths unless -z is used.

    This repo already tracks such a file. The old checker turned the quoted
    name into an 'unreadable' finding AND skipped that file's own links.
    """
    root = make_repo(
        tmp_path,
        {
            "docs/café — notes.md": "[real](../README.md)\n[broken](nope.md)\n",
            "README.md": "root\n",
        },
    )
    report = cdl.run(root)
    assert kinds(report) == ["broken-link"], report.findings
    assert "unreadable" not in details(report, "broken-link")[0]
    assert "nope.md" in details(report, "broken-link")[0]


# --- F3: the largest class — stale paths in non-markdown source ------------


def test_stale_path_in_python_comment_is_caught(tmp_path):
    """The defect a markdown-only checker structurally cannot see."""
    root = make_repo(
        tmp_path,
        {
            "utils/thing.py": '"""Contract lives in docs/contracts/prd-contract.md."""\n',
            "specs/contracts/prd-contract.md": "# contract\n",
        },
    )
    report = cdl.run(root)
    assert kinds(report) == ["stale-source-ref"]
    assert "docs/contracts/prd-contract.md" in details(report, "stale-source-ref")[0]


def test_stale_path_in_typescript_and_yaml_is_caught(tmp_path):
    root = make_repo(
        tmp_path,
        {
            "frontend/app.ts": "// see docs/gone.md for context\n",
            "specs/api/v1.yaml": "# description: see docs/also-gone.md\n",
        },
    )
    assert kinds(cdl.run(root)) == ["stale-source-ref", "stale-source-ref"]


def test_resolving_source_path_is_not_flagged(tmp_path):
    root = make_repo(
        tmp_path,
        {
            "utils/thing.py": "# see docs/real.md\n",
            "docs/real.md": "# real\n",
        },
    )
    assert kinds(cdl.run(root)) == []


def test_url_containing_a_repo_shaped_tail_is_not_flagged(tmp_path):
    root = make_repo(
        tmp_path,
        {
            "utils/thing.py": (
                "URL = 'https://raw.githubusercontent.com/skrinak/ContextEng/"
                "refs/heads/main/docs/TaskListGenerator.md'\n"
            )
        },
    )
    assert kinds(cdl.run(root)) == []


def test_noqa_escape_suppresses_a_source_finding(tmp_path):
    root = make_repo(
        tmp_path,
        {"utils/thing.py": "# historical: docs/old-layout.md  doclink: ignore\n"},
    )
    assert kinds(cdl.run(root)) == []


def test_escape_token_does_not_collide_with_ruff(tmp_path):
    """The marker was `# noqa: doclink` until ruff started emitting
    'Invalid # noqa directive' on every use. An escape hatch that makes another
    linter unhappy is not an escape hatch."""
    assert "noqa" not in cdl.NOQA


def test_ignore_files_may_name_paths_that_do_not_exist(tmp_path):
    """That is the entire purpose of an ignore rule.

    The `tmp.md` pin restored after the 2026-07 secret leak names a file that
    must never exist — flagging it would pressure someone into deleting the
    guard to get CI green, which is exactly how the leak guard was lost.
    """
    root = make_repo(
        tmp_path,
        {
            ".gitignore": "docs/tmp.md\n**/tmp.md\n",
            ".dockerignore": "docs/scratch.md\n",
        },
    )
    assert kinds(cdl.run(root)) == []


def test_recorded_fixture_trees_are_not_scanned(tmp_path, monkeypatch):
    """Captured production data is the user's prose, not our reference.

    Default is empty; this asserts the mechanism a project opts into when it
    starts committing recorded fixtures.
    """
    monkeypatch.setattr(cdl, "NO_SOURCE_REF_PREFIXES", ("fixtures/captured/",))
    root = make_repo(
        tmp_path,
        {
            "fixtures/captured/session.json":
                '[{"content": "we documented it in docs/gone.md"}]\n'
        },
    )
    assert kinds(cdl.run(root)) == []


def test_glob_and_template_shapes_are_not_flagged(tmp_path):
    root = make_repo(
        tmp_path,
        {
            "utils/thing.py": (
                "GLOB = 'backend/lambda/**/*.py'\n"
                "TPL = f'docs/{name}.md'\n"
            )
        },
    )
    assert kinds(cdl.run(root)) == []


def test_taxonomy_dir_is_checked_even_when_emptied(tmp_path):
    """If a bucket holds no tracked file, references to it must still be checked
    — otherwise emptying a directory silently disables the guard for it."""
    root = make_repo(tmp_path, {"utils/thing.py": "# see vision/pitch.md\n"})
    assert kinds(cdl.run(root)) == ["stale-source-ref"]


# --- R8: seeded-customer-repo contract strings must never be flagged -------


def test_generated_repo_paths_are_never_flagged(tmp_path, monkeypatch):
    """Paths describing a repo this project SCAFFOLDS for someone else.

    Rewriting them to match this tree would corrupt every repo you have seeded —
    the single most damaging thing a blind reference sweep can do. The default is
    empty; this asserts the MECHANISM, so the test holds whatever a project fills in.
    """
    monkeypatch.setattr(cdl, "GENERATED_REPO_PATHS", ("docs/architecture/", "docs/deploy-plan.md"))
    root = make_repo(
        tmp_path,
        {
            "backend/seed.py": (
                'files["docs/architecture/ARCHITECTURE.md"] = x\n'
                'files["docs/deploy-plan.md"] = y\n'
            ),
            "docs/guide.md": "[gen](../docs/deploy-plan.md)\n",
        },
    )
    assert kinds(cdl.run(root)) == []


def test_generated_repo_paths_default_to_empty(tmp_path):
    """A fresh project scaffolds nothing, so the allow-list starts empty.

    An allow-list that ships pre-populated with another project's paths is a
    silent hole: it would exempt real breakage in a repo that never seeds anything.
    """
    assert cdl.GENERATED_REPO_PATHS == ()


# --- F4: link labels rewritten out of sync with their targets --------------


def test_label_pointing_at_a_nonexistent_path_is_flagged(tmp_path):
    """Agents copy the visible backticked label, not the href."""
    root = make_repo(
        tmp_path,
        {
            "decisions/MCPinstall.md": "> **Status:** Shipped (2026-06-30)\n",
            "runbooks/mcp/Monday.md": (
                "Design in [`../MCPinstall.md`](../../decisions/MCPinstall.md).\n"
            ),
        },
    )
    report = cdl.run(root)
    assert kinds(report) == ["label-mismatch"]
    assert "../MCPinstall.md" in details(report, "label-mismatch")[0]


def test_bare_filename_label_is_a_display_name_not_a_claim(tmp_path):
    root = make_repo(
        tmp_path,
        {
            "decisions/End2End.md": "> **Status:** Shipped (2026-07-24)\n",
            "README.md": "See [`End2End.md`](decisions/End2End.md).\n",
        },
    )
    assert kinds(cdl.run(root)) == []


def test_repo_root_relative_label_is_accepted(tmp_path):
    root = make_repo(
        tmp_path,
        {
            "docs/arch/images/board.jpg": b"\xff\xd8\xff",
            ".claude/skills/wb/GUIDE.md": (
                "See [`docs/arch/images/board.jpg`](../../../docs/arch/images/board.jpg).\n"
            ),
        },
    )
    assert kinds(cdl.run(root)) == []


# --- F2 / R7: status headers, and the evals exemption ----------------------


def test_decisions_record_without_status_header_is_flagged(tmp_path):
    root = make_repo(tmp_path, {"decisions/Thing.md": "# Thing\n\nBody.\n"})
    assert kinds(cdl.run(root)) == ["missing-status"]


def test_decisions_record_with_status_header_passes(tmp_path):
    root = make_repo(
        tmp_path,
        {"decisions/Thing.md": "# Thing\n\n> **Status:** Proposed\n\nBody.\n"},
    )
    assert kinds(cdl.run(root)) == []


def test_generated_evals_are_exempt_from_the_status_lint(tmp_path):
    """A bake-off scorecard is data, not a decision — it carries a provenance
    line instead of a status. Without this exemption, the generator's own output
    reddens CI on every run (F2's second-order effect)."""
    root = make_repo(
        tmp_path,
        {
            "decisions/evals/2026-07-28-model-strategy.md": (
                "# Scorecard\n\n> **Generated artifact** — produced by ...\n"
            ),
            "decisions/evals/README.md": "# evals\n",
        },
    )
    assert kinds(cdl.run(root)) == []


# --- R9: root markdown bucket membership -----------------------------------


def test_unsanctioned_root_markdown_is_flagged(tmp_path):
    root = make_repo(
        tmp_path,
        {
            "README.md": "ok\n",
            "CLAUDE.md": "ok\n",
            "tasks.md": "ok\n",
            "NOTES.md": "should have been filed into a bucket\n",
        },
    )
    report = cdl.run(root)
    assert kinds(report) == ["root-markdown"]
    assert report.findings[0].file == "NOTES.md"


def test_the_three_sanctioned_root_files_pass(tmp_path):
    root = make_repo(
        tmp_path,
        {"README.md": "ok\n", "CLAUDE.md": "ok\n", "tasks.md": "ok\n"},
    )
    assert kinds(cdl.run(root)) == []


# --- Site-absolute routes are URLs, not filesystem paths -------------------


def test_site_absolute_route_is_not_a_filesystem_path(tmp_path):
    """docs-site/ is a Nextra app whose pages link each other by route."""
    root = make_repo(
        tmp_path,
        {"docs-site/pages/index.mdx": "[Streaming](/streaming)\n"},
    )
    assert kinds(cdl.run(root)) == []


# --- Binary and skipped trees ----------------------------------------------


def test_binary_files_are_skipped_without_error(tmp_path):
    root = make_repo(
        tmp_path,
        {
            "images/logo.png": b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00docs/x.md",
            "docs/index.md": "clean\n",
        },
    )
    assert kinds(cdl.run(root)) == []


@pytest.mark.parametrize("vendor", ["node_modules", "dist", "cdk.out"])
def test_vendored_trees_are_skipped(tmp_path, vendor):
    root = make_repo(
        tmp_path,
        {f"{vendor}/pkg/readme.md": "[x](docs/nope.md)\n", "docs/keep.md": "ok\n"},
    )
    assert kinds(cdl.run(root)) == []


def test_bucket_readme_is_not_a_record(tmp_path):
    """`decisions/README.md` explains the bucket; it does not record a decision."""
    root = make_repo(tmp_path, {"decisions/README.md": "# decisions/\n\nWhat goes here.\n"})
    assert kinds(cdl.run(root)) == []


def test_fenced_status_example_does_not_satisfy_the_lint(tmp_path):
    """A record that merely SHOWS the header syntax has not got one.

    Caught in the wild: every bucket README quotes the syntax in a fenced block,
    so an unfenced status check passes on documents that only demonstrate it.
    """
    root = make_repo(
        tmp_path,
        {"decisions/Thing.md": "# Thing\n\n```markdown\n> **Status:** Shipped (2026-01-01)\n```\n"},
    )
    assert kinds(cdl.run(root)) == ["missing-status"]
