from __future__ import annotations

import copy
import datetime as dt
import importlib
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

UTILS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(UTILS))

fsi_corpus = importlib.import_module("fsi_corpus")
fsi_render = importlib.import_module("fsi_render")

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "fsi"
BASE = FIXTURES / "base"
CASES = sorted((FIXTURES / "cases").glob("*.yaml"))
SCHEMA_DIR = fsi_corpus.DEFAULT_ROOT / "schema"
FIXTURE_TODAY = dt.date(2026, 3, 1)


def load_base() -> fsi_corpus.Corpus:
    return fsi_corpus.load(BASE)


def validate(corpus: fsi_corpus.Corpus, today: dt.date = FIXTURE_TODAY) -> list[fsi_corpus.Finding]:
    return fsi_corpus.Validator(corpus, today, SCHEMA_DIR).run()


def _walk(record: Any, path: list[Any]) -> tuple[Any, Any]:
    for key in path[:-1]:
        record = record[key]
    return record, path[-1]


def apply_case(corpus: fsi_corpus.Corpus, case: dict[str, Any]) -> None:
    for collection, records in (case.get("append") or {}).items():
        for record in records:
            record = copy.deepcopy(record)
            getattr(corpus, collection).append(record)
            corpus.origin[id(record)] = f"case:{collection}"
    for op in case.get("set") or []:
        parent, key = _walk(getattr(corpus, op["collection"])[op["index"]], op["path"])
        parent[key] = op["value"]
    for op in case.get("delete") or []:
        parent, key = _walk(getattr(corpus, op["collection"])[op["index"]], op["path"])
        del parent[key]


def test_base_fixture_is_clean() -> None:
    assert validate(load_base()) == []


@pytest.mark.parametrize("case_path", CASES, ids=[p.stem for p in CASES])
def test_each_failure_mode_is_detected(case_path: Path) -> None:
    case = yaml.safe_load(case_path.read_text(encoding="utf-8"))
    corpus = load_base()
    apply_case(corpus, case)
    today = dt.date.fromisoformat(case["today"]) if "today" in case else FIXTURE_TODAY
    rules = {finding.rule for finding in validate(corpus, today)}
    assert case["expect"] in rules, f"{case['description']}: expected {case['expect']}, got {sorted(rules)}"


def test_every_case_file_names_a_rule_the_validator_emits() -> None:
    known = {
        "schema", "duplicate-id", "dangling-ref", "authority-host", "jurisdiction-mismatch",
        "duplicate-url", "status-missing", "not-in-force", "citation-without-obligation",
        "unquoted-number", "stale", "confidence",
    }
    for path in CASES:
        assert yaml.safe_load(path.read_text(encoding="utf-8"))["expect"] in known, path.name


@pytest.mark.parametrize(
    ("quote", "number", "expected"),
    [
        ("for a period of not less than 6 years", 6, True),
        ("for a period of not less than six years", 6, True),
        ("until eighteen months after", 18, True),
        ("pursuant to § 240.17a-3(a)(6)", 6, False),
        ("a period of 16 years", 6, False),
        ("not less than five years", 6, False),
    ],
)
def test_quote_mentions_matches_numerals_and_words_only(quote: str, number: int, expected: bool) -> None:
    assert fsi_corpus._quote_mentions(quote, number) is expected


def test_citation_numbers_in_requirements_are_not_treated_as_quantities() -> None:
    text = "Preserve the records made under Rule 17a-3(a)(1)-(3) and SEC Rule 2-06 for 6 years."
    assert fsi_corpus.STANDALONE_NUMBER.findall(text) == ["6"]


def test_yaml_dates_and_yes_no_stay_strings() -> None:
    loaded = yaml.load('d: 2026-01-01\nflag: on\n', Loader=fsi_corpus._Loader)
    assert loaded == {"d": "2026-01-01", "flag": "on"}


def test_url_normalization_ignores_fragment_and_trailing_slash() -> None:
    assert fsi_corpus.normalize_url("https://WWW.Example.gov/a/#x") == fsi_corpus.normalize_url("https://www.example.gov/a")


def test_render_is_deterministic() -> None:
    corpus = load_base()
    assert fsi_render.outputs(corpus) == fsi_render.outputs(load_base())


def test_render_check_detects_hand_edits(tmp_path: Path) -> None:
    root = tmp_path / "specs" / "fsi"
    shutil.copytree(BASE, root)
    shutil.copytree(SCHEMA_DIR, root / "schema")
    assert fsi_render.main(["--repo", str(tmp_path), "--today", FIXTURE_TODAY.isoformat()]) == 0
    assert fsi_render.main(["--repo", str(tmp_path), "--check", "--today", FIXTURE_TODAY.isoformat()]) == 0
    index = tmp_path / fsi_render.INDEX
    index.write_text(index.read_text(encoding="utf-8") + "\nhand edit\n", encoding="utf-8")
    assert fsi_render.main(["--repo", str(tmp_path), "--check", "--today", FIXTURE_TODAY.isoformat()]) == 1


def test_render_check_detects_stale_generated_page(tmp_path: Path) -> None:
    root = tmp_path / "specs" / "fsi"
    shutil.copytree(BASE, root)
    shutil.copytree(SCHEMA_DIR, root / "schema")
    assert fsi_render.main(["--repo", str(tmp_path), "--today", FIXTURE_TODAY.isoformat()]) == 0
    orphan = tmp_path / fsi_render.PAGES / "zz.md"
    orphan.write_text(fsi_render.GENERATED_MARK + "\n# orphan\n", encoding="utf-8")
    assert fsi_render.main(["--repo", str(tmp_path), "--check", "--today", FIXTURE_TODAY.isoformat()]) == 1


def test_render_refuses_an_invalid_corpus(tmp_path: Path) -> None:
    root = tmp_path / "specs" / "fsi"
    shutil.copytree(BASE, root)
    shutil.copytree(SCHEMA_DIR, root / "schema")
    assert fsi_render.main(["--repo", str(tmp_path), "--today", "2027-01-01"]) == 1
    assert not (tmp_path / fsi_render.INDEX).exists()


def test_committed_corpus_is_valid_today() -> None:
    _, findings = fsi_corpus.validate()
    assert findings == [], "\n".join(str(f) for f in findings)


def test_committed_generated_files_match_the_corpus() -> None:
    assert fsi_render.main(["--check"]) == 0


def test_every_obligation_has_a_control() -> None:
    corpus = fsi_corpus.load()
    assert fsi_render.coverage(corpus)["obligations_without_control"] == []
