param(
  [Parameter(Mandatory = $true)][string]$Source,
  [Parameter(Mandatory = $true)][string]$Destination,
  [string]$DatasetId = "",
  [switch]$Overwrite
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$env:DATA_BACKEND = if ($env:DATA_BACKEND) { $env:DATA_BACKEND } else { "gcs" }
$env:GCS_DATA_BUCKET = if ($env:GCS_DATA_BUCKET) { $env:GCS_DATA_BUCKET } else { "arabic-proofreading-data-ooredoo-499510" }

$py = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
$argsList = @(
  "scripts\download_dataset.py",
  "--source", $Source,
  "--destination", $Destination,
  "--backend", "gcs"
)
if ($DatasetId) { $argsList += @("--dataset-id", $DatasetId) }
if ($Overwrite) { $argsList += "--overwrite" }

& $py @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
