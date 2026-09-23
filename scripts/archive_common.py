#!/usr/bin/env python3
"""Shared deterministic helpers for PDE local output and Obsidian configuration."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


DEFAULT_USER_CONFIG = Path.home() / ".pde" / "archive.json"
PROJECT_CONFIG_NAME = ".pde-archive.json"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_config(explicit=None, cwd=None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    user_config = DEFAULT_USER_CONFIG
    if user_config.is_file():
        return user_config.resolve()
    project_config = Path(cwd or Path.cwd()) / PROJECT_CONFIG_NAME
    if project_config.is_file():
        return project_config.resolve()
    raise FileNotFoundError(
        "PDE local configuration is required. Run scripts/configure_archive.py before extraction."
    )


def load_config(explicit=None, cwd=None) -> tuple[Path, dict]:
    path = resolve_config(explicit, cwd)
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("archive config root must be an object")
    validate_config(config, require_write=False)
    convention = Path(config["convention_path"]).expanduser().resolve()
    digest = file_sha256(convention)
    if digest != config.get("convention_sha256"):
        raise ValueError(
            "archive convention changed after configuration; reconfigure and preview before archiving"
        )
    return path, config


def validate_config(config: dict, require_write=True) -> None:
    required = ("output_root", "vault_root", "archive_dir", "convention_path", "convention_sha256")
    missing = [name for name in required if not config.get(name)]
    if missing:
        raise ValueError("archive config missing: " + ", ".join(missing))
    vault = Path(config["vault_root"]).expanduser().resolve()
    if not vault.is_dir() or not (vault / ".obsidian").is_dir():
        raise ValueError("vault_root must exist and contain a .obsidian directory")
    output_root = Path(config["output_root"]).expanduser().resolve()
    if not output_root.is_dir():
        raise ValueError("output_root must exist and be a directory")
    if output_root == vault or vault in output_root.parents or output_root in vault.parents:
        raise ValueError("output_root and the Obsidian Vault must be separate directory trees")
    archive_dir = Path(config["archive_dir"])
    if archive_dir.is_absolute() or ".." in archive_dir.parts:
        raise ValueError("archive_dir must be a safe path relative to vault_root")
    convention = Path(config["convention_path"]).expanduser().resolve()
    if not convention.is_file():
        raise ValueError("archive convention file does not exist")
    text = convention.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError("archive convention file is empty")
    if len(text) > 60000:
        raise ValueError("archive convention exceeds the 60000-character safety limit")
    if require_write:
        output_probe = output_root / ".pde-output-write-test"
        output_probe.write_text("ok\n", encoding="utf-8")
        output_probe.unlink()
        target = vault / archive_dir
        target.mkdir(parents=True, exist_ok=True)
        probe = target / ".pde-write-test"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink()


def require_under_output_root(path: Path, config: dict, *, must_exist=True) -> Path:
    """Return a resolved deliverable path only when it is stored under output_root."""
    resolved = path.expanduser().resolve()
    output_root = Path(config["output_root"]).expanduser().resolve()
    if resolved != output_root and output_root not in resolved.parents:
        raise ValueError(f"deliverable is outside configured output_root: {resolved}")
    if must_exist and not resolved.is_file():
        raise FileNotFoundError(f"deliverable does not exist: {resolved}")
    return resolved


def write_json_atomic(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)
