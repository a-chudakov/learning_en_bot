FROM python:3.11-slim

WORKDIR /app

# Копируем файлы проекта
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/

# Устанавливаем uv и зависимости
RUN pip install uv && \
    uv sync --frozen --no-dev && \
    rm -rf /root/.cache

# Создаём директорию для данных
RUN mkdir -p /app/data

# Запуск
CMD ["python", "-m", "src.learning_en_bot.main"]
