#!/usr/bin/env python3
"""Check whether the selected Python runtime is ready for PDE."""
import importlib.util
import json
import shutil
import sys
from importlib import metadata


PACKAGES = {
    "pypdf": "pypdf",
    "PyMuPDF": "fitz",
    "PyYAML": "yaml",
}

OPTIONAL_PACKAGES = {
    "Pillow": "PIL",
    "numpy": "numpy",
}


def package_status(distribution, module):
    available = importlib.util.find_spec(module) is not None
    version = None
    if available:
        try:
            version = metadata.version(distribution)
        except metadata.PackageNotFoundError:
            pass
    return {"available": available, "version": version}


def main():
    packages = {
        distribution: package_status(distribution, module)
        for distribution, module in PACKAGES.items()
    }
    optional_packages = {
        distribution: package_status(distribution, module)
        for distribution, module in OPTIONAL_PACKAGES.items()
    }
    python_compatible = sys.version_info >= (3, 9)
    ready = python_compatible and all(item["available"] for item in packages.values())
    result = {
        "ready": ready,
        "python_compatible": python_compatible,
        "python_version": ".".join(str(part) for part in sys.version_info[:3]),
        "executable": sys.executable,
        "packages": packages,
        "optional_packages": optional_packages,
        "tools": {"pdftoppm": shutil.which("pdftoppm")},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
