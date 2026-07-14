"""Shared utilities and DatasetLoader protocol."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, Protocol

from app.config import settings


class DatasetLoader(Protocol):
    def list_files(self, dataset_path: str) -> list[str]: ...

    def read_text(self, file_path: str) -> str: ...

    def read_jsonl(self, file_path: str) -> Iterable[dict]: ...

    def download_file(self, source_path: str, destination: Path) -> Path: ...

    def upload_file(self, source: Path, destination_path: str) -> str: ...

    def exists(self, path: str) -> bool: ...


_GCS_URI = re.compile(r"^gs://([^/]+)/(.*)$")


def parse_gcs_uri(uri: str) -> tuple[str, str]:
    m = _GCS_URI.match(uri.strip())
    if not m:
        raise ValueError(f"Not a GCS URI: {uri}")
    return m.group(1), m.group(2)


def is_gcs_path(path: str) -> bool:
    return path.strip().startswith("gs://")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_jsonl_file(path: Path) -> int:
    """Validate JSONL; return record count. Raises ValueError with file:line."""
    count = 0
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: malformed JSON ({exc})") from exc
            count += 1
    return count


def iter_jsonl_lines(text_iter: Iterable[str], *, source_name: str) -> Iterable[dict]:
    for line_no, line in enumerate(text_iter, start=1):
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{source_name}:{line_no}: malformed JSON ({exc})") from exc


def looks_like_secret(path: Path) -> bool:
    name = path.name.lower()
    if name in {".env", "credentials.json"} or name.endswith(
        (".pem", ".iam.json", "-sa.json")
    ):
        return True
    if "service_account" in name or "private_key" in name:
        return True
    # Peek first bytes for private key markers
    try:
        head = path.read_bytes()[:200]
    except OSError:
        return False
    return b"BEGIN PRIVATE KEY" in head or b"GOOGLE_APPLICATION_CREDENTIALS" in head


def is_private_prefix(destination_path: str) -> bool:
    p = destination_path.lstrip("/")
    return (
        p.startswith("private/")
        or p.startswith("benchmarks/private/")
        or "/private/" in f"/{p}"
    )


def is_public_prefix(destination_path: str) -> bool:
    p = destination_path.lstrip("/")
    return p.startswith("public/") or p.startswith("benchmarks/public/")


def reject_private_to_public(destination_path: str, *, contains_private_gold: bool) -> None:
    if contains_private_gold and is_public_prefix(destination_path):
        raise ValueError(
            "Refusing to upload private gold / private benchmark to a public/ prefix"
        )
    if "private_gold" in destination_path or "hidden_gold" in destination_path:
        if is_public_prefix(destination_path):
            raise ValueError("Refusing to upload private_gold path under public/")


def get_dataset_loader():
    """Factory: DATA_BACKEND=local|gcs. Local works without GCP credentials."""
    backend = (settings.data_backend or "local").strip().lower()
    if backend == "gcs":
        from app.data.gcs_loader import GCSDatasetLoader

        return GCSDatasetLoader(
            bucket=settings.gcs_data_bucket,
            prefix=settings.gcs_data_prefix or "",
            cache_dir=settings.data_cache_dir if settings.data_cache_enabled else None,
        )
    from app.data.local_loader import LocalDatasetLoader

    return LocalDatasetLoader(root=settings.local_data_dir)


def resolve_loader_for_path(path: str):
    """Pick loader from explicit path (gs:// vs local), independent of DATA_BACKEND."""
    if is_gcs_path(path):
        from app.data.gcs_loader import GCSDatasetLoader

        bucket, _ = parse_gcs_uri(path)
        return GCSDatasetLoader(
            bucket=bucket,
            prefix="",
            cache_dir=settings.data_cache_dir if settings.data_cache_enabled else None,
        )
    from app.data.local_loader import LocalDatasetLoader

    # Absolute or relative file path — use parent as root for relative listing
    return LocalDatasetLoader(root=Path("."))
