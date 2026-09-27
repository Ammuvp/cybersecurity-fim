#!/usr/bin/env python3

"""
Automated File Integrity Monitor (FIM).

Creates, checks, and continuously monitors SHA-256 file integrity
baselines for files inside a selected directory.
"""

import argparse
import hashlib
import json
import sys
import time
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


def load_baseline():
    """Load the stored integrity baseline."""
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

    return baseline_data


def compare_files(baseline_files, current_files):
    """Compare baseline hashes with current file hashes."""
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

    return modified, created, deleted


def print_changes(modified, created, deleted):
    """Print detected file changes."""
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
        print("[OK] No changes detected.")


def check_integrity(directory):
    """Compare current files against the stored baseline."""
    baseline_data = load_baseline()
    baseline_files = baseline_data.get("files", {})

    current_files = collect_file_hashes(directory)

    modified, created, deleted = compare_files(
        baseline_files,
        current_files
    )

    print("\n=== File Integrity Check ===")
    print_changes(modified, created, deleted)

    print("\n=== Summary ===")
    print(f"Modified: {len(modified)}")
    print(f"Created:  {len(created)}")
    print(f"Deleted:  {len(deleted)}")

    return modified, created, deleted


def monitor_directory(directory, interval):
    """Continuously monitor a directory for file changes."""
    baseline_data = load_baseline()
    baseline_files = baseline_data.get("files", {})

    print("\n=== File Integrity Monitor ===")
    print(f"Directory: {directory}")
    print(f"Interval:  {interval} seconds")
    print("Monitoring started. Press Ctrl+C to stop.\n")

    previous_files = collect_file_hashes(directory)

    while True:
        time.sleep(interval)

        current_files = collect_file_hashes(directory)

        modified, created, deleted = compare_files(
            previous_files,
            current_files
        )

        if modified or created or deleted:
            print("\n=== CHANGE DETECTED ===")
            print_changes(modified, created, deleted)

            print("\n=== Summary ===")
            print(f"Modified: {len(modified)}")
            print(f"Created:  {len(created)}")
            print(f"Deleted:  {len(deleted)}")

            previous_files = current_files


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

    monitor_parser = subparsers.add_parser(
        "monitor",
        help="Continuously monitor a directory for changes."
    )

    monitor_parser.add_argument(
        "--directory",
        required=True,
        help="Directory to monitor."
    )

    monitor_parser.add_argument(
        "--interval",
        type=float,
        default=2,
        help="Monitoring interval in seconds (default: 2)."
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

    elif args.command == "monitor":
        if args.interval <= 0:
            print("[!] Error: Interval must be greater than 0.")
            sys.exit(1)

        monitor_directory(directory, args.interval)


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\n[!] Monitoring stopped by user.")
        sys.exit(0)

    except Exception as exc:
        print(f"[!] Error: {exc}")
        sys.exit(1)
