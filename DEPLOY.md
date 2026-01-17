# 🚀 Развёртывание на VPS

Простая инструкция по развёртыванию бота на VPS сервере.

## 📋 Что нужно

- VPS сервер с Linux (Ubuntu/Debian)
- Docker и docker-compose (или просто Docker)
- Твой Telegram User ID

## 🔍 Как узнать свой Telegram User ID

1. Найди в Telegram [@userinfobot](https://t.me/userinfobot)
2. Отправь `/start`
3. Бот покажет твой ID (например: `155760922`)
4. Скопируй этот номер - он нужен для приватного доступа

## 🚀 Вариант 1: С Docker (рекомендуется)

### 1. Подключись к серверу

```bash
ssh user@your-server-ip
```

### 2. Установи Docker (если нет)

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Выйди и зайди снова чтобы применились изменения группы
```

### 3. Установи docker-compose (если нет)

```bash
sudo apt install docker-compose -y
```

### 4. Клонируй репозиторий

```bash
cd ~
git clone <your-repo-url> learning_en_bot
cd learning_en_bot
```

### 5. Создай `.env` файл

```bash
nano .env
```

Добавь:
```env
TELEGRAM_TOKEN=твой_токен_от_BotFather
ALLOWED_USER_ID=твой_telegram_id
```

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`

### 6. Запусти бота

```bash
docker-compose up -d
```

### 7. Проверь работу

```bash
# Смотри логи
docker-compose logs -f

# Проверь статус
docker-compose ps
```

**Готово!** Бот работает и доступен только тебе. 🎉

### Управление

```bash
# Остановить
docker-compose down

# Перезапустить
docker-compose restart

# Обновить (после git pull)
docker-compose down
docker-compose up -d --build
```

---

## 🔧 Вариант 2: Без Docker (проще, но менее удобно)

### 1. Подключись к серверу

```bash
ssh user@your-server-ip
```

### 2. Установи Python

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git
```

### 3. Клонируй репозиторий

```bash
cd ~
git clone <your-repo-url> learning_en_bot
cd learning_en_bot
```

### 4. Установи зависимости

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
```

### 5. Создай `.env` файл

```bash
cat > .env << EOF
TELEGRAM_TOKEN=твой_токен_от_BotFather
ALLOWED_USER_ID=твой_telegram_id
EOF
```

### 6. Запусти в screen

```bash
screen -S bot
source venv/bin/activate
python -m src.learning_en_bot.main
# Ctrl+A, затем D для выхода из screen
```

### 7. Вернуться к боту

```bash
screen -r bot
```

---

## 🔒 Приватность бота

Бот автоматически проверяет `ALLOWED_USER_ID` из `.env`. Если указан:

- ✅ Только ты можешь использовать бота
- ❌ Другие получат сообщение "Доступ запрещён"

**Чтобы сделать бота публичным:** Просто не указывай `ALLOWED_USER_ID` в `.env`

---

## 📊 Мониторинг

### С Docker

```bash
# Логи в реальном времени
docker-compose logs -f bot

# Последние 50 строк
docker-compose logs --tail=50 bot
```

### Без Docker

```bash
# Если используешь screen
screen -r bot

# Если используешь systemd
sudo journalctl -u learning-en-bot -f
```

---

## 🔄 Обновление бота

### С Docker

```bash
cd ~/learning_en_bot
git pull
docker-compose down
docker-compose up -d --build
```

### Без Docker

```bash
cd ~/learning_en_bot
git pull
screen -r bot
# Ctrl+C чтобы остановить
# Затем запусти заново
source venv/bin/activate
python -m src.learning_en_bot.main
```

---

## 🐛 Решение проблем

### Бот не отвечает

```bash
# Проверь логи
docker-compose logs bot

# Проверь .env
cat .env

# Проверь, что бот запущен
docker-compose ps
```

### Ошибка доступа

- Проверь, что `ALLOWED_USER_ID` правильный (твой Telegram ID)
- Убедись, что используешь правильного бота

### Бот упал

```bash
# С Docker - просто перезапусти
docker-compose restart

# Без Docker - зайди в screen и перезапусти
screen -r bot
```

---

## 💾 Резервное копирование

База данных хранится в `./data/bot.db` (на хосте, пробрасывается в контейнер через volume).

Для резервного копирования просто скопируй файл:

```bash
# С Docker (файл хранится на хосте в ./data/)
cd ~/learning_en_bot
cp data/bot.db backup_$(date +%Y%m%d).db

# Или если хочешь сохранить в другое место
cp data/bot.db ~/backups/bot_$(date +%Y%m%d).db
```

**Восстановление:**

```bash
# Останови бота
docker-compose down

# Восстанови базу
cp ~/backups/bot_20240117.db data/bot.db

# Запусти заново
docker-compose up -d
```

---

## ⏰ Автоматическое резервное копирование (cron)

### 1. Создай директорию для бэкапов

```bash
mkdir -p ~/backups/learning_en_bot
```

### 2. Скопируй готовый скрипт

В репозитории есть готовый скрипт `scripts/backup_bot.sh`:

```bash
# Скопируй скрипт из репозитория
cp ~/learning_en_bot/scripts/backup_bot.sh ~/backups/backup_bot.sh

# Или создай сам
nano ~/backups/backup_bot.sh
```

**Готовый скрипт** (содержимое `scripts/backup_bot.sh`):

```bash
#!/bin/bash
set -e

BOT_DIR="${BOT_DIR:-$HOME/learning_en_bot}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/learning_en_bot}"

mkdir -p "$BACKUP_DIR"

if [ ! -f "$BOT_DIR/data/bot.db" ]; then
    echo "$(date): ERROR - Database not found" >> "$BACKUP_DIR/backup.log"
    exit 1
fi

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bot_${TIMESTAMP}.db"
cp "$BOT_DIR/data/bot.db" "$BACKUP_FILE"

echo "$(date): ✅ Backup: $BACKUP_FILE" >> "$BACKUP_DIR/backup.log"

# Удаляем старые бэкапы (старше 30 дней)
find "$BACKUP_DIR" -name "bot_*.db" -mtime +30 -delete
```

### 3. Сделай скрипт исполняемым

```bash
chmod +x ~/backups/backup_bot.sh
```

### 4. Добавь в crontab

```bash
crontab -e
```

Добавь строку (бэкап каждый день в 3:00 ночи):

```cron
0 3 * * * /home/твой_username/backups/backup_bot.sh
```

**Другие варианты расписания:**

```cron
# Каждый день в 3:00
0 3 * * * /home/username/backups/backup_bot.sh

# Каждые 6 часов
0 */6 * * * /home/username/backups/backup_bot.sh

# Каждую неделю в воскресенье в 2:00
0 2 * * 0 /home/username/backups/backup_bot.sh

# Два раза в день (3:00 и 15:00)
0 3,15 * * * /home/username/backups/backup_bot.sh
```

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`

### 5. Проверь работу

```bash
# Запусти вручную
~/backups/backup_bot.sh

# Проверь что бэкап создался
ls -lh ~/backups/learning_en_bot/

# Проверь логи
tail ~/backups/learning_en_bot/backup.log
```

### 6. Просмотр текущих cron задач

```bash
crontab -l
```

---

**Готово!** Бэкапы будут создаваться автоматически по расписанию. ✅

---

**Готово!** Теперь бот работает
