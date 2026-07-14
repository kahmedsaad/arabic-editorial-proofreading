#!/usr/bin/env python3
"""Thin wrapper: python scripts/upload_dataset.py ..."""

from app.cli.upload_dataset import main

if __name__ == "__main__":
    raise SystemExit(main())
