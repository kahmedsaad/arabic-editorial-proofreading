"""Local filesystem dataset loader (default for CI / laptop)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from app.data.loader import iter_jsonl_lines


class LocalDatasetLoader:
    def __init__(self, *, root: Path) -> None:
        self.root = Path(root)

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        # Allow paths relative to CWD or under root
        cwd_candidate = Path.cwd() / p
        if cwd_candidate.exists():
            return cwd_candidate
        return self.root / p

    def list_files(self, dataset_path: str) -> list[str]:
        base = self._resolve(dataset_path)
        if base.is_file():
            return [str(base)]
        if not base.exists():
            return []
        return sorted(str(p) for p in base.rglob("*") if p.is_file())

    def read_text(self, file_path: str) -> str:
        path = self._resolve(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        return path.read_text(encoding="utf-8")

    def read_jsonl(self, file_path: str) -> Iterable[dict]:
        path = self._resolve(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        with path.open(encoding="utf-8") as fh:
            yield from iter_jsonl_lines(fh, source_name=str(path))

    def download_file(self, source_path: str, destination: Path) -> Path:
        src = self._resolve(source_path)
        if not src.exists():
            raise FileNotFoundError(src)
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, destination)
        return destination

    def upload_file(self, source: Path, destination_path: str) -> str:
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(source)
        dest = self._resolve(destination_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        return str(dest)

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()
