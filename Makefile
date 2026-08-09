# stapel-attributes — docs/llms.txt emission + drift gate (contract-pipeline.md §2-3).
#
# docs/capabilities.json here is otherwise HAND-WRITTEN (authored in the
# stapel-catalog sweep, commit 9fce193 "docs: author capabilities.json for the
# stapel-catalog sweep") — this L1 library has no gate registry and no
# docs/schema.json, nothing for a codegen step to derive axes from. It DOES
# now have a derived `surface` section (discoverability-design.md §1.2): the
# functions a product is meant to CALL instead of writing its own type
# dispatch/validation/normalization/formatting. `stapel_tools.surface . --patch`
# refreshes ONLY module/version + `surface` from docs/capabilities.meta.json,
# leaving provides/axes/extension_points/requires verbatim. Then docs/llms.txt
# (the fifth contract artifact) is rendered from the patched document.
#
# PYTHON must have stapel-tools importable (the workspace venv, or
# `pip install stapel-tools`).
PYTHON ?= python3

.PHONY: contract contract-check

# Patch `surface` (+ module/version) into docs/capabilities.json, then emit
# docs/llms.txt from the result.
#
# --budget 4500: the 36-entry surface (this L1 library IS almost entirely
# surface — see docs/capabilities.meta.json's _comment) runs ~95 tokens over
# the generator's default 4000-token ceiling. The owner's call: raise the
# ceiling, do NOT shorten intent/instead_of lines to fit — a trimmed-to-fit
# context file reads exactly like a complete one, which is the failure mode
# the hard-budget gate exists to prevent (see stapel-auth/Makefile for the
# same pattern at a larger scale).
#
# README.md is the SIXTH artifact (tracker #257): assembled by
# stapel_tools.readme from docs/readme.md (the human half — what this L1
# library is, how to think about it) plus everything emitted above. Badges,
# version, surface counts and doc links are generated, so a release cannot
# leave them behind. Edit docs/readme.md; never README.md. Several facts
# (HTTP operations, error codes, documented flows) are legitimately absent
# for this L1 library — the generator omits zero-valued rows rather than
# printing 0.
contract:
	$(PYTHON) -m stapel_tools.surface . --patch
	$(PYTHON) -m stapel_tools.llms_txt . --budget 4500
	$(PYTHON) -m stapel_tools.readme .

# Drift gate: regenerate into a temp dir and diff against the committed docs/*.
contract-check:
	$(PYTHON) -m stapel_tools.surface . --patch --check
	@tmp=$$(mktemp -d); \
	$(PYTHON) -m stapel_tools.llms_txt . --out "$$tmp" --budget 4500 || { rm -rf "$$tmp"; exit 1; }; \
	if ! diff -q docs/llms.txt "$$tmp/llms.txt" >/dev/null 2>&1; then \
		echo "DRIFT: docs/llms.txt is stale — run 'make contract' and commit it"; \
		diff docs/llms.txt "$$tmp/llms.txt" | head -20; \
		rm -rf "$$tmp"; exit 1; \
	fi; \
	rm -rf "$$tmp"; \
	$(PYTHON) -m stapel_tools.readme . --check || exit 1; \
	echo "contract-check: docs/llms.txt + README.md up to date"
