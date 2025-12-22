#!/bin/bash
set -e

echo "Ожидание готовности базы данных..."
until python manage.py check --database default 2>/dev/null; do
  echo "База данных недоступна - ожидание..."
  sleep 2
done

echo "Выполнение миграций..."
python manage.py migrate --noinput

echo "Сборка статических файлов..."
python manage.py collectstatic --noinput || true

echo "Проверка наличия суперпользователя..."
python << PYEOF
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hikvision_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    print("Создание суперпользователя admin/admin123...")
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Суперпользователь создан!")
else:
    print("Суперпользователь уже существует.")
PYEOF

echo "Запуск сервера..."
exec "$@"

