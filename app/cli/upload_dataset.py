"""Upload a JSONL dataset to local tree or GCS with manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import settings
from app.data.gcs_loader import GCSDatasetLoader
from app.data.loader import (
    is_gcs_path,
    looks_like_secret,
    reject_private_to_public,
    sha256_file,
    validate_jsonl_file,
)
from app.data.local_loader import LocalDatasetLoader
from app.data.manifest import build_manifest, manifest_gcs_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Upload dataset JSONL (local or GCS). "
            "External news corpora are NOT Al Jazeera house-style data."
        )
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument(
        "--destination",
        required=True,
        help="Relative key under bucket/local root, e.g. public/clean/foo.jsonl",
    )
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--name", default=None)
    parser.add_argument(
        "--source-type",
        default="external_public",
        help="external_public | synthetic | editor_feedback | before_after | ...",
    )
    parser.add_argument("--license", default="documented-separately", dest="license_name")
    parser.add_argument(
        "--notes",
        default="Not Al Jazeera house-style data",
    )
    parser.add_argument("--contains-private-gold", action="store_true")
    parser.add_argument("--backend", choices=["local", "gcs", "auto"], default="auto")
    parser.add_argument("--yes", action="store_true", help="Skip interactive confirm for large files")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)

    source = args.source.resolve()
    if not source.exists():
        print(f"Source not found: {source}", file=sys.stderr)
        return 1
    if looks_like_secret(source):
        print("Refusing to upload secrets / credential-like files.", file=sys.stderr)
        return 2

    try:
        reject_private_to_public(
            args.destination, contains_private_gold=args.contains_private_gold
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    size = source.stat().st_size
    if size > 1024**3 and not args.yes:
        print(
            f"File is {size / 1024**3:.2f} GiB. Re-run with --yes to confirm upload.",
            file=sys.stderr,
        )
        return 3

    try:
        count = validate_jsonl_file(source)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 4

    backend = args.backend
    if backend == "auto":
        backend = "gcs" if (
            settings.data_backend == "gcs" or args.destination.startswith("gs://")
        ) else settings.data_backend

    if backend == "gcs" or is_gcs_path(args.destination):
        loader = GCSDatasetLoader(
            bucket=settings.gcs_data_bucket,
            prefix=settings.gcs_data_prefix or "",
            cache_dir=None,
        )
    else:
        loader = LocalDatasetLoader(root=settings.local_data_dir)

    if loader.exists(args.destination) and not args.overwrite:
        print(
            f"Destination exists: {args.destination} (pass --overwrite)",
            file=sys.stderr,
        )
        return 5

    uri = loader.upload_file(source, args.destination)
    manifest = build_manifest(
        dataset_id=args.dataset_id,
        name=args.name,
        source=source,
        storage_path=args.destination,
        source_type=args.source_type,
        license_name=args.license_name,
        notes=args.notes,
        contains_private_gold=args.contains_private_gold,
    )
    manifest_path = manifest_gcs_path(args.dataset_id)
    if isinstance(loader, GCSDatasetLoader):
        m_uri = loader.upload_manifest(
            manifest.model_dump(mode="json"),
            manifest_path,
        )
    else:
        m_uri = loader.upload_file(
            _write_temp_manifest(manifest),
            manifest_path,
        )

    print(
        json.dumps(
            {
                "dataset_uri": uri,
                "manifest_uri": m_uri,
                "record_count": count,
                "size_bytes": size,
                "checksum_sha256": sha256_file(source),
                "backend": backend,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _write_temp_manifest(manifest) -> Path:
    from tempfile import NamedTemporaryFile

    tmp = NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    tmp.write(json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2))
    tmp.write("\n")
    tmp.close()
    return Path(tmp.name)


if __name__ == "__main__":
    raise SystemExit(main())
