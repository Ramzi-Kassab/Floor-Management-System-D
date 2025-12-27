#!/bin/bash
# ARDT FMS Restore Script
# Restores from the latest backup ZIP

BACKUP_DIR="backups"

echo "🔄 Starting ARDT FMS Restore..."

# Find latest backup
LATEST_ZIP=$(ls -t ${BACKUP_DIR}/ardt_backup_*.zip 2>/dev/null | head -1)

if [ -z "$LATEST_ZIP" ]; then
    echo "❌ No backup found in ${BACKUP_DIR}/"
    exit 1
fi

echo "📦 Found backup: ${LATEST_ZIP}"

# Extract to temp directory
TEMP_DIR=$(mktemp -d)
unzip -q ${LATEST_ZIP} -d ${TEMP_DIR}

# Check for database file
DB_FILE=$(ls ${TEMP_DIR}/*_db.sqlite3 2>/dev/null | head -1)
DATA_FILE=$(ls ${TEMP_DIR}/*_data.json 2>/dev/null | head -1)

if [ -f "$DB_FILE" ]; then
    echo "💾 Restoring database file..."
    cp ${DB_FILE} db.sqlite3
    echo "✅ Database restored from file"
elif [ -f "$DATA_FILE" ]; then
    echo "📦 Restoring from JSON fixture..."
    python manage.py loaddata ${DATA_FILE}
    echo "✅ Data restored from JSON"
else
    echo "❌ No database or data file found in backup"
    rm -rf ${TEMP_DIR}
    exit 1
fi

# Cleanup
rm -rf ${TEMP_DIR}

echo ""
echo "✅ Restore complete!"
echo ""
echo "Run: python manage.py runserver"
