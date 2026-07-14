"""Download a dataset object from local tree or GCS."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import settings
from app.data.gcs_loader import GCSDatasetLoader
from app.data.loader import is_gcs_path, parse_gcs_uri, sha256_file
from app.data.local_loader import LocalDatasetLoader
from app.data.manifest import manifest_gcs_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download dataset JSONL (local or GCS)")
    parser.add_argument("--source", required=True, help="Relative key or gs:// URI")
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dataset-id", default=None, help="Optional manifest checksum check")
    parser.add_argument("--backend", choices=["local", "gcs", "auto"], default="auto")
    args = parser.parse_args(argv)

    dest = args.destination
    if dest.exists() and not args.overwrite:
        print(f"Destination exists: {dest} (pass --overwrite)", file=sys.stderr)
        return 1

    backend = args.backend
    if backend == "auto":
        backend = "gcs" if is_gcs_path(args.source) or settings.data_backend == "gcs" else "local"

    if backend == "gcs" or is_gcs_path(args.source):
        if is_gcs_path(args.source):
            bucket, key = parse_gcs_uri(args.source)
            loader = GCSDatasetLoader(bucket=bucket, prefix="")
            source_key = key
        else:
            loader = GCSDatasetLoader(
                bucket=settings.gcs_data_bucket,
                prefix=settings.gcs_data_prefix or "",
            )
            source_key = args.source
    else:
        loader = LocalDatasetLoader(root=settings.local_data_dir)
        source_key = args.source

    if not loader.exists(source_key if not is_gcs_path(args.source) else args.source):
        # exists() for GCS with full URI
        check = args.source if is_gcs_path(args.source) else source_key
        if not loader.exists(check):
            print(f"Source not found: {args.source}", file=sys.stderr)
            return 2

    path = loader.download_file(
        args.source if is_gcs_path(args.source) else source_key,
        dest,
    )

    checksum_ok = None
    if args.dataset_id and isinstance(loader, GCSDatasetLoader):
        try:
            raw = loader.read_text(manifest_gcs_path(args.dataset_id))
            manifest = json.loads(raw)
            expected = manifest.get("checksum_sha256")
            if expected:
                checksum_ok = sha256_file(path) == expected
                if not checksum_ok:
                    print("WARNING: checksum mismatch vs manifest", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"Manifest check skipped: {exc}", file=sys.stderr)

    print(
        json.dumps(
            {
                "downloaded": str(path),
                "size_bytes": path.stat().st_size,
                "checksum_sha256": sha256_file(path),
                "checksum_ok": checksum_ok,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
