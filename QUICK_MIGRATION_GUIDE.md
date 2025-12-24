# Быстрая инструкция по переносу БД

## Сценарий 1: Перенос БД на другой компьютер (локальная БД)

### На старом компьютере:

1. **Создайте бэкап:**
   ```bash
   backup_database.bat
   ```
   Или вручную:
   ```bash
   pg_dump -U postgres -h localhost -d hikvision_db -F c -f backup.dump
   ```

2. **Скопируйте файл** `backup.dump` на новый компьютер

### На новом компьютере:

1. **Установите PostgreSQL 18**

2. **Создайте базу данных:**
   ```bash
   psql -U postgres -c "CREATE DATABASE hikvision_db;"
   ```

3. **Восстановите данные:**
   ```bash
   restore_database.bat
   ```
   Или вручную:
   ```bash
   pg_restore -U postgres -h localhost -d hikvision_db -v backup.dump
   ```

4. **Обновите `.env`:**
   ```env
   DB_HOST=host.docker.internal
   DB_PORT=5432
   DB_NAME=hikvision_db
   DB_USER=postgres
   DB_PASSWORD=ваш_пароль
   ```

---

## Сценарий 2: Подключение к удаленной БД (БД на другом компьютере)

### На компьютере с БД (сервер):

1. **Настройте PostgreSQL для сетевого доступа:**
   - Откройте `postgresql.conf`: `listen_addresses = '*'`
   - Откройте `pg_hba.conf`: добавьте `host all all 0.0.0.0/0 md5`
   - Откройте порт 5432 в файрволе
   - Перезапустите PostgreSQL

2. **Узнайте IP адрес сервера:**
   ```bash
   ipconfig
   # Запомните IPv4 адрес, например: 192.168.1.100
   ```

### На компьютере с Docker (клиент):

1. **Обновите `.env`:**
   ```env
   DB_HOST=192.168.1.100  # IP адрес сервера с БД
   DB_PORT=5432
   DB_NAME=hikvision_db
   DB_USER=postgres
   DB_PASSWORD=пароль_на_сервере
   ```

2. **Перезапустите контейнер:**
   ```bash
   docker compose down
   docker compose up -d web
   ```

3. **Проверьте подключение:**
   ```bash
   docker compose exec web python manage.py check --database default
   ```

---

## Проверка после миграции

```bash
# Проверить подключение
docker compose exec web python manage.py check --database default

# Проверить данные
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

## Автоматические бэкапы

Настройте задачу в Планировщике заданий Windows для регулярных бэкапов:

1. Откройте Планировщик заданий
2. Создайте задачу
3. Действие: запустить `backup_database.bat`
4. Расписание: ежедневно в 2:00 ночи

---

## Важно

- **Делайте бэкапы регулярно!**
- **Проверяйте бэкапы** перед удалением старой БД
- **Используйте сильные пароли** для PostgreSQL
- **Ограничьте доступ** в `pg_hba.conf` только нужными IP

