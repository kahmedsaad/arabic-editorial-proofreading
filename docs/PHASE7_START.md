# Phase 7 — Start Here

Phases 1–6 are complete. This file marks the **start of Phase 7**.

## Goal

Optional GCP adapters without breaking local mode (`USE_GCP=false`).

## Implement next (from `prompts/04_GCP_DEPLOYMENT_PROMPT.txt`)

1. Cloud Storage adapter for uploaded documents and datasets
2. Firestore adapter for rules and review results
3. Vertex AI Gemini configuration
4. Cloud Run-ready Dockerfile + deployment instructions
5. Env switching via `USE_GCP` and `AI_CLIENT`
6. Health checks + startup validation for GCP mode

## Do not add yet

- GKE, Pub/Sub, queues, authentication, production hardening

## Current stubs

- `app/gcp/__init__.py` raises `NotImplementedError`
- `.env.example` already lists GCP variables
- Health endpoint reports `phase7_ready: false`

## Acceptance

- Local mode + unit tests work without GCP credentials
- GCP path is opt-in only
