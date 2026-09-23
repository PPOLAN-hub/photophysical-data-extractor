#!/usr/bin/env python3
"""Build a deterministic, privacy-checked PDE ZIP for Doubao Work."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath


ALLOWED_ROOT_FILES = {
    "SKILL.md",
    "requirements.txt",
    "runtime_config.json",
    "report_config.json",
}
ALLOWED_DIRS = {"agents", "references", "scripts"}
ALLOWED_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt"}
FORBIDDEN_NAMES = {
    ".git",
    ".github",
    ".env",
    "__pycache__",
    "private-evaluation",
    "tests",
}
FORBIDDEN_TEXT = {
    "machine_python_path": re.compile(r"[A-Za-z]:[\\/](?:Tool|Users|Codex)[\\/]", re.IGNORECASE),
    "github_classic_token": re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    "github_fine_grained_token": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
}
FIXED_ZIP_TIME = (2020, 1, 1, 0, 0, 0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skill-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="PDE skill directory; defaults to the parent of scripts/.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "dist",
        help="Directory for the ZIP and SHA-256 file.",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Release tag in the form skill-vMAJOR.MINOR.PATCH.",
    )
    return parser.parse_args()


def collect_files(root: Path) -> list[tuple[Path, str]]:
    selected: list[tuple[Path, str]] = []
    for name in sorted(ALLOWED_ROOT_FILES):
        path = root / name
        if not path.is_file():
            raise FileNotFoundError(f"required package file missing: {path}")
        selected.append((path, name))

    for directory_name in sorted(ALLOWED_DIRS):
        directory = root / directory_name
        if not directory.is_dir():
            continue
        for path in sorted(item for item in directory.rglob("*") if item.is_file()):
            relative = path.relative_to(root)
            if path.is_symlink():
                raise ValueError(f"symbolic links are not allowed in the release ZIP: {relative}")
            if any(part in FORBIDDEN_NAMES or part.startswith(".") for part in relative.parts):
                continue
            if path.suffix.lower() not in ALLOWED_SUFFIXES:
                raise ValueError(f"unsupported file type in release inputs: {relative}")
            selected.append((path, PurePosixPath(*relative.parts).as_posix()))
    return selected


def privacy_check(files: list[tuple[Path, str]]) -> None:
    for path, archive_name in files:
        data = path.read_bytes()
        if b"\x00" in data:
            raise ValueError(f"binary file rejected: {archive_name}")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"non-UTF-8 file rejected: {archive_name}") from exc
        for label, pattern in FORBIDDEN_TEXT.items():
            if pattern.search(text):
                raise ValueError(f"{label} detected in {archive_name}")


def write_zip(files: list[tuple[Path, str]], output_path: Path) -> None:
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, archive_name in sorted(files, key=lambda item: item[1]):
            info = zipfile.ZipInfo(archive_name, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def validate_zip(output_path: Path) -> list[str]:
    with zipfile.ZipFile(output_path) as archive:
        names = archive.namelist()
        if "SKILL.md" not in names:
            raise ValueError("SKILL.md is not at ZIP root")
        if any(name.startswith("/") or ".." in PurePosixPath(name).parts for name in names):
            raise ValueError("unsafe ZIP path detected")
        if any(PurePosixPath(name).parts[0] in FORBIDDEN_NAMES for name in names):
            raise ValueError("forbidden directory included in ZIP")
        if len(names) != len(set(names)):
            raise ValueError("duplicate ZIP paths detected")
        return names


def main() -> int:
    args = parse_args()
    if not re.fullmatch(r"skill-v\d+\.\d+\.\d+", args.version):
        raise SystemExit("--version must match skill-vMAJOR.MINOR.PATCH")

    skill_dir = args.skill_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    release_version = args.version.removeprefix("skill-")
    output_path = output_dir / f"photophysical-data-extractor-doubao-skill-{release_version}.zip"
    checksum_path = output_path.with_suffix(output_path.suffix + ".sha256")

    files = collect_files(skill_dir)
    privacy_check(files)
    write_zip(files, output_path)
    names = validate_zip(output_path)
    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    checksum_path.write_text(f"{digest}  {output_path.name}\n", encoding="utf-8", newline="\n")

    print(
        json.dumps(
            {
                "status": "ready",
                "version": args.version,
                "zip": str(output_path),
                "sha256_file": str(checksum_path),
                "sha256": digest,
                "file_count": len(names),
                "skill_md_at_zip_root": names.count("SKILL.md") == 1,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
