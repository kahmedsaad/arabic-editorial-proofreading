param(
  [Parameter(Mandatory = $true)][string]$Source,
  [Parameter(Mandatory = $true)][string]$Destination,
  [Parameter(Mandatory = $true)][string]$DatasetId,
  [string]$SourceType = "external_public",
  [string]$License = "documented-separately",
  [switch]$Yes,
  [switch]$Overwrite
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$env:DATA_BACKEND = if ($env:DATA_BACKEND) { $env:DATA_BACKEND } else { "gcs" }
$env:GCP_PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "ooredoo-499510" }
$env:GCS_DATA_BUCKET = if ($env:GCS_DATA_BUCKET) { $env:GCS_DATA_BUCKET } else { "arabic-proofreading-data-ooredoo-499510" }

$py = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$argsList = @(
  "scripts\upload_dataset.py",
  "--source", $Source,
  "--destination", $Destination,
  "--dataset-id", $DatasetId,
  "--source-type", $SourceType,
  "--license", $License,
  "--backend", "gcs"
)
if ($Yes) { $argsList += "--yes" }
if ($Overwrite) { $argsList += "--overwrite" }

& $py @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
