#!/bin/bash
# ARDT FMS Backup Script
# Creates a timestamped backup of database and fixtures

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups"

echo "🔄 Starting ARDT FMS Backup..."
echo ""
read -p "📝 Enter description (optional, press Enter to skip): " DESCRIPTION

# Clean description: replace spaces with underscores, remove special chars
if [ -n "$DESCRIPTION" ]; then
    CLEAN_DESC=$(echo "$DESCRIPTION" | tr ' ' '_' | tr -cd '[:alnum:]_-')
    BACKUP_NAME="ardt_backup_${TIMESTAMP}_${CLEAN_DESC}"
else
    BACKUP_NAME="ardt_backup_${TIMESTAMP}"
fi

echo ""
echo "📁 Backup name: ${BACKUP_NAME}"

# Create backup directory if not exists
mkdir -p ${BACKUP_DIR}

# Dump database data to JSON
echo "📦 Exporting database..."
python manage.py dumpdata --indent 2 \
    --exclude auth.permission \
    --exclude contenttypes \
    --exclude admin.logentry \
    --exclude sessions.session \
    > ${BACKUP_DIR}/${BACKUP_NAME}_data.json

# Copy database file
if [ -f "db.sqlite3" ]; then
    echo "💾 Copying database file..."
    cp db.sqlite3 ${BACKUP_DIR}/${BACKUP_NAME}_db.sqlite3
fi

# Create ZIP archive
echo "🗜️ Creating ZIP archive..."
cd ${BACKUP_DIR}
zip -q ${BACKUP_NAME}.zip ${BACKUP_NAME}_data.json ${BACKUP_NAME}_db.sqlite3 2>/dev/null
rm -f ${BACKUP_NAME}_data.json ${BACKUP_NAME}_db.sqlite3 2>/dev/null
cd ..

echo ""
echo "✅ Backup complete: ${BACKUP_DIR}/${BACKUP_NAME}.zip"
echo ""
ls -lh ${BACKUP_DIR}/${BACKUP_NAME}.zip
