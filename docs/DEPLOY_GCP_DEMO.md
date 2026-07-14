# Deploy Demo A to GCP Cloud Run

Thin demo: API + UI on Cloud Run, Vertex Gemini, demo auth, ephemeral SQLite.

## Prerequisites

- `gcloud` CLI logged in with rights on the target project (default `ooredoo-499510`)
- Billing enabled; Vertex AI available in `us-central1`

Windows PowerShell:

```powershell
.\scripts\deploy_gcp_demo.ps1 -ProjectId ooredoo-499510 -Region us-central1
```

Or with custom passwords:

```powershell
.\scripts\deploy_gcp_demo.ps1 -ProjectId ooredoo-499510 -PublicPassword demo -AdminPassword 'your-strong-password'
```

Git Bash / WSL / Linux:

```bash
export GCP_PROJECT_ID=ooredoo-499510
export GCP_LOCATION=us-central1
export PUBLIC_PASSWORD=demo
export ADMIN_PASSWORD='your-strong-password'
bash scripts/deploy_gcp_demo.sh
```

The script prints **UI** and **API** URLs when done.

## Live Demo A (ooredoo-499510)

| | URL |
|--|-----|
| **UI** | https://arabic-proofreading-web-2tqtjdoq3q-uc.a.run.app |
| **API** | https://arabic-proofreading-api-2tqtjdoq3q-uc.a.run.app |
| Health | https://arabic-proofreading-api-2tqtjdoq3q-uc.a.run.app/api/v1/health |

Login: `user` / `demo` or `admin` / `302@Labs` (change via deploy params).

In Settings, API base should already point at the Cloud Run API (baked in at build time).

## What gets deployed

| Service | Image | Notes |
|---------|-------|--------|
| `arabic-proofreading-api` | root `Dockerfile` | FastAPI, `AI_CLIENT=gemini`, `USE_GCP=true` |
| `arabic-proofreading-web` | `frontend/Dockerfile` | Built with `VITE_API_BASE_URL=<api url>` |

## After deploy

1. Open the **UI** URL  
2. Login: `user` / public password, or `admin` / admin password  
3. Settings → API base should already match the API URL (from build env)  
4. Live Mode → run a review  

## Limits (Demo A)

- SQLite is `/tmp/app.db` — data resets when instances recycle  
- Unauthenticated Cloud Run URLs (gated only by app login)  
- No Firestore / GCS yet (Phase 7 track B)

## Manual API-only rebuild

```bash
gcloud builds submit --tag REGION-docker.pkg.dev/PROJECT/proofreading/arabic-proofreading-api:latest .
gcloud run deploy arabic-proofreading-api --image ... --region us-central1
```
