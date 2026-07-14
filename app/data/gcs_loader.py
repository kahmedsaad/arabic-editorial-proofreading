"""Google Cloud Storage dataset loader (optional; mocked in CI)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from app.data.loader import (
    iter_jsonl_lines,
    parse_gcs_uri,
    sha256_file,
)


class GCSDatasetLoader:
    """
    Requires google-cloud-storage when used.
    Do not grant the Cloud Run runtime storage.admin — objectViewer is enough for reads.
    """

    def __init__(
        self,
        *,
        bucket: str,
        prefix: str = "",
        cache_dir: Path | None = None,
        client=None,
    ) -> None:
        self.bucket_name = bucket
        self.prefix = (prefix or "").lstrip("/")
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._client = client

    def _client_or_raise(self):
        if self._client is not None:
            return self._client
        try:
            from google.cloud import storage  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "google-cloud-storage is required for DATA_BACKEND=gcs. "
                "Install with: pip install -e \".[gcs]\""
            ) from exc
        from app.config import settings

        project = settings.gcp_project_id or None
        self._client = storage.Client(project=project) if project else storage.Client()
        return self._client

    def _blob_name(self, path: str) -> str:
        path = path.strip()
        if path.startswith("gs://"):
            bucket, key = parse_gcs_uri(path)
            if bucket != self.bucket_name:
                # Allow cross-bucket via full URI by swapping
                self.bucket_name = bucket
            return key
        key = path.lstrip("/")
        if self.prefix and not key.startswith(self.prefix):
            return f"{self.prefix.rstrip('/')}/{key}"
        return key

    def _bucket(self):
        return self._client_or_raise().bucket(self.bucket_name)

    def list_files(self, dataset_path: str) -> list[str]:
        prefix = self._blob_name(dataset_path)
        blobs = self._client_or_raise().list_blobs(self.bucket_name, prefix=prefix)
        return [f"gs://{self.bucket_name}/{b.name}" for b in blobs if not b.name.endswith("/")]

    def read_text(self, file_path: str) -> str:
        blob = self._bucket().blob(self._blob_name(file_path))
        if not blob.exists():
            raise FileNotFoundError(f"gs://{self.bucket_name}/{self._blob_name(file_path)}")
        return blob.download_as_text(encoding="utf-8")

    def read_jsonl(self, file_path: str) -> Iterable[dict]:
        text = self.read_text(file_path)
        name = file_path if file_path.startswith("gs://") else f"gs://{self.bucket_name}/{self._blob_name(file_path)}"
        yield from iter_jsonl_lines(text.splitlines(), source_name=name)

    def download_file(self, source_path: str, destination: Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        key = self._blob_name(source_path)
        blob = self._bucket().blob(key)
        if not blob.exists():
            raise FileNotFoundError(f"gs://{self.bucket_name}/{key}")

        if self.cache_dir is not None:
            # Prefer cache when metadata checksum available
            meta = blob.metadata or {}
            checksum = meta.get("checksum_sha256")
            if checksum:
                cached = self.cache_dir / checksum / destination.name
                if cached.exists() and sha256_file(cached) == checksum:
                    destination.write_bytes(cached.read_bytes())
                    return destination

        blob.download_to_filename(str(destination))

        if self.cache_dir is not None:
            checksum = sha256_file(destination)
            cached = self.cache_dir / checksum / destination.name
            cached.parent.mkdir(parents=True, exist_ok=True)
            if not cached.exists():
                cached.write_bytes(destination.read_bytes())
            blob.metadata = {**(blob.metadata or {}), "checksum_sha256": checksum}
            try:
                blob.patch()
            except Exception:  # noqa: BLE001
                pass
        return destination

    def upload_file(self, source: Path, destination_path: str) -> str:
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(source)
        key = self._blob_name(destination_path)
        blob = self._bucket().blob(key)
        checksum = sha256_file(source)
        blob.metadata = {"checksum_sha256": checksum}
        blob.upload_from_filename(str(source), content_type="application/x-ndjson")
        return f"gs://{self.bucket_name}/{key}"

    def exists(self, path: str) -> bool:
        return self._bucket().blob(self._blob_name(path)).exists()

    def upload_manifest(self, manifest: dict, destination_path: str) -> str:
        key = self._blob_name(destination_path)
        blob = self._bucket().blob(key)
        payload = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        blob.upload_from_string(payload, content_type="application/json")
        return f"gs://{self.bucket_name}/{key}"
