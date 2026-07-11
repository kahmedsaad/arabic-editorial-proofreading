"""Hidden benchmark_v2 scorer package.

Gold answers live under ``benchmark_v2/private/gold`` and must never be
passed to the proofreading engine. Only ``public/cases`` may be used as
engine inputs.
"""

from benchmark_v2.private.scorer.schemas import (
    BenchmarkCase,
    BenchmarkReport,
    CaseScore,
    EngineFinding,
    ForbiddenFinding,
    GoldFinding,
)
from benchmark_v2.private.scorer.score import score_outputs, score_repeated_runs

__all__ = [
    "BenchmarkCase",
    "BenchmarkReport",
    "CaseScore",
    "EngineFinding",
    "ForbiddenFinding",
    "GoldFinding",
    "score_outputs",
    "score_repeated_runs",
]
