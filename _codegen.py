"""stapel-attributes contract-emission harness (contract-pipeline.md §2-3).

Emits this library's one machine artifact into ``docs/``:

  docs/errors.json   generate_error_keys registry (the per-module etalon)

There is no schema.json and no flows.json here: stapel_attributes ships no
Django app, no views and no routes — it is the typed-attribute engine other
modules embed. What it DOES own is thirteen ``error.400.feature_*`` /
``error.400.description_*`` keys, registered by ``errors.py`` and translated by
``translations/errors.{ru,es}.json``, and until this harness existed they
reached a consumer only through whichever host happened to mount the library.

Usage:
    python -m stapel_attributes._codegen --out docs        # `make contract`
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _configure() -> None:
    """Configure + boot the emission instance."""
    # `python -m` prepends cwd to sys.path; strip the repo root the way the
    # flat-layout conftest does, so a sibling-named module in the checkout
    # cannot shadow an installed one.
    repo_root = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != repo_root]

    from django.conf import settings

    if not settings.configured:
        from stapel_attributes._codegen_settings import settings_kwargs

        settings.configure(**settings_kwargs())

    import django

    django.setup()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="stapel-attributes-contract",
        description="Emit this library's error-key registry (errors.json) into --out.",
    )
    parser.add_argument("--out", default="docs", help="Output directory (default: docs).")
    args = parser.parse_args(argv)

    _configure()

    from stapel_tools.codegen import emit_errors

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    errors = emit_errors(out / "errors.json")

    print(
        f"stapel-attributes contract: {errors} error keys -> {out}/",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
