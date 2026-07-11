"""HTML report renderer for benchmark_v2."""

from __future__ import annotations

from html import escape
from pathlib import Path

from benchmark_v2.private.scorer.schemas import BenchmarkReport


def render_html_report(report: BenchmarkReport) -> str:
    rows = []
    for case in report.cases:
        rows.append(
            "<tr>"
            f"<td>{escape(case.case_id)}</td>"
            f"<td>{case.true_positives}</td>"
            f"<td>{case.false_positives}</td>"
            f"<td>{case.false_negatives}</td>"
            f"<td>{case.f1:.3f}</td>"
            f"<td>{'yes' if case.clean_case else 'no'}</td>"
            f"<td>{'yes' if case.attribution_preserved else 'no'}</td>"
            f"<td>{case.suggestion_safety:.3f}</td>"
            f"<td>{'' if case.latency_ms is None else f'{case.latency_ms:.0f}'}</td>"
            "</tr>"
        )

    def metric(label: str, value: object) -> str:
        return (
            f"<div class='metric'><div class='label'>{escape(label)}</div>"
            f"<div class='value'>{escape(str(value))}</div></div>"
        )

    consistency = (
        "n/a" if report.consistency_score is None else f"{report.consistency_score:.4f}"
    )
    latency = (
        "n/a"
        if report.average_latency_ms is None
        else f"{report.average_latency_ms:.2f}"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>benchmark_v2 report</title>
  <style>
    body {{ font-family: Georgia, serif; margin: 2rem; background: #f7f4ef; color: #1c1a17; }}
    h1 {{ margin-bottom: .2rem; }}
    .sub {{ color: #5c574f; margin-bottom: 1.5rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: .75rem; }}
    .metric {{ background: #fff; border: 1px solid #ddd4c6; border-radius: 8px; padding: .75rem 1rem; }}
    .label {{ font-size: .8rem; color: #6b655c; text-transform: uppercase; letter-spacing: .04em; }}
    .value {{ font-size: 1.35rem; margin-top: .2rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; background: #fff; }}
    th, td {{ border: 1px solid #e2d8cb; padding: .5rem .6rem; text-align: left; font-size: .92rem; }}
    th {{ background: #efe7db; }}
  </style>
</head>
<body>
  <h1>benchmark_v2</h1>
  <p class="sub">Hidden evaluation report · runs={report.run_count}</p>
  <div class="grid">
    {metric("Cases", report.total_cases)}
    {metric("Precision", f"{report.precision:.4f}")}
    {metric("Recall", f"{report.recall:.4f}")}
    {metric("F1", f"{report.f1:.4f}")}
    {metric("Critical recall", f"{report.critical_recall:.4f}")}
    {metric("FP rate", f"{report.false_positive_rate:.4f}")}
    {metric("Clean FP rate", f"{report.clean_case_false_positive_rate:.4f}")}
    {metric("Attribution preservation", f"{report.attribution_preservation:.4f}")}
    {metric("Suggestion safety", f"{report.suggestion_safety:.4f}")}
    {metric("Avg latency (ms)", latency)}
    {metric("Consistency", consistency)}
    {metric("TP / FP / FN", f"{report.tp} / {report.fp} / {report.fn}")}
  </div>
  <table>
    <thead>
      <tr>
        <th>Case</th><th>TP</th><th>FP</th><th>FN</th><th>F1</th>
        <th>Clean</th><th>Attr OK</th><th>Sug safety</th><th>Latency</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""


def write_html_report(report: BenchmarkReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html_report(report), encoding="utf-8")
