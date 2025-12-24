# Перенос базы данных на другой компьютер

## Вариант 1: Полный перенос БД на другой компьютер (рекомендуется)

### Шаг 1: Экспорт данных с текущего компьютера

На **текущем компьютере** выполните:

```bash
# Создать полный бэкап БД (структура + данные)
pg_dump -U postgres -h localhost -d hikvision_db -F c -f hikvision_backup.dump

# Или в SQL формате (более универсальный)
pg_dump -U postgres -h localhost -d hikvision_db > hikvision_backup.sql
```

**Параметры:**
- `-U postgres` - пользователь
- `-h localhost` - хост
- `-d hikvision_db` - имя базы данных
- `-F c` - формат custom (для .dump)
- `-f` - файл вывода

### Шаг 2: Установка PostgreSQL на новом компьютере

1. Скачайте и установите PostgreSQL 18 (или ту же версию, что у вас)
2. Запомните пароль пользователя `postgres`
3. Убедитесь, что PostgreSQL запущен

### Шаг 3: Создание базы данных на новом компьютере

На **новом компьютере** выполните:

```bash
# Создать базу данных
psql -U postgres -c "CREATE DATABASE hikvision_db;"

# Создать пользователя (если нужен отдельный)
psql -U postgres -c "CREATE USER postgres WITH PASSWORD 'ваш_пароль';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE hikvision_db TO postgres;"
```

### Шаг 4: Импорт данных на новый компьютер

Скопируйте файл бэкапа на новый компьютер, затем:

```bash
# Для .dump файла
pg_restore -U postgres -h localhost -d hikvision_db -v hikvision_backup.dump

# Для .sql файла
psql -U postgres -h localhost -d hikvision_db < hikvision_backup.sql
```

### Шаг 5: Настройка Docker на новом компьютере

Обновите `.env` файл:

```env
# Подключение к БД на новом компьютере
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=hikvision_db
DB_USER=postgres
DB_PASSWORD=ваш_пароль_на_новом_компьютере

# Django settings
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost;127.0.0.1;192.168.1.129;0.0.0.0

TZ=Asia/Almaty
```

---

## Вариант 2: Подключение к удаленной БД (БД на другом компьютере)

### Шаг 1: Настройка PostgreSQL на удаленном компьютере

На **компьютере с БД** (новый компьютер):

#### 1.1. Настройте `postgresql.conf`:
```bash
# Найдите файл (обычно в C:\Program Files\PostgreSQL\18\data\postgresql.conf)
# Или через psql:
psql -U postgres -c "SHOW config_file;"
```

Откройте `postgresql.conf` и найдите:
```conf
listen_addresses = 'localhost'  # Измените на:
listen_addresses = '*'         # Слушать на всех интерфейсах
```

#### 1.2. Настройте `pg_hba.conf`:
Откройте `pg_hba.conf` и добавьте в конец:
```conf
# Разрешить подключения из сети
host    all    all    0.0.0.0/0    md5
# Или для конкретной подсети:
host    all    all    192.168.1.0/24    md5
```

#### 1.3. Перезапустите PostgreSQL:
```powershell
# Windows
Restart-Service postgresql-x64-18
# Или через службы Windows
```

#### 1.4. Откройте порт в файрволе:
```powershell
# Windows Firewall
New-NetFirewallRule -DisplayName "PostgreSQL" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

### Шаг 2: Настройка Docker на текущем компьютере

Обновите `.env` файл:

```env
# Подключение к удаленной БД
DB_HOST=192.168.1.XXX  # IP адрес нового компьютера
DB_PORT=5432
DB_NAME=hikvision_db
DB_USER=postgres
DB_PASSWORD=пароль_на_удаленном_компьютере

# Django settings
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost;127.0.0.1;192.168.1.129;0.0.0.0

TZ=Asia/Almaty
```

### Шаг 3: Проверка подключения

```bash
# С текущего компьютера проверьте подключение
psql -U postgres -h 192.168.1.XXX -d hikvision_db

# Или из Docker контейнера
docker compose exec web python manage.py check --database default
```

---

## Вариант 3: Использование Docker volume на другом компьютере

Если хотите использовать Docker БД на другом компьютере:

### Шаг 1: Экспорт Docker volume

На **текущем компьютере**:
```bash
# Остановите контейнеры
docker compose down

# Создайте бэкап volume
docker run --rm -v hikvision_camera_project_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_backup.tar.gz /data
```

### Шаг 2: Перенос на новый компьютер

1. Скопируйте `postgres_data_backup.tar.gz` на новый компьютер
2. Скопируйте `docker-compose.yml` и обновите его

### Шаг 3: Восстановление на новом компьютере

```bash
# Создайте volume
docker volume create postgres_data

# Восстановите данные
docker run --rm -v postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_data_backup.tar.gz -C /
```

---

## Рекомендации

### Безопасность:

1. **Используйте сильные пароли** для PostgreSQL
2. **Ограничьте доступ** в `pg_hba.conf` только нужными IP
3. **Используйте SSL** для удаленных подключений (опционально)

### Производительность:

1. **Локальная БД** быстрее, чем удаленная
2. **Удаленная БД** удобнее для централизованного хранения
3. **Регулярные бэкапы** - настройте автоматическое резервное копирование

### Автоматические бэкапы:

Создайте скрипт `backup_db.bat`:
```batch
@echo off
set BACKUP_DIR=C:\Backups\PostgreSQL
set DB_NAME=hikvision_db
set DATE=%date:~-4,4%%date:~-10,2%%date:~-7,2%

mkdir %BACKUP_DIR% 2>nul

"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -h localhost -d %DB_NAME% > %BACKUP_DIR%\hikvision_db_%DATE%.sql

echo Backup created: %BACKUP_DIR%\hikvision_db_%DATE%.sql
```

---

## Проверка после миграции

```bash
# Проверить подключение
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

---

## Устранение проблем

### Ошибка подключения:
1. Проверьте, что PostgreSQL запущен на удаленном компьютере
2. Проверьте файрвол (порт 5432 открыт)
3. Проверьте `pg_hba.conf` (разрешения)
4. Проверьте `postgresql.conf` (listen_addresses)

### Ошибка аутентификации:
1. Проверьте пароль в `.env`
2. Проверьте пользователя в `pg_hba.conf`
3. Убедитесь, что пользователь существует: `\du` в psql

