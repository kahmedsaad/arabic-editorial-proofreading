"""Blind benchmark runner: public cases only — never opens private/.

Does not modify proofreading logic, prompts, rules, or retrieval.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app import __version__ as app_version
from app.config import ROOT_DIR, settings
from app.models.schemas import ReviewRequest
from app.orchestration.review import ReviewOrchestrator

FORBIDDEN_CASE_KEYS = {
    "expected_findings",
    "forbidden_findings",
    "must_explain",
    "required_span_any",
    "acceptable_decisions",
    "severity_band",
}


def _resolve_path(path: Path, *, default_under_benchmark: Path | None = None) -> Path:
    candidates = [path]
    if not path.is_absolute():
        candidates.extend(
            [
                ROOT_DIR / path,
                ROOT_DIR / "benchmark_v2" / path,
            ]
        )
        if default_under_benchmark is not None:
            candidates.append(ROOT_DIR / "benchmark_v2" / default_under_benchmark)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (ROOT_DIR / path).resolve()


def _require_real_gemini_client() -> None:
    client = (settings.ai_client or "").strip().lower()
    model = _model_name().strip().lower()
    if client == "mock" or model == "mock":
        raise SystemExit(
            "benchmark_v2 refuses mock clients. Set AI_CLIENT=gemini and USE_GCP=true "
            "(Vertex). Current: "
            f"ai_client={settings.ai_client!r} model_name={_model_name()!r}"
        )
    if client != "gemini":
        raise SystemExit(
            f"benchmark_v2 requires AI_CLIENT=gemini (got {settings.ai_client!r})"
        )


def log_startup() -> None:
    print(
        json.dumps(
            {
                "event": "benchmark_v2_startup",
                "ai_client": settings.ai_client,
                "model_name": _model_name(),
                "use_gcp": settings.use_gcp,
                "gcp_project": settings.gcp_project_id,
                "gcp_location": settings.gcp_location,
                "prompt_version": _prompt_version(),
                "engine_version": app_version,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _prompt_version() -> str:
    prompt_dir = ROOT_DIR / "prompts" / "gemini" / "v1"
    if prompt_dir.exists():
        return "gemini/v1"
    if (ROOT_DIR / "GEMINI_SYSTEM_PROMPT.txt").exists():
        return "GEMINI_SYSTEM_PROMPT.txt"
    return "unknown"


def _model_name() -> str:
    if settings.ai_client == "mock":
        return "mock"
    return settings.gemini_model


def _assert_public_cases_dir(cases_dir: Path) -> None:
    parts = {p.lower() for p in cases_dir.parts}
    if "private" in parts or "gold" in parts:
        raise SystemExit(
            f"Refusing cases path that looks private/gold: {cases_dir}"
        )


def load_public_cases(cases_dir: Path) -> list[dict[str, str]]:
    _assert_public_cases_dir(cases_dir)
    cases: list[dict[str, str]] = []
    for path in sorted(cases_dir.glob("*.json")):
        raw = json.loads(path.read_text(encoding="utf-8"))
        leaked = FORBIDDEN_CASE_KEYS.intersection(raw)
        if leaked:
            raise RuntimeError(
                f"{path.name} contains forbidden gold keys {sorted(leaked)}"
            )
        case_id = str(raw.get("case_id") or path.stem)
        cases.append(
            {
                "case_id": case_id,
                "headline": str(raw.get("headline") or ""),
                "body": str(raw.get("body") or ""),
            }
        )
    return cases


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _zone_by_segment(segments: list[Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for segment in segments:
        sid = getattr(segment, "segment_id", None)
        zone = getattr(segment, "zone", None)
        if sid is not None:
            mapping[str(sid)] = str(_enum_value(zone) if zone is not None else "body")
    return mapping


def _token_usage_from_client(orch: ReviewOrchestrator) -> tuple[int | None, dict[str, Any] | None]:
    client = getattr(orch, "ai_client", None)
    usage = getattr(client, "last_token_usage", None)
    if not isinstance(usage, dict):
        return None, None
    total = usage.get("total_tokens")
    total_i = int(total) if isinstance(total, (int, float)) else None
    return total_i, usage

def serialize_finding(finding: Any, zone_map: dict[str, str]) -> dict[str, Any]:
    """Preserve raw engine finding fields and add segment_zone for adapters."""
    if hasattr(finding, "model_dump"):
        raw = finding.model_dump(mode="json")
    else:
        raw = dict(finding)
    segment_id = str(raw.get("segment_id") or "")
    raw["segment_zone"] = zone_map.get(segment_id, "body")
    return raw


async def review_case(
    orch: ReviewOrchestrator,
    case: dict[str, str],
) -> dict[str, Any]:
    started = asyncio.get_running_loop().time()
    try:
        response = await orch.review(
            ReviewRequest(
                document_id=case["case_id"],
                headline=case["headline"],
                body=case["body"],
                language="ar",
                source="benchmark_v2",
                metadata={
                    "benchmark": "benchmark_v2",
                    "case_id": case["case_id"],
                },
            )
        )
        latency_ms = (asyncio.get_running_loop().time() - started) * 1000.0
        zone_map = _zone_by_segment(response.segments)
        findings = [serialize_finding(f, zone_map) for f in response.findings]
        token_total, token_detail = _token_usage_from_client(orch)
        return {
            "case_id": case["case_id"],
            "latency_ms": round(latency_ms, 2),
            "token_usage": token_total,
            "token_usage_detail": token_detail,
            "error": None,
            "timed_out": False,
            "review_id": response.review_id,
            "findings": findings,
            "raw_findings": findings,
            "rejected_finding_count": len(response.rejected_findings),
            "mechanical_finding_count": response.mechanical_finding_count,
            "ai_finding_count": response.ai_finding_count,
        }
    except TimeoutError as exc:
        latency_ms = (asyncio.get_running_loop().time() - started) * 1000.0
        token_total, token_detail = _token_usage_from_client(orch)
        return {
            "case_id": case["case_id"],
            "latency_ms": round(latency_ms, 2),
            "token_usage": token_total,
            "token_usage_detail": token_detail,
            "error": f"timeout: {exc}",
            "timed_out": True,
            "findings": [],
            "raw_findings": [],
        }
    except Exception as exc:  # noqa: BLE001 — continue suite on per-case failure
        latency_ms = (asyncio.get_running_loop().time() - started) * 1000.0
        token_total, token_detail = _token_usage_from_client(orch)
        return {
            "case_id": case["case_id"],
            "latency_ms": round(latency_ms, 2),
            "token_usage": token_total,
            "token_usage_detail": token_detail,
            "error": f"{type(exc).__name__}: {exc}",
            "timed_out": False,
            "traceback": traceback.format_exc(limit=5),
            "findings": [],
            "raw_findings": [],
        }


async def run_benchmark(cases: list[dict[str, str]], *, pace_seconds: float = 1.5) -> dict[str, Any]:
    orch = ReviewOrchestrator()
    outputs: list[dict[str, Any]] = []
    for i, case in enumerate(cases):
        # Only case_id / headline / body are sent to the engine.
        outputs.append(
            await review_case(
                orch,
                {
                    "case_id": case["case_id"],
                    "headline": case["headline"],
                    "body": case["body"],
                },
            )
        )
        print(
            f"progress {i + 1}/{len(cases)} {case['case_id']} "
            f"findings={len(outputs[-1].get('findings') or [])} "
            f"error={outputs[-1].get('error')}",
            flush=True,
        )
        if pace_seconds > 0 and i + 1 < len(cases):
            await asyncio.sleep(pace_seconds)

    processed = [o for o in outputs if not o.get("error")]
    failed = [o for o in outputs if o.get("error")]
    latencies = [float(o["latency_ms"]) for o in outputs if o.get("latency_ms") is not None]
    total_findings = sum(len(o.get("findings") or []) for o in outputs)
    mech_count = sum(int(o.get("mechanical_finding_count") or 0) for o in outputs)
    ai_count = sum(int(o.get("ai_finding_count") or 0) for o in outputs)
    # Also count by source on preserved findings (authoritative for mixed runs).
    src_mech = src_ai = 0
    token_totals: list[int] = []
    for o in outputs:
        if isinstance(o.get("token_usage"), int):
            token_totals.append(o["token_usage"])
        for f in o.get("findings") or []:
            src = str(f.get("source") or "")
            if src == "gemini":
                src_ai += 1
            elif src == "mechanical":
                src_mech += 1
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else None

    meta = {
        "benchmark_id": "benchmark_v2",
        "engine_version": app_version,
        "package_version": "0.6.0",
        "prompt_version": _prompt_version(),
        "model_name": _model_name(),
        "ai_client": settings.ai_client,
        "use_gcp": settings.use_gcp,
        "gcp_project": settings.gcp_project_id,
        "gcp_location": settings.gcp_location,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    if meta["ai_client"] == "mock" or meta["model_name"] == "mock":
        raise RuntimeError("Refusing to write mock benchmark_v2 outputs")

    return {
        "meta": meta,
        "summary": {
            "total_cases": len(outputs),
            "processed_cases": len(processed),
            "failed_cases": len(failed),
            "failed_case_ids": [o["case_id"] for o in failed],
            "average_latency_ms": avg_latency,
            "total_findings": total_findings,
            "mechanical_finding_count": mech_count or src_mech,
            "ai_finding_count": ai_count or src_ai,
            "token_usage_total": sum(token_totals) if token_totals else None,
        },
        "outputs": outputs,
    }

def _resolve_output_path(path: Path) -> Path:
    if path.is_absolute():
        return path.resolve()
    # Already rooted at benchmark_v2/...
    if path.parts and path.parts[0] == "benchmark_v2":
        return (ROOT_DIR / path).resolve()
    # Short form results/... → benchmark_v2/results/...
    if path.parts and path.parts[0] == "results":
        return (ROOT_DIR / "benchmark_v2" / path).resolve()
    return (ROOT_DIR / path).resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run blind benchmark_v2 on public cases only"
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("public/cases"),
        help="Directory of public case JSON files (never private/gold)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/engine_outputs.json"),
        help="Output JSON path",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _require_real_gemini_client()
    log_startup()

    cases_dir = _resolve_path(args.cases, default_under_benchmark=Path("public/cases"))
    output_path = _resolve_output_path(args.output)

    _assert_public_cases_dir(cases_dir)
    if not cases_dir.exists():
        raise SystemExit(f"Cases directory not found: {cases_dir}")

    cases = load_public_cases(cases_dir)
    payload = asyncio.run(run_benchmark(cases))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = payload["summary"]
    print(json.dumps({"meta": payload["meta"], "summary": summary}, ensure_ascii=False, indent=2))
    print(f"output_file: {output_path}")
    return 0 if summary["failed_cases"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
