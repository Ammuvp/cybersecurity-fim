#!/usr/bin/env python3

"""
Automated File Integrity Monitor (FIM).

Creates and checks SHA-256 integrity baselines for files
inside a selected directory.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


BASELINE_FILE = Path("fim_baseline.json")


def calculate_sha256(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256 = hashlib.sha256()

    try:
        with file_path.open("rb") as file:
            for chunk in iter(lambda: file.read(4096), b""):
                sha256.update(chunk)

        return sha256.hexdigest()

    except OSError as exc:
        raise RuntimeError(
            f"Unable to read file '{file_path}': {exc}"
        ) from exc


def collect_file_hashes(directory):
    """Calculate SHA-256 hashes for all files in a directory."""
    hashes = {}

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue

        if file_path.name == BASELINE_FILE.name:
            continue

        relative_path = file_path.relative_to(directory)

        try:
            hashes[str(relative_path)] = calculate_sha256(file_path)
        except RuntimeError as exc:
            print(f"[!] Warning: {exc}")

    return hashes


def create_baseline(directory):
    """Create and save a SHA-256 baseline for a directory."""
    hashes = collect_file_hashes(directory)

    baseline_data = {
        "directory": str(directory.resolve()),
        "algorithm": "SHA-256",
        "files": hashes,
    }

    try:
        with BASELINE_FILE.open("w", encoding="utf-8") as file:
            json.dump(baseline_data, file, indent=4)

    except OSError as exc:
        raise RuntimeError(
            f"Unable to save baseline: {exc}"
        ) from exc

    print(f"[+] Baseline created: {BASELINE_FILE}")
    print(f"[+] Files recorded: {len(hashes)}")


def check_integrity(directory):
    """Compare current files against the stored baseline."""
    if not BASELINE_FILE.exists():
        raise RuntimeError(
            f"Baseline file not found: {BASELINE_FILE}"
        )

    try:
        with BASELINE_FILE.open("r", encoding="utf-8") as file:
            baseline_data = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Unable to read baseline: {exc}"
        ) from exc

    baseline_files = baseline_data.get("files", {})
    current_files = collect_file_hashes(directory)

    modified = []
    created = []
    deleted = []

    for file_path, old_hash in baseline_files.items():
        if file_path not in current_files:
            deleted.append(file_path)
        elif current_files[file_path] != old_hash:
            modified.append(file_path)

    for file_path in current_files:
        if file_path not in baseline_files:
            created.append(file_path)

    print("\n=== File Integrity Check ===")

    if modified:
        print("\n[!] MODIFIED FILES:")
        for file_path in modified:
            print(f"    - {file_path}")

    if created:
        print("\n[+] CREATED FILES:")
        for file_path in created:
            print(f"    - {file_path}")

    if deleted:
        print("\n[-] DELETED FILES:")
        for file_path in deleted:
            print(f"    - {file_path}")

    if not modified and not created and not deleted:
        print("\n[OK] No changes detected.")

    print("\n=== Summary ===")
    print(f"Modified: {len(modified)}")
    print(f"Created:  {len(created)}")
    print(f"Deleted:  {len(deleted)}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Automated File Integrity Monitor"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True
    )

    baseline_parser = subparsers.add_parser(
        "baseline",
        help="Create a file integrity baseline."
    )

    baseline_parser.add_argument(
        "--directory",
        required=True,
        help="Directory to create the baseline for."
    )

    check_parser = subparsers.add_parser(
        "check",
        help="Check a directory against the stored baseline."
    )

    check_parser.add_argument(
        "--directory",
        required=True,
        help="Directory to check."
    )

    return parser.parse_args()


def main():
    """Run the File Integrity Monitor."""
    args = parse_arguments()

    directory = Path(args.directory).resolve()

    if not directory.exists():
        print(f"[!] Error: Directory does not exist: {directory}")
        sys.exit(1)

    if not directory.is_dir():
        print(f"[!] Error: Path is not a directory: {directory}")
        sys.exit(1)

    if args.command == "baseline":
        create_baseline(directory)

    elif args.command == "check":
        check_integrity(directory)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\n[!] Operation cancelled by user.")
        sys.exit(1)

    except Exception as exc:
        print(f"[!] Error: {exc}")
        sys.exit(1)
