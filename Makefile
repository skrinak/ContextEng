.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Targets:"
	@echo "  make check-links       Validate every path reference + decisions/ status headers + root taxonomy"
	@echo "  make check-links-test  Run the guard's own fixture suite"

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
