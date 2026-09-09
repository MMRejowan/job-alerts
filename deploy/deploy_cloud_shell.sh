#!/usr/bin/env bash
# ==============================================================================
# 1-Command Google Cloud Deployment Script (for Google Cloud Shell)
# ==============================================================================
set -e

echo "=== 🚀 Deploying Dev Job Alert Engine to Google Cloud ==="

# 1. Verify gcloud is logged in and project is set
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "(unset)" ]; then
  echo "❌ Error: Google Cloud Project ID is not set."
  echo "Run: gcloud config set project <YOUR_PROJECT_ID>"
  exit 1
fi

echo "✅ Target GCP Project: $PROJECT_ID"
REGION="asia-south1" # Mumbai, India (Lowest latency & within free tier)
FUNCTION_NAME="daily-dev-job-alert"
SCHEDULER_JOB_NAME="daily-dev-job-alert-trigger"
BUCKET_NAME="daily-job-alerts-${PROJECT_ID}"

# 2. Check credentials
if [ -z "$GMAIL_APP_PASSWORD" ]; then
  if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
  fi
fi

if [ -z "$GMAIL_APP_PASSWORD" ] || [ "$GMAIL_APP_PASSWORD" = "your-16-char-app-password" ]; then
  echo "⚠️ Warning: GMAIL_APP_PASSWORD is not set or using default placeholder."
  read -p "Enter your 16-character Gmail App Password: " GMAIL_APP_PASSWORD
fi

GMAIL_USER="${GMAIL_USER:-mushtaq.mdrizwan@gmail.com}"
ALERT_RECIPIENT="${ALERT_RECIPIENT:-$GMAIL_USER}"

# 3. Enable Required Google Cloud APIs
echo "Enabling required Google Cloud APIs (Cloud Functions, Cloud Build, Cloud Run, Cloud Scheduler, Storage)..."
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  cloudscheduler.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com

# 4. Create GCS Bucket for Deduplication State (if it doesn't exist)
echo "Checking GCS state bucket: gs://${BUCKET_NAME}..."
if ! gsutil ls -b "gs://${BUCKET_NAME}" >/dev/null 2>&1; then
  echo "Creating state bucket gs://${BUCKET_NAME} in ${REGION}..."
  gcloud storage buckets create "gs://${BUCKET_NAME}" --location="${REGION}"
else
  echo "✅ Bucket gs://${BUCKET_NAME} already exists."
fi

# 5. Deploy Google Cloud Function (Gen 2)
echo "Deploying Cloud Function Gen 2: ${FUNCTION_NAME}..."
gcloud functions deploy "${FUNCTION_NAME}" \
  --gen2 \
  --runtime=python312 \
  --region="${REGION}" \
  --source=. \
  --entry-point=daily_job_alert \
  --trigger-http \
  --allow-unauthenticated \
  --timeout=300s \
  --memory=512Mi \
  --set-env-vars=GMAIL_USER="${GMAIL_USER}",GMAIL_APP_PASSWORD="${GMAIL_APP_PASSWORD}",ALERT_RECIPIENT="${ALERT_RECIPIENT}",GCS_BUCKET_NAME="${BUCKET_NAME}"

# 6. Retrieve Function Trigger URL
FUNCTION_URL=$(gcloud functions describe "${FUNCTION_NAME}" --gen2 --region="${REGION}" --format="value(serviceConfig.uri)")
echo "✅ Function deployed at: ${FUNCTION_URL}"

# 7. Configure Cloud Scheduler (Runs every day at 8:30 AM IST / 03:00 AM UTC)
echo "Configuring Cloud Scheduler job..."
if gcloud scheduler jobs describe "${SCHEDULER_JOB_NAME}" --location="${REGION}" >/dev/null 2>&1; then
  echo "Updating existing Cloud Scheduler job..."
  gcloud scheduler jobs update http "${SCHEDULER_JOB_NAME}" \
    --location="${REGION}" \
    --schedule="30 8 * * *" \
    --time-zone="Asia/Kolkata" \
    --uri="${FUNCTION_URL}" \
    --http-method=GET
else
  echo "Creating new Cloud Scheduler job (Daily 8:30 AM IST)..."
  gcloud scheduler jobs create http "${SCHEDULER_JOB_NAME}" \
    --location="${REGION}" \
    --schedule="30 8 * * *" \
    --time-zone="Asia/Kolkata" \
    --uri="${FUNCTION_URL}" \
    --http-method=GET
fi

echo ""
echo "=================================================================="
echo "🎉 DEPLOYMENT SUCCESSFUL!"
echo "=================================================================="
echo "• Function URL:   ${FUNCTION_URL}"
echo "• Schedule:       Every morning at 8:30 AM IST (Asia/Kolkata)"
echo "• State Bucket:   gs://${BUCKET_NAME}"
echo "• Recipient:      ${ALERT_RECIPIENT}"
echo ""
echo "To trigger a test execution right now, run:"
echo "  gcloud scheduler jobs run ${SCHEDULER_JOB_NAME} --location=${REGION}"
echo "=================================================================="
