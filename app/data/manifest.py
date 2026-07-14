"""Dataset manifest helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.data.loader import sha256_file, validate_jsonl_file
from app.data.models import DatasetManifest


def build_manifest(
    *,
    dataset_id: str,
    name: str | None,
    source: Path,
    storage_path: str,
    source_type: str,
    license_name: str,
    notes: str = "Not Al Jazeera house-style data",
    contains_full_text: bool = True,
    contains_personal_data: bool = False,
    contains_private_gold: bool = False,
    version: str = "1.0.0",
) -> DatasetManifest:
    record_count = validate_jsonl_file(source)
    return DatasetManifest(
        dataset_id=dataset_id,
        name=name or dataset_id,
        version=version,
        storage_path=storage_path,
        format="jsonl",
        language="ar",
        record_count=record_count,
        size_bytes=source.stat().st_size,
        license=license_name,
        source_type=source_type,
        contains_full_text=contains_full_text,
        contains_personal_data=contains_personal_data,
        contains_private_gold=contains_private_gold,
        created_at=datetime.now(timezone.utc),
        checksum_sha256=sha256_file(source),
        notes=notes,
    )


def manifest_gcs_path(dataset_id: str) -> str:
    return f"manifests/{dataset_id}.json"
