# Запуск проекта в Docker

## Требования

- Docker Desktop установлен и запущен
- Docker Compose (входит в Docker Desktop)

## Быстрый старт

### 1. Запуск через bat файл (Windows):

```bash
docker-start.bat
```

### 2. Или вручную через командную строку:

```bash
docker-compose up --build -d
```

## Что происходит при запуске

1. **Сборка образа Django** - создается Docker образ с Python и зависимостями
2. **Запуск PostgreSQL** - база данных в отдельном контейнере
3. **Автоматические миграции** - при первом запуске создаются таблицы БД
4. **Создание суперпользователя** - автоматически создается admin/admin123 (если не существует)
5. **Запуск Django** - веб-сервер на порту 8000

## Доступ к приложению

После запуска проект доступен по адресам:

- **Локально:** http://localhost:8000/
- **Из сети:** http://192.168.1.129:8000/

### Основные страницы:
- Главная: http://192.168.1.129:8000/
- Админка: http://192.168.1.129:8000/admin/ (admin/admin123)
- Отчеты: http://192.168.1.129:8000/report/
- Статистика: http://192.168.1.129:8000/attendance-stats/

### API:
- События камер: http://192.168.1.129:8000/api/camera-events/
- Входы/выходы: http://192.168.1.129:8000/api/entries-exits/
- Статистика: http://192.168.1.129:8000/api/attendance-stats/

## Управление контейнерами

### Просмотр логов:
```bash
docker-compose logs -f
```

### Просмотр логов только веб-сервера:
```bash
docker-compose logs -f web
```

### Остановка:
```bash
docker-compose down
```

Или через bat файл:
```bash
docker-stop.bat
```

### Перезапуск:
```bash
docker-compose restart
```

### Пересборка после изменений:
```bash
docker-compose up --build -d
```

## Выполнение команд Django

### Миграции:
```bash
docker-compose exec web python manage.py migrate
```

### Создание суперпользователя:
```bash
docker-compose exec web python manage.py createsuperuser
```

### Пересчет статистики:
```bash
docker-compose exec web python recalculate_attendance_stats.py
```

### Django shell:
```bash
docker-compose exec web python manage.py shell
```

## Переменные окружения

Создайте файл `.env` в корне проекта для настройки:

```env
DB_NAME=hikvision_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=*
```

## Структура Docker

```
hikvision_camera_project/
├── Dockerfile              # Образ Django приложения
├── docker-compose.yml      # Конфигурация контейнеров
├── .dockerignore          # Исключения при сборке
├── docker-start.bat       # Скрипт запуска (Windows)
└── docker-stop.bat        # Скрипт остановки (Windows)
```

## Порты

- **8000** - Django веб-сервер
- **5432** - PostgreSQL (доступен только внутри Docker сети)

## Volumes (тома данных)

- `postgres_data` - данные PostgreSQL (сохраняются между перезапусками)
- `static_volume` - статические файлы Django

## Решение проблем

### Проблема: Порт 8000 уже занят

Измените порт в `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Внешний порт:Внутренний порт
```

### Проблема: База данных не подключается

Проверьте логи:
```bash
docker-compose logs db
```

Убедитесь, что контейнер БД запущен:
```bash
docker-compose ps
```

### Проблема: Изменения в коде не применяются

Пересоберите образ:
```bash
docker-compose up --build -d
```

### Проблема: Нужно очистить все данные

**ВНИМАНИЕ:** Это удалит все данные из базы!

```bash
docker-compose down -v
docker-compose up --build -d
```

## Отличие от локального запуска

- База данных работает в отдельном контейнере
- Все зависимости изолированы в контейнере
- Не нужно устанавливать Python и PostgreSQL локально
- Легко развернуть на любом сервере с Docker

## Production

Для production используйте:
- Nginx как reverse proxy
- Gunicorn вместо runserver
- SSL сертификаты
- Правильные настройки безопасности

Пример команды для production:
```yaml
command: gunicorn hikvision_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

