#!/bin/bash
# ARDT FMS Backup Script

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups"

echo "🔄 ARDT FMS Backup"
echo "=================="
echo ""
echo "What to backup?"
echo "  1) Full project (code + database) - recommended"
echo "  2) Database only (test data)"
echo ""
read -e -p "Choice [1]: " BACKUP_TYPE
BACKUP_TYPE=${BACKUP_TYPE:-1}

echo ""
read -e -p "📝 Description (optional): " DESCRIPTION

# Clean description
if [ -n "$DESCRIPTION" ]; then
    CLEAN_DESC=$(echo "$DESCRIPTION" | tr ' ' '_' | tr -cd '[:alnum:]_-')
    BACKUP_NAME="ardt_backup_${TIMESTAMP}_${CLEAN_DESC}"
else
    BACKUP_NAME="ardt_backup_${TIMESTAMP}"
fi

mkdir -p ${BACKUP_DIR}

if [ "$BACKUP_TYPE" = "2" ]; then
    # Database only backup
    echo ""
    echo "📦 Exporting database..."
    python manage.py dumpdata --indent 2 \
        --exclude auth.permission \
        --exclude contenttypes \
        --exclude admin.logentry \
        --exclude sessions.session \
        > ${BACKUP_DIR}/${BACKUP_NAME}_data.json

    if [ -f "db.sqlite3" ]; then
        cp db.sqlite3 ${BACKUP_DIR}/${BACKUP_NAME}_db.sqlite3
    fi

    cd ${BACKUP_DIR}
    zip -q ${BACKUP_NAME}.zip ${BACKUP_NAME}_data.json ${BACKUP_NAME}_db.sqlite3 2>/dev/null
    rm -f ${BACKUP_NAME}_data.json ${BACKUP_NAME}_db.sqlite3 2>/dev/null
    cd ..
else
    # Full project backup (default)
    echo ""
    echo "📦 Creating full project backup from: $(pwd)"
    zip -rq ${BACKUP_DIR}/${BACKUP_NAME}.zip \
        . \
        -x "*.pyc" -x "*__pycache__*" -x ".git/*" -x "backups/*" -x "*.zip" -x "node_modules/*" -x "venv/*" -x ".venv/*" 2>/dev/null
fi

echo ""
echo "✅ Backup complete!"
ls -lh ${BACKUP_DIR}/${BACKUP_NAME}.zip
