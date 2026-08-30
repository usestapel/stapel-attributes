"""The wheel gate: every package on disk is declared in pyproject.

stapel-attributes 0.6.0 shipped a wheel whose ``types/__init__.py`` imported
``stapel_attributes.types.group`` — a package the wheel did not contain,
because ``[tool.setuptools] packages`` is an explicit list and the new type was
not added to it. Every import of the library failed on that release, and CI
never saw it: CI installs ``-e .``, which reads the source tree, where the
package is right there.

So the assertion is not "does it import" (it always does, from source) but
"is what is on disk what would be built".
"""
from __future__ import annotations

import os
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _declared_packages() -> set:
    with open(os.path.join(ROOT, "pyproject.toml"), "rb") as fh:
        return set(tomllib.load(fh)["tool"]["setuptools"]["packages"])


def _packages_on_disk() -> set:
    """Every directory under the package root that is an importable package."""
    found = {"stapel_attributes"}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".") and d not in {"__pycache__", "node_modules",
                                                   "build", "dist", "static_src"}
        ]
        if "__init__.py" not in filenames or dirpath == ROOT:
            continue
        rel = os.path.relpath(dirpath, ROOT).replace(os.sep, ".")
        found.add("stapel_attributes." + rel)
    return found


def test_every_package_on_disk_is_declared_in_pyproject():
    missing = _packages_on_disk() - _declared_packages()
    assert not missing, (
        "these packages exist in the source tree but are NOT in "
        "pyproject.toml [tool.setuptools] packages, so the built wheel will not "
        "contain them: " + ", ".join(sorted(missing))
    )


def test_every_declared_package_exists_on_disk():
    stale = _declared_packages() - _packages_on_disk()
    assert not stale, (
        "pyproject.toml declares packages that do not exist: "
        + ", ".join(sorted(stale))
    )
