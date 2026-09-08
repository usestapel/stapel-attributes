# stapel-attributes — contract emission + drift gate (contract-pipeline.md §2-3).
#
# FIRST, docs/errors.json — the error-key registry, emitted by the same
# `generate_error_keys` path every sibling library uses (stapel_tools.codegen's
# emit_errors, driven here by _codegen.py / _codegen_settings.py). This library
# has no Django app, so `autodiscover_modules('errors')` can never reach its
# errors module; the harness names it in `STAPEL_ERROR_MODULES`, core's seam for
# exactly that, which is what makes the artifact deterministic instead of a side
# effect of import order. 55 keys: the 13 this library owns plus the 42
# cross-cutting ones core seeds into every registry — the same shape as all 26
# siblings, and byte-identical to their entries for the shared codes.
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
# --budget 7000: the 59-entry surface (this L1 library IS almost entirely
# surface — see docs/capabilities.meta.json's _comment) runs over the
# generator's default 4000-token ceiling; 0.5.0's rules + vocabulary seams
# added seven more entries, and 0.8.0's visibility axis + source-level guard
# added twelve. 6400 -> 7000 is the errors section: docs/errors.json exists as
# of 0.9.4, so llms.txt now carries the 55-key error table (734 tokens) it had
# no artifact to render before. The owner's call, taken four times now: raise the ceiling, do
# NOT shorten intent/instead_of lines to fit — a trimmed-to-fit context file
# reads exactly like a complete one, which is the failure mode the hard-budget
# gate exists to prevent (see stapel-auth/Makefile for the same pattern at a
# larger scale). The visibility entries are the last ones that should ever be
# trimmed: they are what a consumer reads to find out that redaction exists
# before writing its own leak.
#
# README.md is the SIXTH artifact (tracker #257): assembled by
# stapel_tools.readme from docs/readme.md (the human half — what this L1
# library is, how to think about it) plus everything emitted above. Badges,
# version, surface counts and doc links are generated, so a release cannot
# leave them behind. Edit docs/readme.md; never README.md. Several facts
# (HTTP operations, error codes, documented flows) are legitimately absent
# for this L1 library — the generator omits zero-valued rows rather than
# printing 0.
#
# errors.json is emitted BEFORE llms.txt and README.md, both of which read it:
# the error-key table in the context file and the error-code count in the badge
# row come from the artifact, so emitting it second would ship a context file
# describing the registry as it was one release ago.
contract:
	$(PYTHON) -m stapel_attributes._codegen --out docs
	$(PYTHON) -m stapel_tools.surface . --patch
	$(PYTHON) -m stapel_tools.llms_txt . --budget 7000
	$(PYTHON) -m stapel_tools.readme .

# Drift gate: regenerate into a temp dir and diff against the committed docs/*.
contract-check:
	@tmp=$$(mktemp -d); \
	$(PYTHON) -m stapel_attributes._codegen --out "$$tmp" || { rm -rf "$$tmp"; exit 1; }; \
	if ! diff -q docs/errors.json "$$tmp/errors.json" >/dev/null 2>&1; then \
		echo "DRIFT: docs/errors.json is stale — run 'make contract' and commit it"; \
		diff docs/errors.json "$$tmp/errors.json" | head -20; \
		rm -rf "$$tmp"; exit 1; \
	fi; \
	rm -rf "$$tmp"
	$(PYTHON) -m stapel_tools.surface . --patch --check
	@tmp=$$(mktemp -d); \
	$(PYTHON) -m stapel_tools.llms_txt . --out "$$tmp" --budget 7000 || { rm -rf "$$tmp"; exit 1; }; \
	if ! diff -q docs/llms.txt "$$tmp/llms.txt" >/dev/null 2>&1; then \
		echo "DRIFT: docs/llms.txt is stale — run 'make contract' and commit it"; \
		diff docs/llms.txt "$$tmp/llms.txt" | head -20; \
		rm -rf "$$tmp"; exit 1; \
	fi; \
	rm -rf "$$tmp"; \
	$(PYTHON) -m stapel_tools.readme . --check || exit 1; \
	echo "contract-check: docs/errors.json + docs/llms.txt + README.md up to date"
