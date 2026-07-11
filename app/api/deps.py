from functools import lru_cache

from app.config import settings
from app.entities.repository import EntityRepository
from app.orchestration.review import ReviewOrchestrator
from app.persistence.sqlite_store import ReviewStore
from app.rules.repository import JsonRuleRepository


@lru_cache
def get_rule_repo() -> JsonRuleRepository:
    return JsonRuleRepository(settings.rules_dir)


@lru_cache
def get_entity_repo() -> EntityRepository:
    return EntityRepository(settings.entities_dir)


@lru_cache
def get_store() -> ReviewStore:
    return ReviewStore(settings.sqlite_path)


@lru_cache
def get_orchestrator() -> ReviewOrchestrator:
    return ReviewOrchestrator(rule_repo=get_rule_repo(), entity_repo=get_entity_repo())
