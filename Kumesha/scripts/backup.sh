#!/bin/bash
# Automated backup script for Lost & Found system
# Run daily via cron: 0 2 * * * /path/to/backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
DB_FILE="data/validation.db"
MODELS_DIR="models"

# Create backup directory
mkdir -p $BACKUP_DIR

echo "Starting backup at $(date)"

# Backup SQLite database
if [ -f "$DB_FILE" ]; then
    echo "Backing up database..."
    cp $DB_FILE $BACKUP_DIR/validation_db_$DATE.db
    gzip $BACKUP_DIR/validation_db_$DATE.db
    echo "✓ Database backed up"
else
    echo "⚠ Database file not found"
fi

# Backup model files (if not using Git LFS)
if [ -d "$MODELS_DIR" ]; then
    echo "Backing up models..."
    tar -czf $BACKUP_DIR/models_$DATE.tar.gz $MODELS_DIR
    echo "✓ Models backed up"
fi

# Backup logs
if [ -d "logs" ]; then
    echo "Backing up logs..."
    tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs
    echo "✓ Logs backed up"
fi

# Keep only last 7 days of backups
echo "Cleaning old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.db" -mtime +7 -delete

echo "Backup completed at $(date)"
echo "Backup size: $(du -sh $BACKUP_DIR | cut -f1)"

# Optional: Upload to cloud storage
# aws s3 cp $BACKUP_DIR/ s3://your-bucket/backups/ --recursive
# rclone sync $BACKUP_DIR remote:backups
