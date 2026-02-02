#!/bin/bash
# GCP Infrastructure Setup Script
# This script creates the necessary GCP resources for Copo do Mundo application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
PROJECT_ID="${GCP_PROJECT_ID:-}"
DATASET_ID="${BIGQUERY_DATASET:-copo_do_mundo}"
TABLE_ID="${BIGQUERY_TABLE:-votes}"
BUCKET_NAME="${CLOUD_STORAGE_BUCKET:-}"
REGION="${GCP_REGION:-us-central1}"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    print_error "GCP_PROJECT_ID environment variable is not set."
    print_info "Please set it with: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

# Set the project
print_info "Setting GCP project to: $PROJECT_ID"
gcloud config set project "$PROJECT_ID"

# Enable required APIs
print_info "Enabling required GCP APIs..."
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create BigQuery dataset
print_info "Creating BigQuery dataset: $DATASET_ID"
if bq ls -d "$PROJECT_ID:$DATASET_ID" &> /dev/null; then
    print_warning "Dataset $DATASET_ID already exists. Skipping creation."
else
    bq mk --dataset --location=US "$PROJECT_ID:$DATASET_ID"
    print_info "Dataset $DATASET_ID created successfully."
fi

# Create BigQuery table
print_info "Creating BigQuery table: $TABLE_ID"
TABLE_REF="$PROJECT_ID.$DATASET_ID.$TABLE_ID"

if bq ls -t "$TABLE_REF" &> /dev/null; then
    print_warning "Table $TABLE_ID already exists. Skipping creation."
else
    bq mk --table \
        --schema "Nome:STRING,Participante:STRING,Categoria:STRING,Originalidade:INTEGER,Aparencia:INTEGER,Sabor:INTEGER,Data:TIMESTAMP" \
        "$TABLE_REF"
    print_info "Table $TABLE_ID created successfully."
fi

# Create Cloud Storage bucket
if [ -z "$BUCKET_NAME" ]; then
    BUCKET_NAME="${PROJECT_ID}-copo-do-mundo-images"
    print_warning "CLOUD_STORAGE_BUCKET not set. Using default: $BUCKET_NAME"
fi

print_info "Creating Cloud Storage bucket: $BUCKET_NAME"
if gsutil ls -b "gs://$BUCKET_NAME" &> /dev/null; then
    print_warning "Bucket $BUCKET_NAME already exists. Skipping creation."
else
    gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" "gs://$BUCKET_NAME"
    
    # Make bucket publicly readable for images
    gsutil iam ch allUsers:objectViewer "gs://$BUCKET_NAME"
    
    # Enable versioning
    gsutil versioning set on "gs://$BUCKET_NAME"
    
    print_info "Bucket $BUCKET_NAME created successfully."
fi

# Create service account for Cloud Run
SERVICE_ACCOUNT_NAME="copo-do-mundo-sa"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

print_info "Creating service account: $SERVICE_ACCOUNT_NAME"
if gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" &> /dev/null; then
    print_warning "Service account $SERVICE_ACCOUNT_EMAIL already exists. Skipping creation."
else
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --display-name="Copo do Mundo Service Account" \
        --description="Service account for Copo do Mundo Cloud Run service"
    
    # Grant necessary permissions
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/bigquery.dataEditor"
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/bigquery.jobUser"
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/storage.objectAdmin"
    
    print_info "Service account created and permissions granted."
fi

print_info ""
print_info "=========================================="
print_info "GCP Infrastructure Setup Complete!"
print_info "=========================================="
print_info ""
print_info "BigQuery Dataset: $DATASET_ID"
print_info "BigQuery Table: $TABLE_ID"
print_info "Cloud Storage Bucket: $BUCKET_NAME"
print_info "Service Account: $SERVICE_ACCOUNT_EMAIL"
print_info ""
print_info "Next steps:"
print_info "1. Set environment variables in your Cloud Run service:"
print_info "   - GCP_PROJECT_ID=$PROJECT_ID"
print_info "   - BIGQUERY_DATASET=$DATASET_ID"
print_info "   - BIGQUERY_TABLE=$TABLE_ID"
print_info "   - CLOUD_STORAGE_BUCKET=$BUCKET_NAME"
print_info "   - STORAGE_BACKEND=gcp"
print_info "2. Configure Cloud Run to use service account: $SERVICE_ACCOUNT_EMAIL"
print_info ""
