# Deployment Guide

This guide explains how to deploy Copo do Mundo to Google Cloud Run.

## Prerequisites

1. **Google Cloud Platform Account**
   - Create a GCP project
   - Enable billing
   - Install [gcloud CLI](https://cloud.google.com/sdk/docs/install)

2. **GitHub Repository**
   - Code pushed to GitHub
   - GitHub Actions enabled

3. **Required GCP Services**
   - Cloud Run
   - BigQuery
   - Cloud Storage
   - Container Registry or Artifact Registry
   - Cloud Build (for CI/CD)

## Initial Setup

### 1. Set Up GCP Infrastructure

Run the infrastructure setup script to create all necessary resources:

```bash
# Set environment variables
export GCP_PROJECT_ID=your-project-id
export BIGQUERY_DATASET=copo_do_mundo
export BIGQUERY_TABLE=votes
export CLOUD_STORAGE_BUCKET=your-project-id-copo-do-mundo-images
export GCP_REGION=us-central1

# Run setup script
chmod +x infra/gcp-setup.sh
./infra/gcp-setup.sh
```

This script will:
- Enable required GCP APIs
- Create BigQuery dataset and table
- Create Cloud Storage bucket
- Create service account with appropriate permissions

### 2. Configure GitHub Secrets

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_SA_KEY`: Service account JSON key (for authentication)
- `BIGQUERY_DATASET`: BigQuery dataset name (default: `copo_do_mundo`)
- `BIGQUERY_TABLE`: BigQuery table name (default: `votes`)
- `CLOUD_STORAGE_BUCKET`: Cloud Storage bucket name
- `CLOUD_RUN_SERVICE_ACCOUNT`: Service account email (e.g., `copo-do-mundo-sa@project-id.iam.gserviceaccount.com`)
- `ADMIN_PASSWORD`: Admin password for the application

#### Creating Service Account Key

```bash
# Create service account key
gcloud iam service-accounts keys create key.json \
  --iam-account=copo-do-mundo-sa@PROJECT_ID.iam.gserviceaccount.com

# Copy the contents of key.json to GitHub secret GCP_SA_KEY
cat key.json
```

**Note:** For production, consider using [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) instead of service account keys.

### 3. Migrate Existing Data (Optional)

If you have existing data in local files, migrate it to GCP:

```bash
# Set environment variables
export GCP_PROJECT_ID=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
export BIGQUERY_DATASET=copo_do_mundo
export BIGQUERY_TABLE=votes
export CLOUD_STORAGE_BUCKET=your-bucket-name

# Dry run first to validate
python scripts/migrate_data.py --dry-run

# Actual migration
python scripts/migrate_data.py
```

## Deployment

### Automatic Deployment via GitHub Actions

1. **Push to main branch**: The workflow will automatically trigger on push to `main` or `master`
2. **Manual trigger**: Go to Actions → Deploy to Cloud Run → Run workflow

The workflow will:
- Build Docker image
- Push to Google Container Registry
- Deploy to Cloud Run
- Configure environment variables

### Manual Deployment

If you prefer to deploy manually:

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Build and push image
docker build -t gcr.io/YOUR_PROJECT_ID/copo-do-mundo:latest .
docker push gcr.io/YOUR_PROJECT_ID/copo-do-mundo:latest

# Deploy to Cloud Run
gcloud run deploy copo-do-mundo \
  --image gcr.io/YOUR_PROJECT_ID/copo-do-mundo:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8501 \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars "STORAGE_BACKEND=gcp,GCP_PROJECT_ID=YOUR_PROJECT_ID,BIGQUERY_DATASET=copo_do_mundo,BIGQUERY_TABLE=votes,CLOUD_STORAGE_BUCKET=YOUR_BUCKET_NAME,ADMIN_PASSWORD=your-password" \
  --service-account copo-do-mundo-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## Environment Variables

The following environment variables are required for Cloud Run:

| Variable | Description | Example |
|----------|-------------|---------|
| `STORAGE_BACKEND` | Storage backend to use | `gcp` |
| `GCP_PROJECT_ID` | GCP project ID | `my-project` |
| `BIGQUERY_DATASET` | BigQuery dataset name | `copo_do_mundo` |
| `BIGQUERY_TABLE` | BigQuery table name | `votes` |
| `CLOUD_STORAGE_BUCKET` | Cloud Storage bucket name | `my-bucket` |
| `ADMIN_PASSWORD` | Admin password | `secure-password` |

These are automatically set by the GitHub Actions workflow, but can be updated in Cloud Run console if needed.

## Post-Deployment

### Verify Deployment

1. Get the service URL:
   ```bash
   gcloud run services describe copo-do-mundo --region us-central1 --format 'value(status.url)'
   ```

2. Visit the URL in your browser

3. Test admin login with the configured password

### Monitor Logs

```bash
# View logs
gcloud run services logs read copo-do-mundo --region us-central1 --limit 50
```

### Update Configuration

To update environment variables or other settings:

```bash
gcloud run services update copo-do-mundo \
  --region us-central1 \
  --update-env-vars "ADMIN_PASSWORD=new-password"
```

## Troubleshooting

### Common Issues

1. **Authentication errors**
   - Verify service account has correct permissions
   - Check that `GOOGLE_APPLICATION_CREDENTIALS` is set (for local testing)

2. **BigQuery errors**
   - Ensure dataset and table exist
   - Verify service account has `bigquery.dataEditor` and `bigquery.jobUser` roles

3. **Cloud Storage errors**
   - Ensure bucket exists
   - Verify service account has `storage.objectAdmin` role

4. **Image loading issues**
   - Check bucket permissions (should be publicly readable)
   - Verify image paths are correct

### Rollback

To rollback to a previous version:

```bash
# List revisions
gcloud run revisions list --service copo-do-mundo --region us-central1

# Rollback to specific revision
gcloud run services update-traffic copo-do-mundo \
  --to-revisions REVISION_NAME=100 \
  --region us-central1
```

## Cost Optimization

- Use Cloud Run's automatic scaling (0 to N instances)
- Set appropriate memory and CPU limits
- Monitor usage in GCP Console
- Consider using Cloud Run's free tier (2 million requests/month)

## Security Best Practices

1. **Use Workload Identity Federation** instead of service account keys when possible
2. **Rotate admin password** regularly
3. **Enable Cloud Run authentication** if you don't need public access
4. **Use least privilege** for service account permissions
5. **Enable Cloud Storage bucket versioning** for data recovery
6. **Monitor access logs** regularly

## Next Steps

- Set up custom domain (optional)
- Configure Cloud CDN for better performance (optional)
- Set up monitoring and alerts
- Configure backup strategy for BigQuery data
