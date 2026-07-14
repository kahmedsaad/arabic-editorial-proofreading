# Demo A — deploy API + frontend to Cloud Run
param(
  [string]$ProjectId = $env:GCP_PROJECT_ID,
  [string]$Region = $(if ($env:GCP_LOCATION) { $env:GCP_LOCATION } else { "us-central1" }),
  [string]$ArRepo = "proofreading",
  [string]$ApiService = "arabic-proofreading-api",
  [string]$WebService = "arabic-proofreading-web",
  [string]$PublicPassword = $(if ($env:PUBLIC_PASSWORD) { $env:PUBLIC_PASSWORD } else { "demo" }),
  [string]$AdminPassword = $(if ($env:ADMIN_PASSWORD) { $env:ADMIN_PASSWORD } else { "302@Labs" })
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Assert-LastExit([string]$Step) {
  if ($null -ne $LASTEXITCODE -and $LASTEXITCODE -ne 0) {
    throw "$Step failed (exit $LASTEXITCODE)"
  }
}

if (-not $ProjectId) {
  $ProjectId = (gcloud config get-value project 2>$null).Trim()
}
if (-not $ProjectId -or $ProjectId -eq "(unset)") {
  throw "Set -ProjectId or GCP_PROJECT_ID / gcloud config set project"
}

Write-Host "Project=$ProjectId Region=$Region"
gcloud config set project $ProjectId | Out-Null
Assert-LastExit "gcloud config set project"

Write-Host "Enabling APIs..."
gcloud services enable `
  run.googleapis.com `
  artifactregistry.googleapis.com `
  aiplatform.googleapis.com `
  cloudbuild.googleapis.com `
  --project=$ProjectId
Assert-LastExit "enable APIs"

$ProjectNumber = (gcloud projects describe $ProjectId --format="value(projectNumber)").Trim()
$RuntimeSa = "$ProjectNumber-compute@developer.gserviceaccount.com"
Write-Host "Ensuring Vertex role for $RuntimeSa..."
gcloud projects add-iam-policy-binding $ProjectId `
  --member="serviceAccount:$RuntimeSa" `
  --role="roles/aiplatform.user" `
  --condition=None `
  --quiet *>$null
# IAM binding may already exist; ignore non-zero if role present

$repoOk = $false
gcloud artifacts repositories describe $ArRepo --location=$Region --project=$ProjectId *>$null
if ($LASTEXITCODE -eq 0) { $repoOk = $true }
if (-not $repoOk) {
  Write-Host "Creating Artifact Registry $ArRepo..."
  gcloud artifacts repositories create $ArRepo `
    --repository-format=docker `
    --location=$Region `
    --description="Arabic editorial proofreading demo" `
    --project=$ProjectId
  Assert-LastExit "create artifact registry"
}

$ApiImage = "$Region-docker.pkg.dev/$ProjectId/$ArRepo/${ApiService}:latest"
$WebImage = "$Region-docker.pkg.dev/$ProjectId/$ArRepo/${WebService}:latest"

Write-Host "Building + pushing API image..."
gcloud builds submit --tag $ApiImage --project=$ProjectId .
Assert-LastExit "API cloud build"

Write-Host "Deploying API..."
$ApiEnv = @(
  "AI_CLIENT=gemini",
  "USE_GCP=true",
  "GCP_PROJECT_ID=$ProjectId",
  "GCP_LOCATION=$Region",
  "DEMO_AUTH_REQUIRED=true",
  "PUBLIC_PASSWORD=$PublicPassword",
  "ADMIN_PASSWORD=$AdminPassword",
  "SQLITE_PATH=/tmp/app.db",
  "ENABLE_LETTER_VARIANT_WARNINGS=false",
  "CORS_ORIGINS=*"
) -join ","

gcloud run deploy $ApiService `
  --image=$ApiImage `
  --region=$Region `
  --project=$ProjectId `
  --platform=managed `
  --allow-unauthenticated `
  --memory=1Gi `
  --cpu=1 `
  --timeout=300 `
  --max-instances=3 `
  --set-env-vars=$ApiEnv `
  --quiet
Assert-LastExit "deploy API"

$ApiUrl = (gcloud run services describe $ApiService --region=$Region --project=$ProjectId --format="value(status.url)").Trim()
Write-Host "API_URL=$ApiUrl"

$Cloudbuild = @"
steps:
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - -t
      - $WebImage
      - --build-arg
      - VITE_API_BASE_URL=$ApiUrl
      - frontend
images:
  - $WebImage
"@
$CbPath = Join-Path $env:TEMP "proofreading-web-cloudbuild.yaml"
Set-Content -Path $CbPath -Value $Cloudbuild -Encoding ascii

Write-Host "Building + pushing frontend..."
gcloud builds submit --project=$ProjectId --config=$CbPath .
Assert-LastExit "frontend cloud build"

Write-Host "Deploying frontend..."
gcloud run deploy $WebService `
  --image=$WebImage `
  --region=$Region `
  --project=$ProjectId `
  --platform=managed `
  --allow-unauthenticated `
  --memory=512Mi `
  --cpu=1 `
  --max-instances=3 `
  --quiet
Assert-LastExit "deploy frontend"

$WebUrl = (gcloud run services describe $WebService --region=$Region --project=$ProjectId --format="value(status.url)").Trim()

# Keep CORS open for demo (*). Do not use --env-vars-file alone (it replaces all vars).
gcloud run services update $ApiService `
  --region=$Region `
  --project=$ProjectId `
  --update-env-vars="CORS_ORIGINS=*" `
  --quiet
Assert-LastExit "update API CORS"

Write-Host ""
Write-Host "========================================"
Write-Host "  Demo A deployed"
Write-Host "  UI:   $WebUrl"
Write-Host "  API:  $ApiUrl"
Write-Host "  Login: user / $PublicPassword  or  admin / (ADMIN_PASSWORD)"
Write-Host "========================================"
