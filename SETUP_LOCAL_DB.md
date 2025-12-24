# Настройка Docker для работы с локальной БД и доступом по IP

## Шаг 1: Создайте файл `.env` в корне проекта

Создайте файл `.env` со следующим содержимым:

```env
# Database configuration - подключение к локальной PostgreSQL
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=hikvision_db
DB_USER=postgres
DB_PASSWORD=postgres

# Django settings
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost;127.0.0.1;192.168.1.129;0.0.0.0

# Timezone
TZ=Asia/Almaty
```

**Важно:** Замените значения `DB_NAME`, `DB_USER`, `DB_PASSWORD` на ваши реальные данные локальной БД!

## Шаг 2: Убедитесь, что локальная PostgreSQL доступна

### Проверка подключения:
```bash
# Проверьте, что PostgreSQL запущен
psql -U postgres -h localhost -d hikvision_db -c "SELECT version();"
```

### Если PostgreSQL не принимает подключения из Docker:

#### Windows:
1. Откройте `postgresql.conf`
2. Найдите `listen_addresses` и установите: `listen_addresses = '*'`
3. Откройте `pg_hba.conf`
4. Добавьте строку: `host    all    all    0.0.0.0/0    md5`
5. Перезапустите PostgreSQL

#### Linux/Mac:
Аналогично, но файлы обычно в `/etc/postgresql/*/main/`

## Шаг 3: Перезапустите Docker контейнеры

```bash
# Остановите текущие контейнеры
docker compose down

# Запустите заново (БД контейнер не нужен, только web)
docker compose up -d web
```

## Шаг 4: Проверьте подключение

```bash
# Проверить подключение к БД
docker compose exec web python manage.py check --database default

# Проверить количество данных
docker compose exec web python manage.py shell
```

В Django shell:
```python
from camera_events.models import CameraEvent, Employee, EntryExit
print(f"Events: {CameraEvent.objects.count()}")
print(f"Employees: {Employee.objects.count()}")
print(f"Entries: {EntryExit.objects.count()}")
```

## Шаг 5: Проверьте доступ по IP

Приложение должно быть доступно:
- **Локально:** http://localhost:8000/
- **По сети:** http://192.168.1.129:8000/

## Устранение проблем

### Если не подключается к локальной БД:

1. **Проверьте, что PostgreSQL слушает на всех интерфейсах:**
   ```bash
   # Windows
   netstat -an | findstr :5432
   
   # Linux/Mac
   netstat -an | grep :5432
   ```

2. **Проверьте логи контейнера:**
   ```bash
   docker compose logs web | grep -i "database\|error"
   ```

3. **Попробуйте использовать IP адрес вместо host.docker.internal:**
   - Найдите IP вашего хоста: `ipconfig` (Windows) или `ifconfig` (Linux/Mac)
   - В `.env` замените `DB_HOST=host.docker.internal` на `DB_HOST=ваш_IP`

### Если не доступно по IP 192.168.1.129:

1. **Проверьте, что порт 8000 открыт в файрволе**
2. **Проверьте ALLOWED_HOSTS в `.env`:**
   ```env
   ALLOWED_HOSTS=localhost;127.0.0.1;192.168.1.129;0.0.0.0
   ```

3. **Проверьте, что сервер запущен на 0.0.0.0:**
   ```bash
   docker compose logs web | grep "Starting development server"
   ```
   Должно быть: `Starting development server at http://0.0.0.0:8000/`

## Альтернатива: Использовать IP хоста напрямую

Если `host.docker.internal` не работает, используйте IP адрес вашего компьютера:

1. Найдите IP адрес:
   ```bash
   # Windows
   ipconfig
   
   # Linux/Mac
   ifconfig
   ```

2. В `.env` замените:
   ```env
   DB_HOST=ваш_IP_адрес  # Например: 192.168.1.100
   ```

3. Убедитесь, что PostgreSQL принимает подключения с этого IP

