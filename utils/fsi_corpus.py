from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import jsonschema
import yaml
from referencing import Registry, Resource

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO / "specs" / "fsi"
SCHEMA_BASE = "https://github.com/skrinak/ContextEng/specs/fsi/schema/"
REVIEW_HORIZON_DAYS = 366
IN_FORCE = "in_force"
STATUSES_NEEDING_NOTE = {"proposed", "not_enacted", "withdrawn", "repealed", "superseded", "enacted", "unverified"}
KINDS_NEEDING_STATUS = {"bill", "proposal"}
NUMBER_WORDS = {
    1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
    9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen",
    15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty",
}

Record = dict[str, Any]
STANDALONE_NUMBER = re.compile(r"(?<![\w.\-/(§])\d+(?![\w.\-/)])")


class _Loader(yaml.SafeLoader):
    pass


_Loader.yaml_implicit_resolvers = {
    key: [r for r in resolvers if r[0] not in ("tag:yaml.org,2002:timestamp", "tag:yaml.org,2002:bool")]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Loader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|false)$"), list("tf"))


@dataclass(frozen=True)
class Finding:
    rule: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: [{self.rule}] {self.message}"


@dataclass
class Corpus:
    root: Path
    registry: Record
    instruments: list[Record] = field(default_factory=list)
    obligations: list[Record] = field(default_factory=list)
    controls: list[Record] = field(default_factory=list)
    holdings: list[Record] = field(default_factory=list)
    origin: dict[int, str] = field(default_factory=dict)

    def where(self, record: Record) -> str:
        label = record.get("id") or record.get("title") or "?"
        return f"{self.origin.get(id(record), '?')}#{label}"


def _read_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return yaml.load(handle, Loader=_Loader)


def load(root: Path = DEFAULT_ROOT) -> Corpus:
    corpus = Corpus(root=root, registry=_read_yaml(root / "registry.yaml") or {})

    def rel(path: Path) -> str:
        return path.relative_to(root).as_posix()

    for path in sorted((root / "instruments").glob("*.yaml")):
        record = _read_yaml(path)
        corpus.instruments.append(record)
        corpus.origin[id(record)] = rel(path)
    for path in sorted((root / "obligations").glob("*.yaml")):
        for record in _read_yaml(path) or []:
            corpus.obligations.append(record)
            corpus.origin[id(record)] = rel(path)
    for path in sorted((root / "controls").glob("*.yaml")):
        record = _read_yaml(path)
        corpus.controls.append(record)
        corpus.origin[id(record)] = rel(path)
    holding_path = root / "holding.yaml"
    if holding_path.exists():
        for record in _read_yaml(holding_path) or []:
            corpus.holdings.append(record)
            corpus.origin[id(record)] = rel(holding_path)
    return corpus


def _schema_registry(schema_dir: Path) -> Registry:
    resources = []
    for path in sorted(schema_dir.glob("*.schema.json")):
        contents = json.loads(path.read_text(encoding="utf-8"))
        resources.append((SCHEMA_BASE + path.name, Resource.from_contents(contents)))
    return Registry().with_resources(resources)


def _host(url: str) -> str:
    return (urlsplit(url).hostname or "").lower()


def _host_allowed(host: str, allowed: list[str]) -> bool:
    return any(host == a or host.endswith("." + a) for a in allowed)


def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), (parts.hostname or "").lower(), path, parts.query, ""))


def _numbers_in_duration(duration: str) -> list[int]:
    return [int(n) for n in re.findall(r"\d+", duration)]


def _quote_mentions(quote: str, number: int) -> bool:
    text = quote.lower()
    if re.search(rf"(?<![\w.(\-/]){number}(?![\w)\-/])", text):
        return True
    word = NUMBER_WORDS.get(number)
    return bool(word and re.search(rf"\b{word}\b", text))


def _parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


class Validator:
    def __init__(self, corpus: Corpus, today: dt.date, schema_dir: Path | None = None) -> None:
        self.corpus = corpus
        self.today = today
        self.schema_dir = schema_dir or corpus.root / "schema"
        self.findings: list[Finding] = []

    def add(self, rule: str, where: str, message: str) -> None:
        self.findings.append(Finding(rule, where, message))

    def run(self) -> list[Finding]:
        self._schemas()
        if any(f.rule == "schema" for f in self.findings):
            return self.findings
        self._registry()
        self._ids()
        self._references()
        self._hosts_and_jurisdictions()
        self._duplicate_urls()
        self._statuses()
        self._obligation_coverage()
        self._numbers_are_quoted()
        self._verification()
        return self.findings

    def _schemas(self) -> None:
        registry = _schema_registry(self.schema_dir)
        c = self.corpus

        def check(schema_name: str, record: Any, where: str) -> None:
            validator = jsonschema.Draft202012Validator(
                registry.contents(SCHEMA_BASE + schema_name), registry=registry
            )
            for error in sorted(validator.iter_errors(record), key=lambda e: list(e.absolute_path)):
                location = "/".join(str(p) for p in error.absolute_path) or "(root)"
                self.add("schema", where, f"{location}: {error.message}")

        check("registry.schema.json", c.registry, "registry.yaml")
        for kind, records in (
            ("instrument", c.instruments),
            ("obligation", c.obligations),
            ("control", c.controls),
            ("holding", c.holdings),
        ):
            for record in records:
                if not isinstance(record, dict):
                    self.add("schema", c.origin.get(id(record), "?"), f"{kind} record is not a mapping")
                    continue
                check(f"{kind}.schema.json", record, c.where(record))

    def _registry(self) -> None:
        jurisdictions = self.corpus.registry["jurisdictions"]
        for key, authority in self.corpus.registry["authorities"].items():
            if authority["jurisdiction"] not in jurisdictions:
                self.add("dangling-ref", f"registry.yaml#{key}", f"unknown jurisdiction {authority['jurisdiction']!r}")

    def _ids(self) -> None:
        c = self.corpus
        counts = Counter(r["id"] for r in c.instruments + c.obligations + c.controls)
        for record in c.instruments + c.obligations + c.controls:
            if counts[record["id"]] > 1:
                self.add("duplicate-id", c.where(record), f"id {record['id']!r} is used {counts[record['id']]} times")

    def _references(self) -> None:
        c = self.corpus
        authorities = c.registry["authorities"]
        instruments = {r["id"] for r in c.instruments}
        obligations = {r["id"] for r in c.obligations}
        for record in c.instruments + c.holdings:
            if record["authority"] not in authorities:
                self.add("dangling-ref", c.where(record), f"unknown authority {record['authority']!r}")
        for record in c.instruments:
            target = record.get("superseded_by")
            if target and target not in instruments:
                self.add("dangling-ref", c.where(record), f"superseded_by {target!r} is not an instrument")
        for record in c.obligations:
            if record["instrument"] not in instruments:
                self.add("dangling-ref", c.where(record), f"instrument {record['instrument']!r} does not exist")
            for other in record.get("see_also", []):
                if other not in obligations:
                    self.add("dangling-ref", c.where(record), f"see_also {other!r} is not an obligation")
        for record in c.controls:
            for target in record["satisfies"]:
                if target not in obligations:
                    self.add("dangling-ref", c.where(record), f"satisfies {target!r}, which is not an obligation")

    def _allowed_hosts(self, authority_key: str) -> list[str]:
        registry = self.corpus.registry
        authority = registry["authorities"].get(authority_key)
        if authority is None:
            return []
        jurisdiction = registry["jurisdictions"].get(authority["jurisdiction"], {})
        return list(authority["hosts"]) + list(jurisdiction.get("publisher_hosts", []))

    def _hosts_and_jurisdictions(self) -> None:
        c = self.corpus
        authorities = c.registry["authorities"]
        jurisdictions = c.registry["jurisdictions"]
        instruments = {r["id"]: r for r in c.instruments}
        for record in c.instruments + c.holdings:
            authority = authorities.get(record["authority"])
            if authority is None:
                continue
            if record["jurisdiction"] not in jurisdictions:
                self.add("dangling-ref", c.where(record), f"unknown jurisdiction {record['jurisdiction']!r}")
            elif record["jurisdiction"] != authority["jurisdiction"]:
                self.add(
                    "jurisdiction-mismatch",
                    c.where(record),
                    f"filed under {record['jurisdiction']} but {authority['name']} is a {authority['jurisdiction']} authority",
                )
            host = _host(record["url"])
            if not _host_allowed(host, self._allowed_hosts(record["authority"])):
                self.add(
                    "authority-host",
                    c.where(record),
                    f"{host} is neither a {authority['name']} host nor an official {authority['jurisdiction']} publisher",
                )
        for record in c.obligations:
            instrument = instruments.get(record["instrument"])
            if instrument is None:
                continue
            host = _host(record["source"]["url"])
            if not _host_allowed(host, self._allowed_hosts(instrument["authority"])):
                self.add(
                    "authority-host",
                    c.where(record),
                    f"source host {host} is not a host of {instrument['authority']} or an official publisher for it",
                )
        vendor_hosts = [h for v in c.registry["vendors"].values() for h in v["hosts"]]
        for record in c.controls:
            for binding in record["aws"]:
                host = _host(binding["doc"])
                if not _host_allowed(host, vendor_hosts):
                    self.add("authority-host", c.where(record), f"vendor doc host {host} is not a registered vendor host")

    def _duplicate_urls(self) -> None:
        c = self.corpus
        seen: dict[str, Record] = {}
        for record in c.instruments + c.holdings:
            key = normalize_url(record["url"])
            if key in seen:
                self.add(
                    "duplicate-url",
                    c.where(record),
                    f"same address as {c.where(seen[key])}; two distinct entries cannot cite one source",
                )
            else:
                seen[key] = record

    def _statuses(self) -> None:
        c = self.corpus
        instruments = {r["id"]: r for r in c.instruments}
        for record in c.instruments + c.holdings:
            status = record.get("status")
            if record.get("kind") in KINDS_NEEDING_STATUS and status is None:
                self.add("status-missing", c.where(record), f"a {record['kind']} must state whether it became law")
            if status in STATUSES_NEEDING_NOTE and not record.get("status_note"):
                self.add("status-missing", c.where(record), f"status {status!r} needs a status_note saying how it was established")
        for record in c.instruments:
            if record["status"] == "superseded" and not record.get("superseded_by"):
                self.add("status-missing", c.where(record), "superseded instruments must name superseded_by")
        for record in c.obligations:
            instrument = instruments.get(record["instrument"])
            if instrument is not None and instrument["status"] != IN_FORCE:
                self.add(
                    "not-in-force",
                    c.where(record),
                    f"obligations derive only from law in force; {instrument['id']} is {instrument['status']!r}",
                )

    def _obligation_coverage(self) -> None:
        c = self.corpus
        with_obligations = {r["instrument"] for r in c.obligations}
        for record in c.instruments:
            if record["id"] not in with_obligations:
                self.add(
                    "citation-without-obligation",
                    c.where(record),
                    "an instrument must carry at least one obligation; a bare citation belongs in holding.yaml",
                )

    def _numbers_are_quoted(self) -> None:
        c = self.corpus
        for record in c.obligations:
            quote = record["source"]["quote"]
            retention = record.get("retention") or {}
            for key in ("period", "accessible_period", "extended_period"):
                value = retention.get(key)
                if value is None:
                    continue
                for number in _numbers_in_duration(value):
                    if not _quote_mentions(quote, number):
                        self.add(
                            "unquoted-number",
                            c.where(record),
                            f"retention.{key} {value} states {number}, which the source quote does not contain",
                        )
            if retention and not any(retention.get(k) for k in ("period", "indefinite", "accessible_period")):
                self.add("unquoted-number", c.where(record), "retention needs a period, an accessible_period or indefinite: true")
            for number in STANDALONE_NUMBER.findall(record["requirement"]):
                if not _quote_mentions(quote, int(number)):
                    self.add(
                        "unquoted-number",
                        c.where(record),
                        f"requirement states {number}, which the source quote does not contain",
                    )

    def _verification(self) -> None:
        c = self.corpus
        for record in c.instruments + c.obligations + c.controls:
            verified = record["verified"]
            verified_on = _parse_date(verified["date"])
            review_due = _parse_date(record["review_due"])
            if verified_on > self.today:
                self.add("stale", c.where(record), f"verified date {verified_on} is in the future")
            if review_due < self.today:
                self.add("stale", c.where(record), f"review was due {review_due}; re-verify against the primary source")
            if (review_due - verified_on).days > REVIEW_HORIZON_DAYS:
                self.add(
                    "stale",
                    c.where(record),
                    f"review_due is more than {REVIEW_HORIZON_DAYS} days after verification",
                )
            if record["confidence"] == "high" and "source" in record:
                retrieved = _parse_date(record["source"]["retrieved"])
                if retrieved > verified_on:
                    self.add("confidence", c.where(record), "source retrieved after the verification date")


def validate(root: Path = DEFAULT_ROOT, today: dt.date | None = None) -> tuple[Corpus, list[Finding]]:
    corpus = load(root)
    findings = Validator(corpus, today or dt.datetime.now(dt.UTC).date()).run()
    return corpus, findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the FSI regulatory corpus.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--today", type=dt.date.fromisoformat, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    corpus, findings = validate(args.root, args.today)
    if args.json:
        json.dump([f.__dict__ for f in findings], sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        for finding in findings:
            sys.stdout.write(f"{finding}\n")
        counts = (
            f"{len(corpus.instruments)} instruments, {len(corpus.obligations)} obligations, "
            f"{len(corpus.controls)} controls, {len(corpus.holdings)} unmigrated references"
        )
        sys.stdout.write(f"fsi corpus {'OK' if not findings else 'FAILED'}: {counts}\n")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
