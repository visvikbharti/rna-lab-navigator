"""
Celery tasks for automated backups.
Contains tasks for backing up Postgres database and Weaviate vector database.
"""

import os
import subprocess
import shutil
import logging
import tempfile
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import requests
from django.conf import settings
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger

# Set up logging
logger = get_task_logger(__name__)

# Backup constants
BACKUP_PATHS = {
    'postgres': os.path.join(settings.BASE_DIR, 'backups', 'postgres'),
    'weaviate': os.path.join(settings.BASE_DIR, 'backups', 'weaviate'),
    'media': os.path.join(settings.BASE_DIR, 'backups', 'media'),
}

# Ensure backup directories exist
for path in BACKUP_PATHS.values():
    os.makedirs(path, exist_ok=True)


@shared_task(bind=True, max_retries=3)
def backup_postgres_database(self):
    """
    Backup PostgreSQL database using pg_dump.
    Handles both local backups and S3 uploads if configured.
    """
    try:
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"pg_backup_{backup_timestamp}.sql"
        backup_path = os.path.join(BACKUP_PATHS['postgres'], backup_filename)
        
        # Get database connection details from settings
        db_settings = settings.DATABASES['default']
        
        # Set environment variables for pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        # Build pg_dump command
        cmd = [
            'pg_dump',
            '--host', db_settings['HOST'],
            '--port', db_settings['PORT'],
            '--username', db_settings['USER'],
            '--format=c',  # Custom format (compressed)
            '--file', backup_path,
            db_settings['NAME']
        ]
        
        # Execute pg_dump
        logger.info(f"Starting PostgreSQL backup: {backup_filename}")
        process = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8')
            logger.error(f"PostgreSQL backup failed: {error_msg}")
            raise Exception(f"pg_dump failed: {error_msg}")
        
        logger.info(f"PostgreSQL backup completed: {backup_path}")
        
        # Upload to S3 if configured
        if hasattr(settings, 'AWS_BACKUP_BUCKET'):
            s3_key = f"postgres/{backup_filename}"
            upload_to_s3(backup_path, s3_key, settings.AWS_BACKUP_BUCKET)
            
            # Clean up local file after successful S3 upload if configured
            if getattr(settings, 'BACKUP_CLEANUP_LOCAL', False):
                os.remove(backup_path)
                logger.info(f"Local backup file removed: {backup_path}")
        
        # Cleanup old backups
        cleanup_old_backups('postgres', settings.BACKUP_RETENTION_DAYS)
        
        return {
            'status': 'success',
            'backup_file': backup_path,
            'timestamp': backup_timestamp
        }
        
    except Exception as e:
        logger.error(f"Error during PostgreSQL backup: {str(e)}")
        try:
            self.retry(countdown=60 * 5)  # Retry after 5 minutes
        except MaxRetriesExceededError:
            logger.error("Max retries exceeded for PostgreSQL backup")
        raise


@shared_task(bind=True, max_retries=3)
def backup_weaviate_database(self):
    """
    Backup Weaviate vector database using Weaviate's backup API.
    Supports local or S3 backups depending on configuration.
    """
    try:
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"weaviate_backup_{backup_timestamp}"
        
        # Determine if we're using local or S3 backup
        if hasattr(settings, 'AWS_BACKUP_BUCKET') and settings.AWS_BACKUP_BUCKET:
            backend = "s3"
            backup_path = f"s3://{settings.AWS_BACKUP_BUCKET}/weaviate/{backup_name}"
        else:
            backend = "filesystem"
            backup_path = os.path.join(BACKUP_PATHS['weaviate'], backup_name)
            os.makedirs(backup_path, exist_ok=True)
        
        logger.info(f"Starting Weaviate backup: {backup_name} using {backend} backend")
        
        # Call Weaviate API to create backup
        weaviate_url = settings.WEAVIATE_URL.rstrip('/')
        backup_endpoint = f"{weaviate_url}/v1/backups"
        
        # Backup request payload
        payload = {
            "id": backup_name,
            "backend": backend
        }
        
        # Add backend-specific configuration
        if backend == "s3":
            # S3 config
            payload["s3Config"] = {
                "bucket": settings.AWS_BACKUP_BUCKET,
                "key": f"weaviate/{backup_name}",
                "accessKeyID": os.getenv("AWS_ACCESS_KEY_ID", ""),
                "secretAccessKey": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
                "endpoint": os.getenv("AWS_S3_ENDPOINT", ""),
                "useSSL": True
            }
        else:
            # Filesystem config
            payload["filesystem"] = {
                "path": backup_path
            }
        
        # Get authentication header if API key is configured
        headers = {"Content-Type": "application/json"}
        if settings.WEAVIATE_API_KEY:
            headers["Authorization"] = f"Bearer {settings.WEAVIATE_API_KEY}"
        
        # Create backup request
        response = requests.post(backup_endpoint, json=payload, headers=headers)
        
        if not response.ok:
            error_msg = f"Weaviate backup creation failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"Weaviate backup initiated: {backup_name}")
        
        # Wait for backup to complete (this might take a while for large databases)
        backup_status_endpoint = f"{backup_endpoint}/{backup_name}"
        
        # Poll for backup completion
        max_attempts = 30  # 30 attempts with 10 seconds between = 5 minutes max wait
        for attempt in range(max_attempts):
            status_response = requests.get(backup_status_endpoint, headers=headers)
            
            if not status_response.ok:
                logger.warning(f"Failed to get backup status: {status_response.status_code} - {status_response.text}")
                continue
            
            status_data = status_response.json()
            status = status_data.get("status", "")
            
            if status == "SUCCESS":
                logger.info(f"Weaviate backup completed successfully: {backup_name}")
                break
            elif status == "FAILED":
                error_msg = f"Weaviate backup failed: {status_data.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            else:
                # Still in progress, wait and retry
                import time
                time.sleep(10)  # Wait 10 seconds before checking again
        else:
            # If we get here, we've exceeded max attempts
            logger.warning(f"Backup status check timed out after {max_attempts} attempts. Assuming it's still running in the background.")
        
        # Cleanup old backups if using filesystem
        if backend == "filesystem":
            cleanup_old_backups('weaviate', settings.BACKUP_RETENTION_DAYS)
        
        return {
            'status': 'success',
            'backup_name': backup_name,
            'timestamp': backup_timestamp,
            'path': backup_path
        }
        
    except Exception as e:
        logger.error(f"Error during Weaviate backup: {str(e)}")
        try:
            self.retry(countdown=60 * 5)  # Retry after 5 minutes
        except MaxRetriesExceededError:
            logger.error("Max retries exceeded for Weaviate backup")
        raise


@shared_task(bind=True, max_retries=3)
def backup_media_files(self):
    """
    Backup media files (uploaded documents, images, etc.)
    """
    try:
        backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"media_backup_{backup_timestamp}.tar.gz"
        backup_path = os.path.join(BACKUP_PATHS['media'], backup_filename)
        
        # Create tar.gz archive of media directory
        media_dir = settings.MEDIA_ROOT
        
        logger.info(f"Starting media files backup: {backup_filename}")
        
        # Create the archive
        shutil.make_archive(
            backup_path.replace('.tar.gz', ''),  # Base name without extension
            'gztar',  # Format
            root_dir=os.path.dirname(media_dir),  # Parent directory
            base_dir=os.path.basename(media_dir)  # Directory to archive
        )
        
        logger.info(f"Media files backup completed: {backup_path}")
        
        # Upload to S3 if configured
        if hasattr(settings, 'AWS_BACKUP_BUCKET'):
            s3_key = f"media/{backup_filename}"
            upload_to_s3(backup_path, s3_key, settings.AWS_BACKUP_BUCKET)
            
            # Clean up local file after successful S3 upload if configured
            if getattr(settings, 'BACKUP_CLEANUP_LOCAL', False):
                os.remove(backup_path)
                logger.info(f"Local backup file removed: {backup_path}")
        
        # Cleanup old backups
        cleanup_old_backups('media', settings.BACKUP_RETENTION_DAYS)
        
        return {
            'status': 'success',
            'backup_file': backup_path,
            'timestamp': backup_timestamp
        }
        
    except Exception as e:
        logger.error(f"Error during media files backup: {str(e)}")
        try:
            self.retry(countdown=60 * 5)  # Retry after 5 minutes
        except MaxRetriesExceededError:
            logger.error("Max retries exceeded for media files backup")
        raise


def upload_to_s3(file_path, s3_key, bucket_name):
    """
    Upload a file to S3 bucket.
    
    Args:
        file_path (str): Path to local file
        s3_key (str): S3 object key
        bucket_name (str): S3 bucket name
    """
    try:
        logger.info(f"Uploading {file_path} to S3 bucket {bucket_name} with key {s3_key}")
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            endpoint_url=os.getenv('AWS_S3_ENDPOINT')  # For non-AWS S3-compatible storage
        )
        
        # Upload file
        s3_client.upload_file(file_path, bucket_name, s3_key)
        
        logger.info(f"Successfully uploaded to S3: s3://{bucket_name}/{s3_key}")
        return True
        
    except ClientError as e:
        logger.error(f"S3 upload error: {str(e)}")
        raise


def cleanup_old_backups(backup_type, retention_days):
    """
    Delete local backup files older than retention_days.
    
    Args:
        backup_type (str): Type of backup ('postgres', 'weaviate', 'media')
        retention_days (int): Number of days to keep backups
    """
    try:
        backup_dir = BACKUP_PATHS.get(backup_type)
        if not backup_dir or not os.path.exists(backup_dir):
            logger.warning(f"Backup directory not found for {backup_type}")
            return
        
        logger.info(f"Cleaning up old {backup_type} backups, keeping {retention_days} days")
        
        import time
        current_time = time.time()
        max_age = retention_days * 86400  # days to seconds
        
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            
            # Skip directories in weaviate backup folder (they're actual backups)
            if backup_type == 'weaviate' and os.path.isdir(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > max_age:
                    logger.info(f"Removing old backup directory: {file_path}")
                    shutil.rmtree(file_path)
            # Regular files for postgres and media backups
            elif os.path.isfile(file_path):
                file_age = current_time - os.path.getctime(file_path)
                if file_age > max_age:
                    logger.info(f"Removing old backup file: {file_path}")
                    os.remove(file_path)
        
        logger.info(f"Cleanup of old {backup_type} backups completed")
        
    except Exception as e:
        logger.error(f"Error during cleanup of old {backup_type} backups: {str(e)}")


@shared_task
def run_full_backup():
    """
    Run a full backup of all systems.
    """
    logger.info("Starting full system backup")
    
    # Run all backup tasks
    postgres_result = backup_postgres_database.delay()
    weaviate_result = backup_weaviate_database.delay()
    media_result = backup_media_files.delay()
    
    logger.info(f"Backup tasks initiated: postgres ({postgres_result.id}), weaviate ({weaviate_result.id}), media ({media_result.id})")
    
    return {
        'status': 'initiated',
        'task_ids': {
            'postgres': postgres_result.id,
            'weaviate': weaviate_result.id,
            'media': media_result.id
        }
    }