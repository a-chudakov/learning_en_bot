#!/bin/bash
# Скрипт автоматического резервного копирования базы данных бота

set -e  # Остановить при ошибке

# Путь к директории бота (измени если нужно)
BOT_DIR="${BOT_DIR:-$HOME/learning_en_bot}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/learning_en_bot}"

# Создаём директорию для бэкапов если её нет
mkdir -p "$BACKUP_DIR"

# Проверяем наличие базы данных
if [ ! -f "$BOT_DIR/data/bot.db" ]; then
    echo "$(date): ERROR - Database file not found: $BOT_DIR/data/bot.db" >> "$BACKUP_DIR/backup.log"
    exit 1
fi

# Делаем бэкап с временной меткой
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bot_${TIMESTAMP}.db"

cp "$BOT_DIR/data/bot.db" "$BACKUP_FILE"

# Проверяем что бэкап создался
if [ -f "$BACKUP_FILE" ]; then
    echo "$(date): ✅ Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))" >> "$BACKUP_DIR/backup.log"
else
    echo "$(date): ❌ ERROR - Backup failed" >> "$BACKUP_DIR/backup.log"
    exit 1
fi

# Удаляем старые бэкапы (старше 30 дней)
DELETED=$(find "$BACKUP_DIR" -name "bot_*.db" -mtime +30 -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "$(date): 🗑️  Deleted $DELETED old backup(s)" >> "$BACKUP_DIR/backup.log"
fi

exit 0
