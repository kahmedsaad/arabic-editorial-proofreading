"""Tests for local/GCS dataset loaders (GCS client mocked)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.data.gcs_loader import GCSDatasetLoader
from app.data.loader import (
    get_dataset_loader,
    is_gcs_path,
    looks_like_secret,
    parse_gcs_uri,
    reject_private_to_public,
    sha256_file,
    validate_jsonl_file,
)
from app.data.local_loader import LocalDatasetLoader
from app.data.manifest import build_manifest
from app.data.models import CleanArticleRecord, DatasetManifest


def test_parse_gcs_uri():
    b, k = parse_gcs_uri("gs://arabic-proofreading-data-ooredoo-499510/public/a.jsonl")
    assert b == "arabic-proofreading-data-ooredoo-499510"
    assert k == "public/a.jsonl"
    assert is_gcs_path("gs://x/y")
    assert not is_gcs_path("./data/x.jsonl")


def test_local_loader_streams_arabic_jsonl(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DATA_BACKEND", "local")
    path = tmp_path / "clean.jsonl"
    path.write_text(
        '{"record_id":"A1","source_type":"synthetic","headline":"عنوان","body":"نص عربي"}\n'
        "\n"
        '{"record_id":"A2","source_type":"synthetic","headline":"ب","body":"ج"}\n',
        encoding="utf-8",
    )
    loader = LocalDatasetLoader(root=tmp_path)
    rows = list(loader.read_jsonl(str(path)))
    assert len(rows) == 2
    assert rows[0]["headline"] == "عنوان"
    # Streaming: generator, not a pre-materialized giant list from loader API
    gen = loader.read_jsonl(str(path))
    assert hasattr(gen, "__iter__")
    CleanArticleRecord.model_validate({**rows[0], "language": "ar"})


def test_local_mode_factory_without_gcp(monkeypatch):
    monkeypatch.setattr("app.config.settings.data_backend", "local")
    from app.data.loader import get_dataset_loader
    from app.data.local_loader import LocalDatasetLoader

    loader = get_dataset_loader()
    assert isinstance(loader, LocalDatasetLoader)


def test_malformed_jsonl_includes_line(tmp_path: Path):
    path = tmp_path / "bad.jsonl"
    path.write_text('{"ok":1}\n{not-json}\n', encoding="utf-8")
    with pytest.raises(ValueError, match=r"bad\.jsonl:2"):
        validate_jsonl_file(path)


def test_checksum_and_manifest(tmp_path: Path):
    path = tmp_path / "a.jsonl"
    path.write_text('{"record_id":"1","source_type":"synthetic"}\n', encoding="utf-8")
    digest = sha256_file(path)
    m = build_manifest(
        dataset_id="sample",
        name="Sample",
        source=path,
        storage_path="public/samples/a.jsonl",
        source_type="synthetic",
        license_name="internal-demo",
    )
    assert m.checksum_sha256 == digest
    assert m.record_count == 1
    DatasetManifest.model_validate(m.model_dump())


def test_reject_private_gold_to_public():
    with pytest.raises(ValueError, match="public"):
        reject_private_to_public("public/x.jsonl", contains_private_gold=True)
    reject_private_to_public("private/x.jsonl", contains_private_gold=True)


def test_looks_like_secret(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("x=1", encoding="utf-8")
    assert looks_like_secret(env)
    ok = tmp_path / "clean.jsonl"
    ok.write_text("{}\n", encoding="utf-8")
    assert not looks_like_secret(ok)


def test_gcs_loader_mocked_upload_download(tmp_path: Path):
    client = MagicMock()
    bucket = MagicMock()
    blob = MagicMock()
    client.bucket.return_value = bucket
    bucket.blob.return_value = blob
    blob.exists.return_value = True
    blob.metadata = {"checksum_sha256": None}
    blob.download_as_text.return_value = '{"record_id":"1"}\n'

    src = tmp_path / "up.jsonl"
    src.write_text('{"record_id":"1","source_type":"synthetic"}\n', encoding="utf-8")
    loader = GCSDatasetLoader(bucket="test-bucket", prefix="", client=client)
    uri = loader.upload_file(src, "public/samples/up.jsonl")
    assert uri.startswith("gs://test-bucket/")
    blob.upload_from_filename.assert_called()

    rows = list(loader.read_jsonl("public/samples/up.jsonl"))
    assert rows[0]["record_id"] == "1"

    dest = tmp_path / "down.jsonl"
    blob.download_to_filename.side_effect = lambda p: Path(p).write_text(
        '{"record_id":"1"}\n', encoding="utf-8"
    )
    loader.download_file("public/samples/up.jsonl", dest)
    assert dest.exists()


def test_gcs_missing_file(tmp_path: Path):
    client = MagicMock()
    bucket = MagicMock()
    blob = MagicMock()
    client.bucket.return_value = bucket
    bucket.blob.return_value = blob
    blob.exists.return_value = False
    loader = GCSDatasetLoader(bucket="b", client=client)
    with pytest.raises(FileNotFoundError):
        loader.read_text("missing.jsonl")


def test_sample_files_are_valid_jsonl():
    root = Path(__file__).resolve().parents[1]
    for name in ("sample_clean_articles.jsonl", "sample_synthetic_cases.jsonl"):
        validate_jsonl_file(root / "data" / "samples" / name)
