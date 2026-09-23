# Obsidian archive integration

The user-selected archive convention is authoritative for naming, Markdown structure, index updates, conflicts, and reading style. Complete PDE files live under a separate configured output root; Obsidian stores only compact archive cards and links. The Skill must not infer or hard-code either personal path.

## First-use gate

Before the first formal extraction, require all four user selections:

1. persistent PDE output root outside the Vault;
2. Obsidian Vault root containing `.obsidian`;
3. PDE archive directory relative to that root;
4. a UTF-8 Markdown/text/YAML/JSON archive-convention file.

Configure with the selected Python 3.9+ runtime:

```text
scripts/configure_archive.py --output-root <reports-root> --vault-root <vault> --archive-dir <relative-dir> --convention <file> --confirm
```

The local configuration defaults to `~/.pde/archive.json`. Never commit it. The script validates the output root, Vault marker, convention readability, safe relative archive path, separation of report storage from the Vault, and actual write/delete permission in both roots.

Before each run, create the task directory with `scripts/prepare_output_dir.py`. Single-paper output uses `<output_root>/<year>/PDE/<doi-or-paper-id>_<title>/`; batch output uses `<output_root>/<year>/PDEmore/<date>_<topic>/`. Only `_work/` may contain transient indexes. The JSON, HTML, and DOCX passed to `archive_report.py` must be below `output_root`; otherwise the archive write is rejected.

## Per-run archive sequence

1. Validate canonical JSON and render HTML plus DOCX outside the Vault.
2. Reread the selected convention and verify its SHA-256 against the local config.
3. Produce a real-data preview without writing the Vault:

```text
scripts/archive_report.py paper_data.json --html report.html --docx report.docx --model <actual-model> --preview
```

4. On the first run, show the complete preview and planned absolute paths to the user. After confirmation, rerun with `--yes`.
5. Validate the written card with `scripts/validate_archive_md.py`.

The archive contains one Markdown card per run. Batch extraction produces one card, never one card per paper. Complete HTML, DOCX, JSON, images, and work files remain under the configured output root, outside the Vault, and are linked only when their targets exist.

## Safety invariants

- Preview must not change any Vault file or mtime.
- Missing or changed configuration blocks formal extraction/archiving; never silently select a different convention.
- Preserve manual content outside PDE stable blocks.
- Modify `_索引.md` only between configured sentinel markers; if markers are absent, append a warning section instead of overwriting content.
- A missing artifact becomes visible `⚠️ 产物缺失` text, never a dead link.
- Archive rendering may summarize or normalize display units but must not modify `paper_data.json` or decide scientific conflicts.
