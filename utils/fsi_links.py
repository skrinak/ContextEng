from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import fsi_corpus
import truststore

truststore.inject_into_ssl()

CONTACT_ENV = "FSI_LINKCHECK_CONTACT"
TIMEOUT_S = 25
BROKEN_CODES = {404, 410}
EVALS = Path("decisions/evals")


@dataclass(frozen=True)
class Check:
    url: str
    where: str
    recorded: str
    code: int | None
    error: str | None

    @property
    def observed(self) -> str:
        if self.code is not None and 200 <= self.code < 300 and self.code != 202:
            return "ok"
        if self.code in BROKEN_CODES:
            return "broken"
        return "blocked"

    @property
    def regressed(self) -> bool:
        return self.observed == "broken" and self.recorded != "broken"


def targets(corpus: fsi_corpus.Corpus) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    for record in corpus.instruments:
        found.append((record["url"], corpus.where(record), "ok"))
    for record in corpus.obligations:
        found.append((record["source"]["url"], corpus.where(record), "ok"))
    for record in corpus.controls:
        for binding in record["aws"]:
            found.append((binding["doc"], corpus.where(record), "ok"))
    for record in corpus.holdings:
        found.append((record["url"], corpus.where(record), record["link"]["status"]))
    unique: dict[str, tuple[str, str, str]] = {}
    for url, where, recorded in found:
        key = url.split("#", 1)[0]
        unique.setdefault(key, (key, where, recorded))
    return sorted(unique.values())


def user_agent() -> str:
    contact = os.environ.get(CONTACT_ENV, "").strip()
    return f"ContextEng fsi-linkcheck {contact}".strip()


def fetch(url: str) -> tuple[int | None, str | None]:
    headers = {"User-Agent": user_agent(), "Accept": "text/html,application/pdf,*/*", "Accept-Language": "en"}
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            return response.status, None
    except urllib.error.HTTPError as error:
        return error.code, None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return None, str(error)


def run(corpus: fsi_corpus.Corpus, workers: int = 12) -> list[Check]:
    items = targets(corpus)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda item: fetch(item[0]), items))
    return [Check(url, where, recorded, code, error) for (url, where, recorded), (code, error) in zip(items, results)]


def report(checks: list[Check], today: dt.date, command: str) -> str:
    lines = [
        f"# {today.isoformat()} - FSI corpus link check",
        "",
        "> **Generated artifact**",
        f"> Produced by `{command}`. Data, not a decision record.",
        "",
        "| Observed | Recorded | HTTP | URL | First cited by |",
        "|---|---|---|---|---|",
    ]
    order = {"broken": 0, "blocked": 1, "ok": 2}
    for check in sorted(checks, key=lambda c: (order[c.observed], c.url)):
        code = str(check.code) if check.code is not None else (check.error or "error")
        lines.append(f"| {check.observed} | {check.recorded} | {code} | <{check.url}> | `{check.where}` |")
    counts = {state: sum(1 for c in checks if c.observed == state) for state in order}
    lines += [
        "",
        f"{len(checks)} addresses: {counts['ok']} ok, {counts['blocked']} blocked or unverifiable, {counts['broken']} broken.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check every address the FSI corpus cites.")
    parser.add_argument("--root", type=Path, default=fsi_corpus.DEFAULT_ROOT)
    parser.add_argument("--report", action="store_true", help="also write a dated report to decisions/evals/")
    args = parser.parse_args(argv)
    corpus = fsi_corpus.load(args.root)
    checks = run(corpus)
    for check in checks:
        if check.observed != "ok":
            detail = check.code if check.code is not None else check.error
            sys.stdout.write(f"{check.observed:8} {detail}  {check.url}  ({check.where})\n")
    regressions = [c for c in checks if c.regressed]
    for check in regressions:
        sys.stdout.write(f"REGRESSION: {check.url} is broken but recorded as {check.recorded} ({check.where})\n")
    if args.report:
        today = dt.datetime.now(dt.UTC).date()
        target = fsi_corpus.REPO / EVALS / f"{today.isoformat()}-fsi-link-check.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report(checks, today, "make fsi-links-report"), encoding="utf-8")
        sys.stdout.write(f"wrote {target.relative_to(fsi_corpus.REPO)}\n")
    ok = sum(1 for c in checks if c.observed == "ok")
    sys.stdout.write(f"fsi links: {len(checks)} checked, {ok} ok, {len(regressions)} regressions\n")
    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main())
