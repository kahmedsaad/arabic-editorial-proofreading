# Hidden Benchmark V2

Blind evaluation harness for the Arabic Editorial Proofreading Engine.

## Layout

```
benchmark_v2/
  public/cases/          # Neutral IDs (case-0001 …). Engine may read ONLY these.
  public/run_engine.py   # Runs the engine on public cases (never opens gold).
  private/gold/          # Hidden answers (gitignored). Scorer only.
  private/scorer/        # Schemas + scorer + HTML/JSON reports.
  private/manifest.json  # Case tags / critical flags (gitignored).
  results/               # Engine outputs + reports.
```

## Rules

1. Never copy gold into prompts, rules, few-shot examples, or engine source.
2. The engine receives `BenchmarkCase` fields only (`case_id`, `headline`, `body`).
3. Freeze engine / prompt / model versions before a scored run.
4. Prefer 3 repeated runs for consistency scoring.
5. Keep the old regression suite separate from this hidden set.

## Run engine (public only)

```bash
# from repo root
python -m benchmark_v2.public.run_engine --out benchmark_v2/results/engine_outputs_run1.json --run-id run-1
```

## Score (private gold)

```bash
python -m benchmark_v2.private.scorer.cli \
  --gold-dir benchmark_v2/private/gold \
  --outputs benchmark_v2/results/engine_outputs_run1.json \
  --report benchmark_v2/results/report.json
```

Repeated runs:

```bash
python -m benchmark_v2.private.scorer.cli \
  --gold-dir benchmark_v2/private/gold \
  --outputs benchmark_v2/results/engine_outputs_run1.json \
  --outputs benchmark_v2/results/engine_outputs_run2.json \
  --outputs benchmark_v2/results/engine_outputs_run3.json \
  --report benchmark_v2/results/report_consistency.json
```

## Metrics

- precision / recall / F1
- critical recall
- false-positive rate
- clean-case false-positive rate
- attribution preservation
- suggestion safety
- average latency
- consistency score (multi-run)

## Mechanical baseline vs Gemini evaluation

The earlier mock run is preserved as:

`results/benchmark_v2_mechanical_baseline.json`

It is **not** an AI evaluation. Real Vertex Gemini runs write:

`results/engine_outputs_gemini_run1.json`

`app.cli.run_benchmark` refuses `AI_CLIENT=mock`.
