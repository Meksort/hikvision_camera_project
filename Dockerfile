FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование проекта
COPY . .

# Создание директории для статических файлов
RUN mkdir -p /app/staticfiles

# Настройка переменных окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Копирование скрипта запуска
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Порт для Django
EXPOSE 8000

# Entrypoint для выполнения миграций перед запуском
ENTRYPOINT ["/docker-entrypoint.sh"]

# Команда запуска (будет переопределена в docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

