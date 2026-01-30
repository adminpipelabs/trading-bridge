#!/usr/bin/env python3
"""
backup_to_s3.py - Database backup script with S3 upload
Run daily via cron or Railway scheduled job

Environment Variables Required:
- DATABASE_URL: PostgreSQL connection string
- BACKUP_S3_BUCKET: S3 bucket name (default: pipelabs-backups)
- AWS_ACCESS_KEY_ID: AWS access key
- AWS_SECRET_ACCESS_KEY: AWS secret key
- AWS_DEFAULT_REGION: AWS region (default: us-east-1)
- RETENTION_DAYS: Days to keep backups (default: 30)
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import boto3
except ImportError:
    print("❌ ERROR: boto3 not installed. Run: pip install boto3")
    sys.exit(1)

# Configuration
S3_BUCKET = os.environ.get("BACKUP_S3_BUCKET", "pipelabs-backups")
S3_PREFIX = "database/"
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))
DATABASE_URL = os.environ.get("DATABASE_URL")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

def create_backup():
    """Create database backup and upload to S3."""
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"pipelabs_{timestamp}.sql.gz"
    local_path = f"/tmp/{filename}"
    
    print(f"📦 Creating backup: {filename}")
    print(f"   Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else '***'}")
    
    # Run pg_dump
    try:
        result = subprocess.run(
            f"pg_dump '{DATABASE_URL}' | gzip > {local_path}",
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ pg_dump failed: {e.stderr}")
        sys.exit(1)
    
    # Check if file was created
    if not os.path.exists(local_path):
        print("❌ Backup file was not created")
        sys.exit(1)
    
    # Get file size
    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    print(f"✅ Backup created: {size_mb:.2f} MB")
    
    # Upload to S3
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            region_name=AWS_REGION
        )
        
        s3_key = f"{S3_PREFIX}{filename}"
        print(f"☁️  Uploading to s3://{S3_BUCKET}/{s3_key}")
        
        s3.upload_file(local_path, S3_BUCKET, s3_key)
        print("✅ Upload complete")
        
        # Cleanup local file
        os.remove(local_path)
        
        # Delete old backups
        cleanup_old_backups(s3)
        
        return s3_key
        
    except Exception as e:
        print(f"❌ S3 upload failed: {e}")
        # Keep local file for manual recovery
        print(f"⚠️  Local backup kept at: {local_path}")
        sys.exit(1)

def cleanup_old_backups(s3):
    """Delete backups older than RETENTION_DAYS."""
    print(f"🧹 Cleaning up backups older than {RETENTION_DAYS} days")
    
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    deleted_count = 0
    
    try:
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=S3_PREFIX)
        
        for page in pages:
            for obj in page.get("Contents", []):
                if obj["LastModified"].replace(tzinfo=None) < cutoff:
                    print(f"  Deleting: {obj['Key']}")
                    s3.delete_object(Bucket=S3_BUCKET, Key=obj["Key"])
                    deleted_count += 1
        
        print(f"✅ Cleanup complete: {deleted_count} old backup(s) deleted")
        
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

if __name__ == "__main__":
    create_backup()
