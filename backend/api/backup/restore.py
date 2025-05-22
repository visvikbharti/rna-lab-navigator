"""
Restore utilities for RNA Lab Navigator backups.
Contains functions for restoring from backups.
"""

import os
import subprocess
import shutil
import logging
import tempfile
import requests
from django.conf import settings
import boto3
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger(__name__)


def restore_postgres_from_backup(backup_path, database_name=None):
    """
    Restore PostgreSQL database from a backup file.
    
    Args:
        backup_path (str): Path to the backup file
        database_name (str, optional): Database name to restore to, defaults to settings.DATABASES['default']['NAME']
    
    Returns:
        dict: Result information
    """
    try:
        # Get database settings
        db_settings = settings.DATABASES['default']
        db_name = database_name or db_settings['NAME']
        
        logger.info(f"Starting PostgreSQL restore to database {db_name} from {backup_path}")
        
        # Set environment variables for pg_restore
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings['PASSWORD']
        
        # First, drop and recreate the database
        drop_cmd = [
            'dropdb',
            '--host', db_settings['HOST'],
            '--port', db_settings['PORT'],
            '--username', db_settings['USER'],
            '--if-exists',
            db_name
        ]
        
        create_cmd = [
            'createdb',
            '--host', db_settings['HOST'],
            '--port', db_settings['PORT'],
            '--username', db_settings['USER'],
            db_name
        ]
        
        # Then restore from backup
        restore_cmd = [
            'pg_restore',
            '--host', db_settings['HOST'],
            '--port', db_settings['PORT'],
            '--username', db_settings['USER'],
            '--dbname', db_name,
            '--no-owner',
            '--no-privileges',
            backup_path
        ]
        
        # Execute drop command
        logger.info("Dropping existing database...")
        process = subprocess.Popen(drop_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.warning(f"Warning while dropping database: {stderr.decode('utf-8')}")
        
        # Execute create command
        logger.info("Creating new database...")
        process = subprocess.Popen(create_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8')
            logger.error(f"Error creating database: {error_msg}")
            raise Exception(f"createdb failed: {error_msg}")
        
        # Execute restore command
        logger.info("Restoring from backup...")
        process = subprocess.Popen(restore_cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8')
            logger.error(f"Error during restore: {error_msg}")
            # Check if there are just some warnings but restore was successful
            if "ERROR:" in error_msg:
                raise Exception(f"pg_restore failed: {error_msg}")
            else:
                logger.warning(f"pg_restore completed with warnings: {error_msg}")
        
        logger.info(f"PostgreSQL database restore completed successfully")
        
        return {
            'status': 'success',
            'database': db_name,
            'backup_file': backup_path
        }
        
    except Exception as e:
        logger.error(f"Error during PostgreSQL restore: {str(e)}")
        raise


def restore_weaviate_from_backup(backup_name, backup_path=None):
    """
    Restore Weaviate vector database from a backup.
    
    Args:
        backup_name (str): Name of the backup
        backup_path (str, optional): Path to backup directory for filesystem backend
    
    Returns:
        dict: Result information
    """
    try:
        logger.info(f"Starting Weaviate restore from backup: {backup_name}")
        
        # Determine if we're using local or S3 backup
        if hasattr(settings, 'AWS_BACKUP_BUCKET') and settings.AWS_BACKUP_BUCKET:
            backend = "s3"
            backup_location = f"s3://{settings.AWS_BACKUP_BUCKET}/weaviate/{backup_name}"
        else:
            backend = "filesystem"
            backup_location = backup_path or os.path.join(settings.BASE_DIR, 'backups', 'weaviate', backup_name)
        
        # Call Weaviate API to restore backup
        weaviate_url = settings.WEAVIATE_URL.rstrip('/')
        restore_endpoint = f"{weaviate_url}/v1/backups/{backup_name}/restore"
        
        # Restore request payload
        payload = {
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
                "path": backup_location
            }
        
        # Get authentication header if API key is configured
        headers = {"Content-Type": "application/json"}
        if settings.WEAVIATE_API_KEY:
            headers["Authorization"] = f"Bearer {settings.WEAVIATE_API_KEY}"
        
        # Create restore request
        response = requests.post(restore_endpoint, json=payload, headers=headers)
        
        if not response.ok:
            error_msg = f"Weaviate restore failed: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        logger.info(f"Weaviate restore initiated: {backup_name}")
        
        # Check restore status until complete or failed
        restore_status_endpoint = f"{weaviate_url}/v1/backups/{backup_name}/restore"
        
        # Poll for restore completion
        import time
        max_attempts = 60  # 60 attempts with 10 seconds between = 10 minutes max wait
        for attempt in range(max_attempts):
            status_response = requests.get(restore_status_endpoint, headers=headers)
            
            if not status_response.ok:
                logger.warning(f"Failed to get restore status: {status_response.status_code} - {status_response.text}")
                continue
            
            status_data = status_response.json()
            status = status_data.get("status", "")
            
            if status == "SUCCESS":
                logger.info(f"Weaviate restore completed successfully: {backup_name}")
                break
            elif status == "FAILED":
                error_msg = f"Weaviate restore failed: {status_data.get('error', 'Unknown error')}"
                logger.error(error_msg)
                raise Exception(error_msg)
            else:
                # Still in progress, wait and retry
                logger.info(f"Weaviate restore in progress: {status}")
                time.sleep(10)  # Wait 10 seconds before checking again
        else:
            # If we get here, we've exceeded max attempts
            logger.warning(f"Restore status check timed out after {max_attempts} attempts. Assuming it's still running in the background.")
        
        return {
            'status': 'success',
            'backup_name': backup_name,
            'backend': backend,
            'location': backup_location
        }
        
    except Exception as e:
        logger.error(f"Error during Weaviate restore: {str(e)}")
        raise


def restore_media_files(backup_path):
    """
    Restore media files from a backup archive.
    
    Args:
        backup_path (str): Path to the backup archive file
    
    Returns:
        dict: Result information
    """
    try:
        logger.info(f"Starting media files restore from {backup_path}")
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract archive
            shutil.unpack_archive(backup_path, temp_dir)
            
            # Determine extracted directory
            extracted_dir = os.path.join(temp_dir, os.listdir(temp_dir)[0])
            
            # Remove existing media directory
            media_dir = settings.MEDIA_ROOT
            if os.path.exists(media_dir):
                shutil.rmtree(media_dir)
            
            # Copy extracted files to media directory
            shutil.copytree(extracted_dir, media_dir)
            
            logger.info(f"Media files restored successfully to {media_dir}")
            
            return {
                'status': 'success',
                'backup_file': backup_path,
                'media_dir': media_dir
            }
        
    except Exception as e:
        logger.error(f"Error during media files restore: {str(e)}")
        raise