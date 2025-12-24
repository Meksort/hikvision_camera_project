# Где находится база данных

## Текущая конфигурация

Согласно настройкам в `docker-compose.yml`, используется **локальная PostgreSQL** (не в Docker).

## Расположение локальной PostgreSQL на Windows

### Стандартные пути установки:

1. **Данные БД (data directory):**
   - `C:\Program Files\PostgreSQL\{версия}\data`
   - Например: `C:\Program Files\PostgreSQL\15\data`

2. **Конфигурационные файлы:**
   - `postgresql.conf` - в директории data
   - `pg_hba.conf` - в директории data

### Как найти точное расположение:

#### Способ 1: Через psql
```bash
psql -U postgres -c "SHOW data_directory;"
```

#### Способ 2: Через pgAdmin
1. Откройте pgAdmin
2. Правый клик на сервере → Properties → Connection
3. Посмотрите путь к data directory

#### Способ 3: Через службы Windows
1. Откройте "Службы" (services.msc)
2. Найдите "postgresql-x64-{версия}"
3. Посмотрите путь к исполняемому файлу
4. Data directory обычно рядом

#### Способ 4: Через реестр Windows
```bash
reg query "HKLM\SOFTWARE\PostgreSQL\Installations" /s
```

## Расположение Docker volume (если использовался)

Если вы использовали Docker БД ранее, данные находятся в Docker volume:

```bash
# Найти volume
docker volume ls | grep postgres

# Посмотреть детали
docker volume inspect hikvision_camera_project_postgres_data

# Обычно на Windows находится в:
# \\wsl$\docker-desktop-data\data\docker\volumes\
```

## Текущие настройки подключения

Согласно `docker-compose.yml`:
- **DB_HOST**: `host.docker.internal` (локальная БД)
- **DB_PORT**: `5432`
- **DB_NAME**: `hikvision_db` (из .env или по умолчанию)
- **DB_USER**: `postgres` (из .env или по умолчанию)

## Проверка подключения

### Проверить, какая БД используется:
```bash
# Из контейнера
docker compose exec web python manage.py dbshell

# Или напрямую
psql -U postgres -h localhost -d hikvision_db
```

### Проверить расположение данных:
```sql
-- В psql выполните:
SHOW data_directory;
```

## Если нужно найти конкретную БД

```sql
-- Подключитесь к PostgreSQL
psql -U postgres

-- Посмотрите список БД
\l

-- Выберите БД
\c hikvision_db

-- Посмотрите таблицы
\dt
```

