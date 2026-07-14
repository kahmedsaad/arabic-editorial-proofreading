#!/usr/bin/env python3
"""Thin wrapper: python scripts/download_dataset.py ..."""

from app.cli.download_dataset import main

if __name__ == "__main__":
    raise SystemExit(main())
