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
gcloud services enable secretmanager.googleapis.com
gcloud services enable iamcredentials.googleapis.com

# Create Artifact Registry repository
REPO_NAME="copo-do-mundo-repo"
print_info "Creating Artifact Registry repository: $REPO_NAME"
if gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &> /dev/null; then
    print_warning "Repository $REPO_NAME already exists. Skipping creation."
else
    gcloud artifacts repositories create "$REPO_NAME" \
        --repository-format=docker \
        --location="$REGION" \
        --description="Docker repository for Copo do Mundo"
    print_info "Repository $REPO_NAME created successfully."
fi

# Create BigQuery dataset
print_info "Creating BigQuery dataset: $DATASET_ID"
if bq show "$PROJECT_ID:$DATASET_ID" &> /dev/null; then
    print_warning "Dataset $DATASET_ID already exists. Skipping creation."
else
    bq mk --dataset --location=US "$PROJECT_ID:$DATASET_ID"
    print_info "Dataset $DATASET_ID created successfully."
fi

# Create BigQuery table
print_info "Creating BigQuery table: $TABLE_ID"
TABLE_REF="$PROJECT_ID:$DATASET_ID.$TABLE_ID"

if bq show "$TABLE_REF" &> /dev/null; then
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
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/secretmanager.secretAccessor"
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/artifactregistry.writer"
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/run.admin"
    
    gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_EMAIL" \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="roles/iam.serviceAccountUser" \
        --project="$PROJECT_ID"
    
    print_info "Service account created and permissions granted."
fi

# Set up Workload Identity Federation for GitHub Actions
print_info "Setting up Workload Identity Federation for GitHub Actions..."
POOL_NAME="github-actions-pool"
PROVIDER_NAME="github-provider"
REPO_NAME="felipbizz/copo-do-mundo"

if gcloud iam workload-identity-pools describe "$POOL_NAME" --location="global" &> /dev/null; then
    print_warning "Workload Identity Pool $POOL_NAME already exists."
else
    gcloud iam workload-identity-pools create "$POOL_NAME" \
        --location="global" \
        --display-name="GitHub Actions Pool" \
        --description="OIDC pool for GitHub Actions"
    print_info "Created Workload Identity Pool $POOL_NAME"
fi

if gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
    --workload-identity-pool="$POOL_NAME" --location="global" &> /dev/null; then
    print_warning "Workload Identity Provider $PROVIDER_NAME already exists."
else
    gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
        --location="global" \
        --workload-identity-pool="$POOL_NAME" \
        --display-name="GitHub provider" \
        --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
        --attribute-condition="assertion.repository == '$REPO_NAME'" \
        --issuer-uri="https://token.actions.githubusercontent.com"
    print_info "Created Workload Identity Provider $PROVIDER_NAME"
fi

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
WIF_POOL_ID="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME"
WIF_PROVIDER_ID="$WIF_POOL_ID/providers/$PROVIDER_NAME"

# Bind Service Account to GitHub Repo
print_info "Binding Service Account to Workload Identity Pool..."
gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/$WIF_POOL_ID/attribute.repository/$REPO_NAME"

# Set up Secret Manager for ADMIN_PASSWORD
print_info "Setting up Secret Manager for ADMIN_PASSWORD..."
if gcloud secrets describe admin-password &> /dev/null; then
    print_warning "Secret admin-password already exists."
else
    gcloud secrets create admin-password --replication-policy="automatic"
    echo -n "change_me_to_a_secure_password" | gcloud secrets versions add admin-password --data-file=-
    print_info "Created secret admin-password with default value 'change_me_to_a_secure_password'"
    print_info "Please update this secret in the GCP Console -> Security -> Secret Manager!"
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
print_info "Add these to your GitHub Repository Variables (Settings -> Secrets and variables -> Actions -> Variables):"
print_info "GCP_PROJECT_ID=$PROJECT_ID"
print_info "BIGQUERY_DATASET=$DATASET_ID"
print_info "BIGQUERY_TABLE=$TABLE_ID"
print_info "CLOUD_STORAGE_BUCKET=$BUCKET_NAME"
print_info "WIF_PROVIDER=$WIF_PROVIDER_ID"
print_info "WIF_SERVICE_ACCOUNT=$SERVICE_ACCOUNT_EMAIL"
print_info "CLOUD_RUN_SERVICE_ACCOUNT=$SERVICE_ACCOUNT_EMAIL"
print_info ""
print_info "Next steps:"
print_info "1. Update the 'admin-password' value in GCP Secret Manager"
print_info "2. Push to GitHub to trigger deployment!"
print_info ""
