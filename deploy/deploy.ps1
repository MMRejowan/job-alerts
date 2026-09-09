# ==============================================================================
# PowerShell Google Cloud Deployment Script (for Windows with gcloud CLI)
# ==============================================================================
param (
    [string]$Region = "asia-south1",
    [string]$FunctionName = "daily-dev-job-alert",
    [string]$SchedulerJobName = "daily-dev-job-alert-trigger"
)

$ErrorActionPreference = "Stop"

Write-Host "=== 🚀 Deploying Dev Job Alert Engine to Google Cloud ===" -ForegroundColor Cyan

# 1. Check gcloud CLI
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Error "gcloud CLI is not found on your PATH. Please install Google Cloud SDK or deploy using Google Cloud Shell."
}

# 2. Get active project
$ProjectId = (gcloud config get-value project 2>$null).Trim()
if ([string]::IsNullOrWhiteSpace($ProjectId) -or $ProjectId -eq "(unset)") {
    Write-Error "Google Cloud project is not set. Run: gcloud config set project <YOUR_PROJECT_ID>"
}
Write-Host "✅ Target GCP Project: $ProjectId" -ForegroundColor Green

# 3. Read .env if present
$EnvFile = Join-Path $PSScriptRoot "..\.env"
$GmailUser = "mushtaq.mdrizwan@gmail.com"
$GmailAppPassword = ""
$AlertRecipient = $GmailUser

if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^\s*([^#=]+)=(.*)$") {
            $k = $matches[1].Trim()
            $v = $matches[2].Trim()
            if ($k -eq "GMAIL_USER") { $GmailUser = $v }
            if ($k -eq "GMAIL_APP_PASSWORD") { $GmailAppPassword = $v }
            if ($k -eq "ALERT_RECIPIENT") { $AlertRecipient = $v }
        }
    }
}

if ([string]::IsNullOrWhiteSpace($GmailAppPassword) -or $GmailAppPassword -eq "your-16-char-app-password") {
    $GmailAppPassword = Read-Host "Enter your 16-character Gmail App Password"
}

$BucketName = "daily-job-alerts-$ProjectId"

# 4. Enable Services
Write-Host "Enabling Google Cloud APIs..." -ForegroundColor Yellow
gcloud services enable cloudfunctions.googleapis.com cloudbuild.googleapis.com run.googleapis.com cloudscheduler.googleapis.com storage.googleapis.com artifactregistry.googleapis.com

# 5. Create State Bucket if needed
Write-Host "Ensuring GCS bucket gs://$BucketName exists..." -ForegroundColor Yellow
$bucketExists = gsutil ls -b "gs://$BucketName" 2>$null
if (-not $bucketExists) {
    gcloud storage buckets create "gs://$BucketName" --location=$Region
}

# 6. Deploy Function Gen 2
$SourceDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Write-Host "Deploying Cloud Function Gen 2 from $SourceDir..." -ForegroundColor Yellow

gcloud functions deploy $FunctionName `
    --gen2 `
    --runtime=python312 `
    --region=$Region `
    --source=$SourceDir `
    --entry-point=daily_job_alert `
    --trigger-http `
    --allow-unauthenticated `
    --timeout=300s `
    --memory=512Mi `
    --set-env-vars="GMAIL_USER=$GmailUser,GMAIL_APP_PASSWORD=$GmailAppPassword,ALERT_RECIPIENT=$AlertRecipient,GCS_BUCKET_NAME=$BucketName"

# 7. Get Function URL
$FunctionUrl = (gcloud functions describe $FunctionName --gen2 --region=$Region --format="value(serviceConfig.uri)").Trim()
Write-Host "✅ Function URL: $FunctionUrl" -ForegroundColor Green

# 8. Create or Update Scheduler
Write-Host "Setting up Cloud Scheduler (Daily 8:30 AM IST)..." -ForegroundColor Yellow
$schedExists = gcloud scheduler jobs describe $SchedulerJobName --location=$Region 2>$null
if ($schedExists) {
    gcloud scheduler jobs update http $SchedulerJobName `
        --location=$Region `
        --schedule="30 8 * * *" `
        --time-zone="Asia/Kolkata" `
        --uri=$FunctionUrl `
        --http-method=GET
} else {
    gcloud scheduler jobs create http $SchedulerJobName `
        --location=$Region `
        --schedule="30 8 * * *" `
        --time-zone="Asia/Kolkata" `
        --uri=$FunctionUrl `
        --http-method=GET
}

Write-Host "`n🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "Your function will run daily at 8:30 AM IST and deliver directly to $AlertRecipient." -ForegroundColor Green
