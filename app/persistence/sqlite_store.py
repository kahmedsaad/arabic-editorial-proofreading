from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.models.schemas import ReviewResponse


class ReviewStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_runs (
                    run_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def save_review(self, review: ReviewResponse) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO reviews(review_id, document_id, payload) VALUES (?, ?, ?)",
                (
                    review.review_id,
                    review.document.document_id,
                    review.model_dump_json(),
                ),
            )
            conn.commit()

    def get_review(self, review_id: str) -> ReviewResponse | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM reviews WHERE review_id = ?",
                (review_id,),
            ).fetchone()
        if not row:
            return None
        return ReviewResponse.model_validate_json(row["payload"])

    def save_evaluation(self, run_id: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO evaluation_runs(run_id, payload) VALUES (?, ?)",
                (run_id, json.dumps(payload, ensure_ascii=False)),
            )
            conn.commit()
