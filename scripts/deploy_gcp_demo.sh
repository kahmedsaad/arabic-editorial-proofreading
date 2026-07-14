#!/usr/bin/env bash
# Demo A — deploy API + frontend to Cloud Run (project ooredoo-499510 by default).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${GCP_LOCATION:-us-central1}"
AR_REPO="${AR_REPO:-proofreading}"
API_SERVICE="${API_SERVICE:-arabic-proofreading-api}"
WEB_SERVICE="${WEB_SERVICE:-arabic-proofreading-web}"
PUBLIC_PASSWORD="${PUBLIC_PASSWORD:-demo}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-302@Labs}"

if [[ -z "${PROJECT_ID}" || "${PROJECT_ID}" == "(unset)" ]]; then
  echo "Set GCP_PROJECT_ID or gcloud config set project ..." >&2
  exit 1
fi

echo "Project=${PROJECT_ID} Region=${REGION}"

gcloud config set project "${PROJECT_ID}"

echo "Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  aiplatform.googleapis.com \
  cloudbuild.googleapis.com \
  --project="${PROJECT_ID}"

PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo "Granting Vertex AI user to ${RUNTIME_SA} (idempotent)..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/aiplatform.user" \
  --condition=None \
  --quiet >/dev/null || true

if ! gcloud artifacts repositories describe "${AR_REPO}" \
  --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
  echo "Creating Artifact Registry ${AR_REPO}..."
  gcloud artifacts repositories create "${AR_REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Arabic editorial proofreading demo" \
    --project="${PROJECT_ID}"
fi

API_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${API_SERVICE}:latest"
WEB_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/${WEB_SERVICE}:latest"

echo "Building + pushing API image..."
gcloud builds submit \
  --tag "${API_IMAGE}" \
  --project="${PROJECT_ID}" \
  .

echo "Deploying API..."
gcloud run deploy "${API_SERVICE}" \
  --image="${API_IMAGE}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --max-instances=3 \
  --set-env-vars="AI_CLIENT=gemini,USE_GCP=true,GCP_PROJECT_ID=${PROJECT_ID},GCP_LOCATION=${REGION},DEMO_AUTH_REQUIRED=true,PUBLIC_PASSWORD=${PUBLIC_PASSWORD},ADMIN_PASSWORD=${ADMIN_PASSWORD},SQLITE_PATH=/tmp/app.db,ENABLE_LETTER_VARIANT_WARNINGS=false,CORS_ORIGINS=*" \
  --quiet

API_URL="$(gcloud run services describe "${API_SERVICE}" \
  --region="${REGION}" --project="${PROJECT_ID}" \
  --format='value(status.url)')"
echo "API_URL=${API_URL}"

echo "Building + pushing frontend (VITE_API_BASE_URL=${API_URL})..."
gcloud builds submit \
  --project="${PROJECT_ID}" \
  --config=- \
  <<EOF
steps:
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - -t
      - ${WEB_IMAGE}
      - --build-arg
      - VITE_API_BASE_URL=${API_URL}
      - frontend
images:
  - ${WEB_IMAGE}
EOF

echo "Deploying frontend..."
gcloud run deploy "${WEB_SERVICE}" \
  --image="${WEB_IMAGE}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --max-instances=3 \
  --set-env-vars="PORT=8080" \
  --quiet

WEB_URL="$(gcloud run services describe "${WEB_SERVICE}" \
  --region="${REGION}" --project="${PROJECT_ID}" \
  --format='value(status.url)')"

# Tighten CORS to the real web origin (optional second API update)
gcloud run services update "${API_SERVICE}" \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --update-env-vars="CORS_ORIGINS=${WEB_URL},http://127.0.0.1:5173,http://localhost:5173" \
  --quiet

echo ""
echo "========================================"
echo "  Demo A deployed"
echo "  UI:   ${WEB_URL}"
echo "  API:  ${API_URL}"
echo "  Login user / admin"
echo "  PUBLIC_PASSWORD=${PUBLIC_PASSWORD}"
echo "  ADMIN_PASSWORD=(set via ADMIN_PASSWORD env when deploying)"
echo "========================================"
