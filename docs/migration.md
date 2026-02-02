# Data Migration Guide

This guide explains how to migrate existing data from local storage to GCP services.

## Overview

The migration process moves:
- **Votes**: From `data/votes.csv` to BigQuery
- **Images**: From `data/images/` directory to Cloud Storage

## Prerequisites

1. GCP project with BigQuery and Cloud Storage set up (see [deployment guide](deployment.md))
2. Service account with appropriate permissions
3. Local credentials configured

## Setup

### 1. Install Dependencies

Ensure you have the required Python packages:

```bash
uv pip install google-cloud-bigquery google-cloud-storage
```

### 2. Configure Credentials

Set up authentication:

```bash
# Option 1: Service account key file
export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json

# Option 2: Use gcloud auth (for local development)
gcloud auth application-default login
```

### 3. Set Environment Variables

```bash
export GCP_PROJECT_ID=your-project-id
export BIGQUERY_DATASET=copo_do_mundo
export BIGQUERY_TABLE=votes
export CLOUD_STORAGE_BUCKET=your-bucket-name
```

## Running Migration

### Dry Run (Recommended First Step)

Always run a dry run first to validate the migration:

```bash
python scripts/migrate_data.py --dry-run
```

This will:
- Validate CSV file structure
- Count votes and images to migrate
- Check GCP connectivity
- **Not** actually migrate any data

### Full Migration

#### Migrate Everything

```bash
python scripts/migrate_data.py
```

#### Migrate Only Votes

```bash
python scripts/migrate_data.py --votes-only
```

#### Migrate Only Images

```bash
python scripts/migrate_data.py --images-only
```

### Custom Paths

If your data is in different locations:

```bash
python scripts/migrate_data.py \
  --csv-file /path/to/custom/votes.csv \
  --images-dir /path/to/custom/images
```

## Migration Process

### Votes Migration

1. Reads CSV file from local storage
2. Validates required columns exist
3. Connects to BigQuery
4. Appends data to BigQuery table (preserves existing data)
5. Reports success/failure

**Note**: The migration uses `append_data`, so it won't overwrite existing BigQuery data. If you need to replace all data, clear the BigQuery table first.

### Images Migration

1. Scans local images directory
2. Finds all `.jpg`, `.jpeg`, and `.png` files
3. For each image:
   - Opens and validates the image
   - Uploads to Cloud Storage
   - Makes image publicly accessible
4. Reports success/failure for each image

**Note**: Images are uploaded with their original filenames. Make sure filenames match the expected format: `participant_{N}_{category}.jpg`

## Verification

After migration, verify the data:

### Check BigQuery

```bash
# Query vote count
bq query --use_legacy_sql=false \
  "SELECT COUNT(*) as total_votes FROM \`PROJECT_ID.copo_do_mundo.votes\`"

# View sample votes
bq query --use_legacy_sql=false \
  "SELECT * FROM \`PROJECT_ID.copo_do_mundo.votes\` LIMIT 10"
```

### Check Cloud Storage

```bash
# List images in bucket
gsutil ls gs://BUCKET_NAME/

# Count images
gsutil ls gs://BUCKET_NAME/*.jpg | wc -l
```

### Test Application

1. Deploy application to Cloud Run (see [deployment guide](deployment.md))
2. Set `STORAGE_BACKEND=gcp` environment variable
3. Access the application and verify:
   - Votes are displayed correctly
   - Images load properly
   - New votes can be submitted

## Troubleshooting

### CSV File Issues

**Error**: "Missing required columns"

**Solution**: Ensure your CSV has all required columns:
- Nome
- Participante
- Categoria
- Originalidade
- Aparencia
- Sabor
- Data

**Error**: "CSV file not found"

**Solution**: Check the file path. Use `--csv-file` to specify custom path.

### BigQuery Issues

**Error**: "Dataset not found"

**Solution**: Run the infrastructure setup script first:
```bash
./infra/gcp-setup.sh
```

**Error**: "Permission denied"

**Solution**: Ensure service account has:
- `roles/bigquery.dataEditor`
- `roles/bigquery.jobUser`

### Cloud Storage Issues

**Error**: "Bucket not found"

**Solution**: Create the bucket or run infrastructure setup:
```bash
gsutil mb -p PROJECT_ID -l us-central1 gs://BUCKET_NAME
```

**Error**: "Permission denied"

**Solution**: Ensure service account has:
- `roles/storage.objectAdmin`

### Image Issues

**Error**: "Failed to upload image"

**Solution**:
- Check image file is not corrupted
- Verify image format is supported (JPEG, PNG)
- Check file size (very large images may timeout)

## Rollback

If you need to rollback the migration:

### Rollback Votes

1. Export data from BigQuery:
   ```bash
   bq extract --destination_format=CSV \
     PROJECT_ID:dataset.table \
     gs://BUCKET_NAME/backup-votes.csv
   ```

2. Download and restore to local CSV:
   ```bash
   gsutil cp gs://BUCKET_NAME/backup-votes.csv data/votes.csv
   ```

### Rollback Images

1. Download images from Cloud Storage:
   ```bash
   gsutil -m cp -r gs://BUCKET_NAME/* data/images/
   ```

2. Set `STORAGE_BACKEND=local` in application

## Best Practices

1. **Always run dry run first** to catch issues early
2. **Backup existing data** before migration
3. **Migrate in stages**: votes first, then images
4. **Verify data** after migration
5. **Test application** with migrated data before switching production
6. **Keep local backups** until migration is verified

## Post-Migration

After successful migration:

1. Update application configuration to use `STORAGE_BACKEND=gcp`
2. Test all functionality
3. Monitor for any issues
4. Keep local data as backup for a period
5. Document the migration date and details

## Support

If you encounter issues:

1. Check the logs: `python scripts/migrate_data.py --dry-run`
2. Verify GCP setup: `./infra/gcp-setup.sh`
3. Review [deployment guide](deployment.md) for infrastructure setup
4. Check GCP service status in Cloud Console
