# 🚀 Деплой на VPS

Пошаговая инструкция по развёртыванию бота на VPS сервере.

## 📋 Требования

- VPS с Ubuntu 20.04+ (или другой Linux дистрибутив)
- Доступ по SSH
- Python 3.11+ на сервере
- Git установлен

## 🔧 Подготовка сервера

### 1. Подключись к серверу

```bash
ssh user@your-server-ip
```

### 2. Обнови систему

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Установи Python и необходимые пакеты

```bash
sudo apt install -y python3.11 python3.11-venv python3-pip git
```

### 4. Установи uv (опционально, но рекомендуется)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

## 📦 Развёртывание бота

### Вариант 1: Простое развёртывание (рекомендуется для начала)

1. **Создай директорию для бота:**

```bash
mkdir -p ~/bots/learning_en_bot
cd ~/bots/learning_en_bot
```

2. **Клонируй репозиторий:**

```bash
git clone <your-repo-url> .
```

3. **Создай виртуальное окружение:**

```bash
python3.11 -m venv venv
source venv/bin/activate
```

4. **Установи зависимости:**

```bash
pip install -e .
# или с uv:
# uv sync
```

5. **Создай `.env` файл:**

```bash
nano .env
```

Добавь:
```env
TELEGRAM_TOKEN=твой_токен_от_BotFather
DATABASE_PATH=./data/bot.db
BOT_USERNAME=learning_en_bot
LOG_LEVEL=INFO
TIMEZONE=Europe/Moscow
```

Сохрани: `Ctrl+O`, `Enter`, `Ctrl+X`

6. **Создай директорию для данных:**

```bash
mkdir -p data
```

7. **Протестируй запуск:**

```bash
python -m src.learning_en_bot.main
```

Если всё работает, останови (Ctrl+C) и переходи к следующему шагу.

### Вариант 2: С systemd (для автозапуска)

1. **Выполни шаги 1-6 из Варианта 1**

2. **Создай systemd сервис:**

```bash
sudo nano /etc/systemd/system/learning-en-bot.service
```

Добавь:
```ini
[Unit]
Description=Learning English Bot
After=network.target

[Service]
Type=simple
User=твой_username
WorkingDirectory=/home/твой_username/bots/learning_en_bot
Environment="PATH=/home/твой_username/bots/learning_en_bot/venv/bin"
ExecStart=/home/твой_username/bots/learning_en_bot/venv/bin/python -m src.learning_en_bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Важно:** Замени `твой_username` на свой username и пути при необходимости.

3. **Перезагрузи systemd:**

```bash
sudo systemctl daemon-reload
```

4. **Включи автозапуск:**

```bash
sudo systemctl enable learning-en-bot
```

5. **Запусти бота:**

```bash
sudo systemctl start learning-en-bot
```

6. **Проверь статус:**

```bash
sudo systemctl status learning-en-bot
```

7. **Смотри логи:**

```bash
# Последние 50 строк
sudo journalctl -u learning-en-bot -n 50

# В реальном времени
sudo journalctl -u learning-en-bot -f
```

## 🔄 Обновление бота

### Ручное обновление

```bash
cd ~/bots/learning_en_bot
git pull
source venv/bin/activate  # если используешь venv
pip install -e .  # обновить зависимости при необходимости

# Если используешь systemd
sudo systemctl restart learning-en-bot
```

### Автоматическое обновление (смотри CI/CD ниже)

## 🔒 Безопасность

1. **Не коммить `.env` файл** (уже в `.gitignore`)

2. **Настрой firewall:**

```bash
sudo ufw allow 22/tcp   # SSH
sudo ufw enable
```

3. **Используй сильные пароли** для пользователя

4. **Регулярно обновляй систему:**

```bash
sudo apt update && sudo apt upgrade -y
```

## 📊 Мониторинг

### Проверка работы бота

```bash
# Если используешь systemd
sudo systemctl status learning-en-bot

# Логи
sudo journalctl -u learning-en-bot -n 100
```

### Проверка использования ресурсов

```bash
# Процессы
ps aux | grep python

# Память и CPU
htop
# или
top
```

## 🐛 Решение проблем

### Бот не запускается

1. Проверь логи: `sudo journalctl -u learning-en-bot -n 100`
2. Проверь `.env` файл
3. Проверь права доступа: `ls -la ~/bots/learning_en_bot`
4. Проверь Python версию: `python3.11 --version`

### Бот упал

```bash
# Перезапусти
sudo systemctl restart learning-en-bot

# Проверь почему упал
sudo journalctl -u learning-en-bot -n 100 --no-pager
```

### Проблемы с базой данных

```bash
# Проверь права доступа
ls -la ~/bots/learning_en_bot/data/

# Если нужно, исправь
chmod 755 ~/bots/learning_en_bot/data/
chmod 644 ~/bots/learning_en_bot/data/*.db
```

## 🚀 Быстрый скрипт установки

Сохрани в `setup.sh`:

```bash
#!/bin/bash
set -e

BOT_DIR="$HOME/bots/learning_en_bot"
REPO_URL="your-repo-url"  # Замени на свой URL

echo "🚀 Установка Learning English Bot..."

# Создаём директорию
mkdir -p "$BOT_DIR"
cd "$BOT_DIR"

# Клонируем репозиторий
if [ ! -d ".git" ]; then
    git clone "$REPO_URL" .
fi

# Создаём venv
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi

# Активируем venv
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -e .

# Создаём директорию для данных
mkdir -p data

# Создаём .env если его нет
if [ ! -f ".env" ]; then
    echo "⚠️  Создай .env файл с TELEGRAM_TOKEN!"
    echo "Пример:"
    echo "TELEGRAM_TOKEN=your_token_here"
    echo "DATABASE_PATH=./data/bot.db"
fi

echo "✅ Установка завершена!"
echo "📝 Не забудь создать .env файл с TELEGRAM_TOKEN"
echo "🚀 Запуск: cd $BOT_DIR && source venv/bin/activate && python -m src.learning_en_bot.main"
```

Использование:
```bash
chmod +x setup.sh
./setup.sh
```
