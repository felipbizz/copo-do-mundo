#!/usr/bin/env python3
"""Migration script to move data from local storage to GCP.

This script migrates:
- Votes from CSV file to BigQuery
- Images from local directory to Cloud Storage
"""

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from PIL import Image

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.data.storage.bigquery_storage import BigQueryVoteStorage
from backend.data.storage.cloud_storage import CloudStorageImageStorage
from config import CONFIG

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def migrate_votes(
    csv_file: str,
    project_id: str,
    dataset_id: str,
    table_id: str,
    dry_run: bool = False,
) -> bool:
    """Migrate votes from CSV to BigQuery.

    Args:
        csv_file: Path to the CSV file with votes.
        project_id: GCP project ID.
        dataset_id: BigQuery dataset ID.
        table_id: BigQuery table ID.
        dry_run: If True, only validate without migrating.

    Returns:
        bool: True if migration was successful.
    """
    try:
        logger.info(f"Reading votes from {csv_file}")
        if not os.path.exists(csv_file):
            logger.error(f"CSV file not found: {csv_file}")
            return False

        df = pd.read_csv(csv_file)
        logger.info(f"Found {len(df)} votes to migrate")

        if df.empty:
            logger.warning("No votes to migrate")
            return True

        # Validate required columns
        required_columns = [
            "Nome",
            "Participante",
            "Categoria",
            "Originalidade",
            "Aparencia",
            "Sabor",
            "Data",
        ]
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False

        if dry_run:
            logger.info("DRY RUN: Would migrate votes to BigQuery")
            logger.info(f"  Project: {project_id}")
            logger.info(f"  Dataset: {dataset_id}")
            logger.info(f"  Table: {table_id}")
            logger.info(f"  Rows: {len(df)}")
            return True

        # Initialize BigQuery storage
        logger.info("Connecting to BigQuery...")
        storage = BigQueryVoteStorage(project_id=project_id, dataset_id=dataset_id, table_id=table_id)

        # Append data to BigQuery
        logger.info("Uploading votes to BigQuery...")
        storage.append_data(df)

        logger.info(f"Successfully migrated {len(df)} votes to BigQuery")
        return True

    except Exception as e:
        logger.error(f"Error migrating votes: {str(e)}", exc_info=True)
        return False


def migrate_images(
    images_dir: str,
    project_id: str,
    bucket_name: str,
    dry_run: bool = False,
) -> bool:
    """Migrate images from local directory to Cloud Storage.

    Args:
        images_dir: Path to the local images directory.
        project_id: GCP project ID.
        bucket_name: Cloud Storage bucket name.
        dry_run: If True, only validate without migrating.

    Returns:
        bool: True if migration was successful.
    """
    try:
        logger.info(f"Scanning images directory: {images_dir}")
        if not os.path.exists(images_dir):
            logger.warning(f"Images directory not found: {images_dir}")
            return True  # Not an error if directory doesn't exist

        image_files = (
            list(Path(images_dir).glob("*.jpg"))
            + list(Path(images_dir).glob("*.jpeg"))
            + list(Path(images_dir).glob("*.png"))
        )

        if not image_files:
            logger.warning("No images found to migrate")
            return True

        logger.info(f"Found {len(image_files)} images to migrate")

        if dry_run:
            logger.info("DRY RUN: Would migrate images to Cloud Storage")
            logger.info(f"  Project: {project_id}")
            logger.info(f"  Bucket: {bucket_name}")
            logger.info(f"  Images: {len(image_files)}")
            for img_file in image_files[:5]:  # Show first 5
                logger.info(f"    - {img_file.name}")
            if len(image_files) > 5:
                logger.info(f"    ... and {len(image_files) - 5} more")
            return True

        # Initialize Cloud Storage
        logger.info("Connecting to Cloud Storage...")
        storage = CloudStorageImageStorage(project_id=project_id, bucket_name=bucket_name)

        # Upload each image
        success_count = 0
        for img_file in image_files:
            try:
                logger.info(f"Uploading {img_file.name}...")
                image = Image.open(img_file)

                # Use filename as the storage path
                storage_path = img_file.name

                if storage.save_image(image, storage_path):
                    success_count += 1
                    logger.info(f"  ✓ Uploaded {img_file.name}")
                else:
                    logger.error(f"  ✗ Failed to upload {img_file.name}")

            except Exception as e:
                logger.error(f"Error uploading {img_file.name}: {str(e)}")

        logger.info(f"Successfully migrated {success_count}/{len(image_files)} images")
        return success_count == len(image_files)

    except Exception as e:
        logger.error(f"Error migrating images: {str(e)}", exc_info=True)
        return False


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description="Migrate data from local storage to GCP")
    parser.add_argument(
        "--csv-file",
        type=str,
        default=CONFIG.get("DATA_FILE", "data/votes.csv"),
        help="Path to CSV file with votes",
    )
    parser.add_argument(
        "--images-dir",
        type=str,
        default=CONFIG.get("IMAGES_DIR", "data/images"),
        help="Path to images directory",
    )
    parser.add_argument(
        "--project-id",
        type=str,
        default=os.getenv("GCP_PROJECT_ID"),
        help="GCP project ID (or set GCP_PROJECT_ID env var)",
    )
    parser.add_argument(
        "--dataset-id",
        type=str,
        default=os.getenv("BIGQUERY_DATASET", "copo_do_mundo"),
        help="BigQuery dataset ID (or set BIGQUERY_DATASET env var)",
    )
    parser.add_argument(
        "--table-id",
        type=str,
        default=os.getenv("BIGQUERY_TABLE", "votes"),
        help="BigQuery table ID (or set BIGQUERY_TABLE env var)",
    )
    parser.add_argument(
        "--bucket-name",
        type=str,
        default=os.getenv("CLOUD_STORAGE_BUCKET"),
        help="Cloud Storage bucket name (or set CLOUD_STORAGE_BUCKET env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without actually migrating data",
    )
    parser.add_argument(
        "--votes-only",
        action="store_true",
        help="Only migrate votes, skip images",
    )
    parser.add_argument(
        "--images-only",
        action="store_true",
        help="Only migrate images, skip votes",
    )

    args = parser.parse_args()

    # Validate required arguments
    if not args.project_id:
        logger.error("GCP_PROJECT_ID must be provided (--project-id or env var)")
        return 1

    if not args.bucket_name and not args.images_only:
        logger.error("CLOUD_STORAGE_BUCKET must be provided (--bucket-name or env var)")
        return 1

    logger.info("=" * 60)
    logger.info("Copo do Mundo Data Migration")
    logger.info("=" * 60)
    logger.info(f"Project ID: {args.project_id}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info("")

    success = True

    # Migrate votes
    if not args.images_only:
        logger.info("Migrating votes...")
        logger.info("-" * 60)
        votes_success = migrate_votes(
            csv_file=args.csv_file,
            project_id=args.project_id,
            dataset_id=args.dataset_id,
            table_id=args.table_id,
            dry_run=args.dry_run,
        )
        success = success and votes_success
        logger.info("")

    # Migrate images
    if not args.votes_only and args.bucket_name:
        logger.info("Migrating images...")
        logger.info("-" * 60)
        images_success = migrate_images(
            images_dir=args.images_dir,
            project_id=args.project_id,
            bucket_name=args.bucket_name,
            dry_run=args.dry_run,
        )
        success = success and images_success
        logger.info("")

    if success:
        logger.info("=" * 60)
        logger.info("Migration completed successfully!")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("Migration completed with errors. Please review the logs above.")
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
