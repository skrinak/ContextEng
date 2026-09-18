# `utils/` — executable tooling

| Script | Purpose |
|---|---|
| `check_doc_links.py` | The reference guard — every path reference in every tracked text file, plus `decisions/` status headers and root-markdown membership. `make check-links` |
| `fsi_corpus.py` | Loads and validates the FSI corpus in `../specs/fsi/`: schemas, references, authority hosts, jurisdictions, duplicate addresses, legislative status, quoted numbers, review dates. `make fsi-validate` |
| `fsi_render.py` | Renders the corpus to `../specs/fsi/export/corpus.json`, `../docs/FSIregulation.md` and `../docs/regulations/`; `--check` fails on drift. `make fsi-render` / `make fsi-check` |
| `fsi_links.py` | Fetches every address the corpus cites. Fails only when an address recorded as working is now dead; bot-blocked sites are reported, not failed. Set `FSI_LINKCHECK_CONTACT` to a contact address, because sec.gov refuses requests without one. `make fsi-links` |
| `whiteboard-gen.sh` | Generate a hand-drawn glass-whiteboard illustration from a text CONTENT description |

Never call `python`/`pip` directly — use `uv run`. A script that writes markdown into
`decisions/` must target `decisions/evals/` with a dated filename.

Archetype: https://github.com/skrinak/groundwork/blob/main/utils/README.md
