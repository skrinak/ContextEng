# `utils/` — executable tooling

| Script | Purpose |
|---|---|
| `check_doc_links.py` | The reference guard — every path reference in every tracked text file, plus `decisions/` status headers and root-markdown membership. `make check-links` |
| `whiteboard-gen.sh` | Generate a hand-drawn glass-whiteboard illustration from a text CONTENT description |

Never call `python`/`pip` directly — use `uv run`. A script that writes markdown into
`decisions/` must target `decisions/evals/` with a dated filename.

Archetype: https://github.com/skrinak/groundwork/blob/main/utils/README.md
