#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/jobpilot_${TIMESTAMP}.sql.gz"
RETENTION_DAYS=30

echo "=== JobPilot Database Backup ==="
echo "Timestamp: ${TIMESTAMP}"

# Create backup directory if not exists
mkdir -p ${BACKUP_DIR}

# Run pg_dump inside the postgres container
echo "Creating backup..."
docker compose exec -T postgres pg_dump \
    -U ${POSTGRES_USER:-jobpilot} \
    -d ${POSTGRES_DB:-jobpilot_db} \
    --format=custom \
    --compress=9 \
    > "${BACKUP_FILE}"

# Check if backup was successful
if [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "Backup created: ${BACKUP_FILE} (${SIZE})"
else
    echo "ERROR: Backup failed!"
    exit 1
fi

# Remove old backups
echo "Removing backups older than ${RETENTION_DAYS} days..."
find ${BACKUP_DIR} -name "jobpilot_*.sql.gz" -mtime +${RETENTION_DAYS} -delete

echo "=== Backup Complete ==="
