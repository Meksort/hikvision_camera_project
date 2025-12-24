# Расположение базы данных

## ✅ Найдено!

**PostgreSQL установлен:** `C:\Program Files\PostgreSQL\18\`

**Данные БД находятся:** `C:\Program Files\PostgreSQL\18\data\`

## Детальная информация

### Основные пути:

1. **Исполняемые файлы:**
   - `C:\Program Files\PostgreSQL\18\bin\psql.exe`
   - `C:\Program Files\PostgreSQL\18\bin\pg_dump.exe`

2. **Данные базы данных:**
   - `C:\Program Files\PostgreSQL\18\data\`
   - Здесь хранятся все базы данных, включая `hikvision_db`

3. **Конфигурационные файлы:**
   - `C:\Program Files\PostgreSQL\18\data\postgresql.conf` - основные настройки
   - `C:\Program Files\PostgreSQL\18\data\pg_hba.conf` - настройки доступа

### Ваша база данных `hikvision_db`:

Физически данные находятся в:
```
C:\Program Files\PostgreSQL\18\data\base\{OID базы данных}\
```

Чтобы найти точный OID базы данных:
```sql
SELECT oid, datname FROM pg_database WHERE datname = 'hikvision_db';
```

## Текущие настройки подключения

Согласно `docker-compose.yml` и `.env`:
- **Хост:** `host.docker.internal` (локальная БД на вашем компьютере)
- **Порт:** `5432`
- **База данных:** `hikvision_db`
- **Пользователь:** `postgres`
- **Пароль:** (из вашего `.env` файла)

## Проверка подключения

### Из командной строки:
```bash
psql -U postgres -h localhost -d hikvision_db
```

### Из Docker контейнера:
```bash
docker compose exec web python manage.py dbshell
```

## Резервное копирование

Для создания бэкапа вашей БД:
```bash
pg_dump -U postgres -h localhost -d hikvision_db > backup.sql
```

## Важно

- Данные БД физически находятся на вашем компьютере
- Docker контейнер подключается к этой локальной БД через `host.docker.internal`
- При переустановке Windows или PostgreSQL данные могут быть потеряны - делайте бэкапы!

