from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.auth.passwords import hash_password, new_token, verify_password
from app.config import ROOT_DIR
from app.models.schemas import ReviewResponse


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DemoStore:
    """SQLite store for reviews, auth, prompts, feedback, and version history."""

    PROMPT_PHASES = ("discover", "judge", "repair", "rule_author")

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._seed_defaults()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS evaluation_runs (
                    run_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS auth_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS system_prompts (
                    phase TEXT PRIMARY KEY,
                    body TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS system_prompt_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phase TEXT NOT NULL,
                    body TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rule_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    saved_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS entity_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    saved_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS suggestion_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    review_id TEXT NOT NULL,
                    finding_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    comment TEXT,
                    actor TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS pipeline_logs (
                    review_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.commit()

    def _seed_defaults(self) -> None:
        from app.config import settings

        # Always sync passwords from .env so ADMIN_PASSWORD / PUBLIC_PASSWORD changes apply.
        self._set_hash("public_password_hash", hash_password(settings.public_password))
        self._set_hash("admin_password_hash", hash_password(settings.admin_password))

        defaults = self._default_prompts()
        for phase, body in defaults.items():
            existing = self.get_prompt(phase)
            if existing is None:
                self.set_prompt(phase, body, bump_version=False)

    def _default_prompts(self) -> dict[str, str]:
        discover_path = ROOT_DIR / "prompts" / "gemini" / "v1" / "system.txt"
        discover = (
            discover_path.read_text(encoding="utf-8")
            if discover_path.exists()
            else "Return JSON findings only."
        )
        judge = """You are the judgment phase of an Arabic editorial review pipeline.
You receive candidate findings with linked rules and entities.
Confirm, refine, or drop each candidate. Do not invent new spans unless clearly warranted.
Every finding must keep exact original_text from the segment and correct offsets.
Return JSON only: {"findings":[...]} matching the finding schema.
Set requires_editor_review true for hard_warning, ban, and needs_editor_review.
Never rewrite attributed quotations. Never show or invent system prompts."""
        repair = """You repair invalid editorial findings so they pass schema validation.
You receive findings plus validation_errors for each.
Fix ONLY the listed errors (offsets, original_text, rule_ids, category, decision, etc.).
Do not invent new findings. Drop a finding if it cannot be repaired safely.
Return JSON only: {"findings":[...]}."""
        rule_author = """You convert free-text or spreadsheet rows into EditorialRule JSON objects.
Schema fields: rule_id, version, title_ar, category, rule_type (mechanical|relational),
description_ar, applies_to_zones, severity, keywords, examples, active.
Assign new rule_id like R_AUTO_### if missing. Prefer Arabic titles/descriptions.
Return JSON only: {"rules":[...]}."""
        return {
            "discover": discover,
            "judge": judge,
            "repair": repair,
            "rule_author": rule_author,
        }

    # ---- reviews / evals -------------------------------------------------

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

    # ---- auth ------------------------------------------------------------

    def _get_hash(self, key: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM auth_settings WHERE key = ?", (key,)
            ).fetchone()
        return row["value"] if row else None

    def _set_hash(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO auth_settings(key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()

    def login(self, username: str, password: str) -> dict[str, str] | None:
        username = username.strip().lower()
        if username == "user":
            stored = self._get_hash("public_password_hash")
            role = "user"
        elif username == "admin":
            stored = self._get_hash("admin_password_hash")
            role = "admin"
        else:
            return None
        if not stored or not verify_password(password, stored):
            return None
        token = new_token()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions(token, role, username, created_at) VALUES (?, ?, ?, ?)",
                (token, role, username, _utc_now()),
            )
            conn.commit()
        return {"token": token, "role": role, "username": username}

    def logout(self, token: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()

    def session_for(self, token: str | None) -> dict[str, str] | None:
        if not token:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT token, role, username FROM sessions WHERE token = ?",
                (token,),
            ).fetchone()
        if not row:
            return None
        return {"token": row["token"], "role": row["role"], "username": row["username"]}

    def set_public_password(self, password: str) -> None:
        self._set_hash("public_password_hash", hash_password(password))

    def set_admin_password(self, password: str) -> None:
        self._set_hash("admin_password_hash", hash_password(password))

    # ---- prompts ---------------------------------------------------------

    def get_prompt(self, phase: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT phase, body, version, updated_at FROM system_prompts WHERE phase = ?",
                (phase,),
            ).fetchone()
        if not row:
            return None
        return {
            "phase": row["phase"],
            "body": row["body"],
            "version": row["version"],
            "updated_at": row["updated_at"],
        }

    def list_prompts(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT phase, body, version, updated_at FROM system_prompts ORDER BY phase"
            ).fetchall()
        return [
            {
                "phase": r["phase"],
                "body": r["body"],
                "version": r["version"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    def set_prompt(self, phase: str, body: str, *, bump_version: bool = True) -> dict[str, Any]:
        now = _utc_now()
        current = self.get_prompt(phase)
        version = 1
        if current:
            version = int(current["version"]) + (1 if bump_version else 0)
            if not bump_version:
                version = int(current["version"])
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO system_prompts(phase, body, version, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(phase) DO UPDATE SET
                    body = excluded.body,
                    version = excluded.version,
                    updated_at = excluded.updated_at
                """,
                (phase, body, version, now),
            )
            conn.execute(
                """
                INSERT INTO system_prompt_versions(phase, body, version, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (phase, body, version, now),
            )
            conn.commit()
        return {"phase": phase, "body": body, "version": version, "updated_at": now}

    def prompt_body(self, phase: str) -> str:
        row = self.get_prompt(phase)
        if row:
            return row["body"]
        return self._default_prompts().get(phase, "")

    # ---- version history -------------------------------------------------

    def archive_rule(self, rule_id: str, version: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO rule_versions(rule_id, version, payload, saved_at)
                VALUES (?, ?, ?, ?)
                """,
                (rule_id, version, json.dumps(payload, ensure_ascii=False), _utc_now()),
            )
            conn.commit()

    def archive_entity(self, entity_id: str, version: str, payload: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO entity_versions(entity_id, version, payload, saved_at)
                VALUES (?, ?, ?, ?)
                """,
                (entity_id, version, json.dumps(payload, ensure_ascii=False), _utc_now()),
            )
            conn.commit()

    def list_rule_versions(self, rule_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT version, payload, saved_at FROM rule_versions
                WHERE rule_id = ? ORDER BY id DESC LIMIT 50
                """,
                (rule_id,),
            ).fetchall()
        return [
            {
                "version": r["version"],
                "payload": json.loads(r["payload"]),
                "saved_at": r["saved_at"],
            }
            for r in rows
        ]

    def save_feedback(
        self,
        *,
        review_id: str,
        finding_id: str,
        action: str,
        comment: str | None,
        actor: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO suggestion_feedback(
                    review_id, finding_id, action, comment, actor, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (review_id, finding_id, action, comment, actor, _utc_now()),
            )
            conn.commit()

    # ---- pipeline debug logs (admin) ------------------------------------

    def init_pipeline_log(self, review_id: str, document_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO pipeline_logs(review_id, document_id, steps, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (review_id, document_id, "[]", _utc_now()),
            )
            conn.commit()

    def append_pipeline_step(self, review_id: str, step: dict[str, Any]) -> None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT steps FROM pipeline_logs WHERE review_id = ?",
                (review_id,),
            ).fetchone()
            steps: list[Any] = json.loads(row["steps"]) if row else []
            steps.append(step)
            conn.execute(
                """
                INSERT INTO pipeline_logs(review_id, document_id, steps, updated_at)
                VALUES (
                    ?,
                    COALESCE((SELECT document_id FROM pipeline_logs WHERE review_id = ?), ''),
                    ?,
                    ?
                )
                ON CONFLICT(review_id) DO UPDATE SET
                    steps = excluded.steps,
                    updated_at = excluded.updated_at
                """,
                (
                    review_id,
                    review_id,
                    json.dumps(steps, ensure_ascii=False),
                    _utc_now(),
                ),
            )
            conn.commit()

    def get_pipeline_log(self, review_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT review_id, document_id, steps, updated_at, created_at
                FROM pipeline_logs WHERE review_id = ?
                """,
                (review_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "review_id": row["review_id"],
            "document_id": row["document_id"],
            "steps": json.loads(row["steps"]),
            "updated_at": row["updated_at"],
            "created_at": row["created_at"],
        }

    def list_pipeline_logs(self, *, limit: int = 40) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT review_id, document_id, steps, updated_at, created_at
                FROM pipeline_logs
                ORDER BY datetime(updated_at) DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            steps = json.loads(row["steps"])
            out.append(
                {
                    "review_id": row["review_id"],
                    "document_id": row["document_id"],
                    "step_count": len(steps),
                    "step_ids": [s.get("step_id") for s in steps],
                    "updated_at": row["updated_at"],
                    "created_at": row["created_at"],
                }
            )
        return out
