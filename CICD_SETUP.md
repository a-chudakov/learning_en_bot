# ⚙️ Настройка CI/CD для автоматического деплоя

Простая настройка автоматического развёртывания через GitHub Actions (без Docker registry).

## 📋 Что нужно

1. GitHub репозиторий с кодом
2. VPS сервер с SSH доступом
3. SSH ключ для доступа к серверу

## 🔑 Настройка Secrets в GitHub

1. Перейди в свой репозиторий на GitHub
2. Открой **Settings** → **Secrets and variables** → **Actions**
3. Добавь следующие секреты:

| Secret | Описание | Пример |
|--------|----------|--------|
| `VPS_HOST` | IP адрес или домен VPS | `123.45.67.89` или `example.com` |
| `VPS_USERNAME` | Username для SSH | `ubuntu` или `root` |
| `VPS_SSH_KEY` | Приватный SSH ключ | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `VPS_PORT` | SSH порт (опционально) | `22` (по умолчанию) |
| `BOT_DIR` | Путь к директории бота на сервере | `~/bots/learning_en_bot` |

### Как получить SSH ключ

**Если у тебя уже есть SSH ключ на компьютере:**

```bash
cat ~/.ssh/id_rsa
# Или
cat ~/.ssh/id_ed25519
```

**Если нет, создай новый:**

```bash
ssh-keygen -t ed25519 -C "github-actions"
# Сохрани в ~/.ssh/github_actions

# Скопируй приватный ключ
cat ~/.ssh/github_actions

# Добавь публичный ключ на сервер
ssh-copy-id -i ~/.ssh/github_actions.pub user@your-server-ip
```

**Важно:** Добавь приватный ключ в `VPS_SSH_KEY` секрет в GitHub!

## 🚀 Настройка GitHub Actions

Файл `.github/workflows/deploy.yml` уже создан. Просто проверь:

1. **Измени ветку в workflow** (если нужно):

```yaml
on:
  push:
    branches:
      - main  # Твоя ветка
```

2. **Настрой пути в `script` секции** (если твой путь отличается):

```yaml
cd ${{ secrets.BOT_DIR || '~/bots/learning_en_bot' }}
```

## ✅ Проверка работы

1. **Запушь код в main ветку:**

```bash
git add .
git commit -m "Setup CI/CD"
git push origin main
```

2. **Проверь GitHub Actions:**

- Перейди в **Actions** вкладку в репозитории
- Увидишь запущенный workflow
- Если есть ошибки, посмотри логи

3. **Проверь деплой на сервере:**

```bash
ssh user@your-server
cd ~/bots/learning_en_bot
git log -1  # Проверь последний коммит
sudo systemctl status learning-en-bot  # Если используешь systemd
```

## 🔧 Альтернативный вариант (проще, без systemd)

Если не используешь systemd, можно использовать простой способ:

**Измени в `.github/workflows/deploy.yml` секцию `script`:**

```yaml
script: |
  cd ${{ secrets.BOT_DIR || '~/bots/learning_en_bot' }}
  
  git fetch origin
  git reset --hard origin/main
  
  if [ -d "venv" ]; then
    source venv/bin/activate
  fi
  
  pip install -e .
  
  # Убиваем старый процесс
  pkill -f "src.learning_en_bot.main" || true
  
  # Запускаем новый
  nohup python -m src.learning_en_bot.main > bot.log 2>&1 &
  
  echo "✅ Бот перезапущен"
```

## 🐛 Решение проблем

### Ошибка: "Permission denied (publickey)"

**Решение:**
1. Проверь, что `VPS_SSH_KEY` правильный (полный приватный ключ)
2. Убедись, что публичный ключ добавлен на сервер:
   ```bash
   ssh-copy-id -i ~/.ssh/your_key.pub user@server
   ```

### Ошибка: "Connection refused"

**Решение:**
1. Проверь `VPS_HOST` и `VPS_PORT`
2. Убедись, что SSH сервер работает:
   ```bash
   sudo systemctl status ssh
   ```

### Ошибка: "Command not found: git" или "python"

**Решение:**
Добавь путь к командам в `script`:
```yaml
script: |
  export PATH="$HOME/.local/bin:$PATH"
  # остальной код
```

### Бот не перезапускается

**Решение:**
Проверь логи на сервере:
```bash
ssh user@server
sudo journalctl -u learning-en-bot -n 50  # Если systemd
# или
tail -f ~/bots/learning_en_bot/bot.log  # Если nohup
```

## 📊 Что происходит при деплое

1. ✅ Код клонируется на GitHub Actions runner
2. ✅ Устанавливаются зависимости
3. ✅ (Опционально) Запускаются тесты
4. ✅ Код деплоится на VPS через SSH
5. ✅ Обновляется репозиторий на сервере
6. ✅ Обновляются зависимости
7. ✅ Бот перезапускается

## 💡 Дополнительные улучшения

### Уведомления в Telegram при деплое

Добавь в workflow после деплоя:

```yaml
- name: 📱 Notify Telegram
  uses: appleboy/telegram-action@v0.1.3
  with:
    to: ${{ secrets.TELEGRAM_CHAT_ID }}
    token: ${{ secrets.TELEGRAM_BOT_TOKEN }}
    message: |
      ✅ Деплой завершён!
      Ветка: ${{ github.ref }}
      Коммит: ${{ github.sha }}
```

### Деплой только на определённые теги

Измени trigger:

```yaml
on:
  push:
    tags:
      - 'v*'  # Например v1.0.0
```

### Деплой в разные окружения

Добавь несколько jobs:

```yaml
jobs:
  deploy-staging:
    # Деплой на staging сервер
  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    # Деплой на production
```

## ✅ Готово!

Теперь при каждом push в main ветку бот будет автоматически обновляться на VPS! 🚀
