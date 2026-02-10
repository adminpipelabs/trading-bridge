# Phase 2 Task 1: Database Backups - Implementation Guide

## ✅ What Was Created

1. **`scripts/backup.sh`** - Simple bash script for pg_dump backups
2. **`scripts/backup_to_s3.py`** - Python script for S3 backups (production grade)

## 📋 Implementation Options

### Option A: Railway Automated Backups (Easiest - Recommended)

If using Railway's PostgreSQL:

1. Go to Railway Dashboard
2. Click on PostgreSQL service
3. Settings → Backups
4. Enable "Automatic Backups"
5. Set retention period (7-30 days)

**Cost:** Included in Railway Pro plan, or ~$5/month extra

### Option B: Manual pg_dump Script (Free)

**Setup:**

1. **Add to Railway as scheduled job:**
   - Create new Railway service from same repo
   - Set start command: `./scripts/backup.sh`
   - Add cron schedule: `0 2 * * *` (2am UTC daily)
   - Set environment variables:
     - `DATABASE_URL` (from PostgreSQL service)
     - `BACKUP_DIR=/backups` (optional)
     - `RETENTION_DAYS=7` (optional)

2. **Or run manually:**
   ```bash
   export DATABASE_URL="your_database_url"
   ./scripts/backup.sh
   ```

**Storage:** Backups stored in `/backups` directory (need persistent volume)

### Option C: Backup to S3 (Production Grade)

**Setup:**

1. **Install boto3:**
   ```bash
   pip install boto3
   ```
   (Already added to requirements.txt)

2. **Create S3 bucket:**
   - AWS Console → S3 → Create bucket
   - Name: `pipelabs-backups`
   - Region: `us-east-1` (or your preference)

3. **Create IAM user with S3 permissions:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::pipelabs-backups/*",
           "arn:aws:s3:::pipelabs-backups"
         ]
       }
     ]
   }
   ```

4. **Add to Railway as scheduled job:**
   - Create new Railway service
   - Set start command: `python scripts/backup_to_s3.py`
   - Add cron schedule: `0 2 * * *` (2am UTC daily)
   - Set environment variables:
     - `DATABASE_URL` (from PostgreSQL service)
     - `BACKUP_S3_BUCKET=pipelabs-backups`
     - `AWS_ACCESS_KEY_ID=xxx`
     - `AWS_SECRET_ACCESS_KEY=xxx`
     - `AWS_DEFAULT_REGION=us-east-1`
     - `RETENTION_DAYS=30` (optional)

## 🧪 Testing

### Test backup script:
```bash
cd /Users/mikaelo/trading-bridge
export DATABASE_URL="your_database_url"
./scripts/backup.sh
```

### Test S3 backup:
```bash
export DATABASE_URL="your_database_url"
export BACKUP_S3_BUCKET="pipelabs-backups"
export AWS_ACCESS_KEY_ID="xxx"
export AWS_SECRET_ACCESS_KEY="xxx"
python scripts/backup_to_s3.py
```

## 🔄 Restore Procedure

### From local backup:
```bash
gunzip pipelabs_20260129_020000.sql.gz
psql $DATABASE_URL < pipelabs_20260129_020000.sql
```

### From S3:
```bash
# Download from S3
aws s3 cp s3://pipelabs-backups/database/pipelabs_20260129_020000.sql.gz ./

# Restore
gunzip pipelabs_20260129_020000.sql.gz
psql $DATABASE_URL < pipelabs_20260129_020000.sql
```

## ✅ Success Criteria

- [ ] Daily backups running (verified in S3/storage)
- [ ] Can restore from backup in <30 minutes
- [ ] Old backups cleaned up automatically
- [ ] Alerts if backup fails (add to monitoring)

## 📝 Next Steps

1. Choose backup option (A, B, or C)
2. Set up Railway scheduled job or cron
3. Test backup manually
4. Verify restore procedure
5. Monitor first few backups
