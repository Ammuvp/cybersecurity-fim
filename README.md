# Automated File Integrity Monitor (FIM)

## Project Overview

This project is a Python-based File Integrity Monitor (FIM) designed to detect unauthorized changes to files.

The tool uses SHA-256 cryptographic hashing to create a trusted baseline and compares the current state of a directory against that baseline.

## Features

- SHA-256 file hashing
- Baseline creation
- Modified file detection
- Created file detection
- Deleted file detection
- Command-line interface using argparse
- Input validation
- Error handling without raw stack traces
- JSON-based baseline storage

## Requirements

- Python 3.10 or later
- Linux, Windows, or macOS
- No external Python packages are required

## Installation

Clone or download the project:

```bash
git clone <YOUR-GITHUB-REPOSITORY-URL>
cd cybersecurity-fim
