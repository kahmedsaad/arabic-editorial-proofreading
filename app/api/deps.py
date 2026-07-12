from functools import lru_cache

from fastapi import Depends, HTTPException, Request

from app.config import settings
from app.entities.repository import EntityRepository
from app.orchestration.review import ReviewOrchestrator
from app.persistence.demo_store import DemoStore
from app.rules.repository import JsonRuleRepository


@lru_cache
def get_rule_repo() -> JsonRuleRepository:
    return JsonRuleRepository(settings.rules_dir)


@lru_cache
def get_entity_repo() -> EntityRepository:
    return EntityRepository(settings.entities_dir)


@lru_cache
def get_store() -> DemoStore:
    return DemoStore(settings.sqlite_path)


@lru_cache
def get_orchestrator() -> ReviewOrchestrator:
    return ReviewOrchestrator(
        rule_repo=get_rule_repo(),
        entity_repo=get_entity_repo(),
        prompt_provider=get_store(),
        store=get_store(),
    )


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth:
        return None
    parts = auth.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def get_optional_session(request: Request) -> dict | None:
    token = _bearer_token(request) or request.cookies.get("demo_token")
    return get_store().session_for(token)


def require_user(request: Request) -> dict:
    if not settings.demo_auth_required:
        session = get_optional_session(request)
        return session or {"role": "user", "username": "user", "token": ""}
    session = get_optional_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="authentication required")
    return session


def require_admin(request: Request) -> dict:
    if not settings.demo_auth_required:
        session = get_optional_session(request)
        if session and session.get("role") == "admin":
            return session
        # Allow admin ops in open local mode when explicitly logged in as admin,
        # otherwise treat as admin for seed/dev convenience.
        return session or {"role": "admin", "username": "admin", "token": ""}
    session = get_optional_session(request)
    if not session or session.get("role") != "admin":
        raise HTTPException(status_code=403, detail="admin required")
    return session


# FastAPI dependency aliases
OptionalSession = Depends(get_optional_session)
UserSession = Depends(require_user)
AdminSession = Depends(require_admin)
