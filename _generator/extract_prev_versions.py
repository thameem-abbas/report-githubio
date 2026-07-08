#!/usr/bin/env python3
"""Extract the previous version of each report's entry HTML from git history.

For each report that has been modified at least once, writes the prior version
as <entry>.prev.html alongside the current file.
"""

import json
import subprocess
from pathlib import Path

REPORTS_DIR = Path("reports")


def get_commits_for_path(path):
    """Return list of commit SHAs that touched this path, newest first."""
    result = subprocess.run(
        ["git", "log", "--follow", "--format=%H", "--", str(path)],
        capture_output=True, text=True,
    )
    return [sha for sha in result.stdout.strip().split("\n") if sha]


def get_file_at_commit(sha, path):
    """Return file contents at a specific commit, or None if not found."""
    result = subprocess.run(
        ["git", "show", f"{sha}:{path}"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return result.stdout
    return None


def find_entry_file(report_dir):
    """Determine the entry HTML file for a report."""
    meta_path = report_dir / "meta.json"
    entry_file = "report.html"
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)
        entry_file = meta.get("entry", entry_file)

    html_path = report_dir / entry_file
    if html_path.exists():
        return html_path

    html_files = list(report_dir.glob("*.html"))
    return html_files[0] if html_files else None


def main():
    if not REPORTS_DIR.exists():
        return

    extracted = 0
    for category_dir in sorted(REPORTS_DIR.iterdir()):
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue
        for report_dir in sorted(category_dir.iterdir()):
            if not report_dir.is_dir() or report_dir.name.startswith("."):
                continue

            entry_path = find_entry_file(report_dir)
            if not entry_path:
                continue

            commits = get_commits_for_path(entry_path)
            if len(commits) < 2:
                continue

            prev_content = get_file_at_commit(commits[1], str(entry_path))
            if not prev_content:
                continue

            prev_path = entry_path.with_suffix(f".prev{entry_path.suffix}")
            prev_path.write_text(prev_content)
            extracted += 1
            print(f"  Extracted previous version: {prev_path}")

    print(f"Extracted {extracted} previous version(s)")


if __name__ == "__main__":
    main()
