# Перенос данных из локальной БД в Docker

## Проблема
Docker создает новую пустую базу данных, а ваши данные находятся в локальной PostgreSQL.

## Решение 1: Подключить Docker к локальной БД (быстро)

### Шаг 1: Убедитесь, что локальная PostgreSQL запущена и доступна

### Шаг 2: Создайте файл `.env` в корне проекта (если его нет):
```env
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=hikvision_db
DB_USER=postgres
DB_PASSWORD=postgres
```

### Шаг 3: Перезапустите контейнеры:
```bash
docker compose down
docker compose up -d
```

**Примечание:** `host.docker.internal` работает на Windows и Mac. На Linux используйте IP-адрес вашего хоста.

---

## Решение 2: Перенести данные из локальной БД в Docker (рекомендуется)

### Шаг 1: Экспортируйте данные из локальной БД

```bash
# Экспорт всей БД
pg_dump -U postgres -h localhost -d hikvision_db > backup.sql

# Или только структура + данные
pg_dump -U postgres -h localhost -d hikvision_db --clean --if-exists > backup.sql
```

### Шаг 2: Убедитесь, что Docker контейнеры запущены

```bash
docker compose up -d db
```

### Шаг 3: Импортируйте данные в Docker БД

```bash
# Через docker exec
docker exec -i hikvision_db psql -U postgres -d hikvision_db < backup.sql

# Или если файл большой, используйте cat
cat backup.sql | docker exec -i hikvision_db psql -U postgres -d hikvision_db
```

### Шаг 4: Перезапустите веб-контейнер

```bash
docker compose restart web
```

---

## Решение 3: Использовать существующий volume PostgreSQL

Если у вас есть бэкап данных PostgreSQL, можно заменить volume:

### Шаг 1: Остановите контейнеры
```bash
docker compose down
```

### Шаг 2: Замените данные в volume
```bash
# Найдите volume
docker volume ls | grep postgres_data

# Скопируйте данные в volume (требует root доступ к данным PostgreSQL)
```

---

## Проверка подключения

### Проверить подключение к БД из контейнера:
```bash
docker compose exec web python manage.py dbshell
```

### Проверить количество записей:
```bash
docker compose exec web python manage.py shell
```

В Django shell:
```python
from camera_events.models import CameraEvent, Employee, EntryExit
print(f"CameraEvent: {CameraEvent.objects.count()}")
print(f"Employee: {Employee.objects.count()}")
print(f"EntryExit: {EntryExit.objects.count()}")
```

---

## Быстрая проверка

Если данные не отображаются, проверьте:

1. **Подключение к БД:**
   ```bash
   docker compose exec web python manage.py check --database default
   ```

2. **Логи контейнера:**
   ```bash
   docker compose logs web | grep -i "database\|error"
   ```

3. **Проверка переменных окружения:**
   ```bash
   docker compose exec web env | grep DB_
   ```

---

## Важно

- Если используете локальную БД, убедитесь, что PostgreSQL настроен на прием подключений из Docker
- Проверьте `pg_hba.conf` и `postgresql.conf` для разрешения внешних подключений
- Убедитесь, что порт 5432 не заблокирован файрволом

