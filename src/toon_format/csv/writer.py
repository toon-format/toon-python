"""Write CSV strings to files and optionally package them into a ZIP archive.

This module provides a convenience function `write_csvs` that takes a mapping
of names to CSV text and writes them to disk. It supports two layout modes:

- flat: write all CSVs into a single output directory with sanitized filenames
- nested: create subdirectories from dot-separated keys and place CSVs there

The function also optionally prefixes files with a UTF-8 BOM and creates a
zip archive containing the output directory.
"""

from pathlib import Path
import zipfile
import re
from typing import Dict


def write_csvs(csvs: Dict[str, str], out_dir: str = 'toon_csvs', zip_name: str = 'toon_csvs.zip', bom: bool = True, flat: bool = True):
    """Write CSV content to disk and produce an optional ZIP archive.

    Args:
        csvs: Mapping of name -> CSV text. Names may be dot-separated paths
              (e.g., "parent.child") when `flat` is False.
        out_dir: Directory where CSV files will be created.
        zip_name: Path to the ZIP file to create containing the output files.
        bom: If True, write files using `utf-8-sig` (include BOM). Otherwise use
             plain `utf-8`.
        flat: If True, produce sanitized filenames in a single directory.
              If False, treat names as hierarchical paths and create nested
              directories accordingly.

    Returns:
        A tuple `(out_path, zip_path)` where `out_path` is a `pathlib.Path` to
        the output directory and `zip_path` is a `pathlib.Path` to the created
        ZIP file.
    """

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, csv in csvs.items():
        if flat:
            safe_name = re.sub(r"[^A-Za-z0-9_.-]", "", name)
            filename = safe_name + '.csv'
            path = out / filename
        else:
            parts = name.split('.') if isinstance(name, str) else [str(name)]
            subdir = out.joinpath(*parts[:-1]) if len(parts) > 1 else out
            subdir.mkdir(parents=True, exist_ok=True)
            filename = parts[-1] + '.csv'
            path = subdir / filename
        enc = 'utf-8-sig' if bom else 'utf-8'
        with open(path, 'w', encoding=enc, newline='') as f:
            f.write(csv)
    # create zip
    zip_path = Path(zip_name)
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for file in out.rglob('*'):
            if file.is_file():
                zf.write(file, arcname=file.relative_to(out))
    return out, zip_path
