.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Targets:"
	@echo "  make check-links       Validate every path reference + decisions/ status headers + root taxonomy"
	@echo "  make check-links-test  Run the guard's own fixture suite"
	@echo "  make fsi-validate      Validate the FSI regulatory corpus in specs/fsi/"
	@echo "  make fsi-render        Regenerate docs/FSIregulation.md, docs/regulations/ and the JSON export"
	@echo "  make fsi-check         Validate, fail on generated-file drift, run the fixture suite"
	@echo "  make fsi-links         Check every address the corpus cites (network)"
	@echo "  make fsi-links-report  Same, and write a dated report to decisions/evals/"

# The taxonomy guard. Validates references in EVERY tracked text file — markdown
# links AND source comments — because source comments are where path references
# actually live and a docs-only linter cannot see them. Also lints decisions/
# status headers and root-markdown membership.
# Rationale: https://github.com/skrinak/ContextEng/blob/main/docs/REPOSITORY_TAXONOMY.md
.PHONY: check-links
check-links:
	uv run --no-project python3 utils/check_doc_links.py

# The guard's own guard. Do not skip this: the checker this replaced had no tests,
# which is exactly how it reported "OK" through a restructure that broke ~282 refs.
.PHONY: check-links-test
check-links-test:
	uv run --no-project --with pytest python3 -m pytest utils/tests/test_check_doc_links.py -q

FSI_DEPS := --with 'pyyaml>=6,<7' --with 'jsonschema>=4.23,<5'
FSI_RUN := uv run --no-project $(FSI_DEPS) python3

.PHONY: fsi-validate
fsi-validate:
	$(FSI_RUN) utils/fsi_corpus.py

.PHONY: fsi-render
fsi-render:
	$(FSI_RUN) utils/fsi_render.py

.PHONY: fsi-check
fsi-check:
	$(FSI_RUN) utils/fsi_corpus.py
	$(FSI_RUN) utils/fsi_render.py --check
	uv run --no-project $(FSI_DEPS) --with pytest python3 -m pytest utils/tests/test_fsi_corpus.py -q

.PHONY: fsi-links
fsi-links:
	uv run --no-project $(FSI_DEPS) --with truststore python3 utils/fsi_links.py

.PHONY: fsi-links-report
fsi-links-report:
	uv run --no-project $(FSI_DEPS) --with truststore python3 utils/fsi_links.py --report
