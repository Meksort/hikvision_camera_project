# Безопасное восстановление базы данных

## ✅ Важно: Восстановление НЕ затрагивает другие базы данных

При восстановлении базы данных `hikvision_db` **НЕ будут затронуты** другие базы данных на том же сервере PostgreSQL.

### Почему это безопасно:

1. **Каждая база данных изолирована** - PostgreSQL хранит каждую БД в отдельной директории
2. **Команда `pg_restore` работает только с указанной БД** - она не трогает другие БД
3. **Таблицы в разных БД независимы** - нет риска перезаписи или удаления

## Что происходит при восстановлении:

### Вариант 1: Восстановление в существующую БД

```bash
pg_restore -U postgres -h localhost -d hikvision_db backup.dump
```

**Что происходит:**
- ✅ Восстанавливаются только таблицы в БД `hikvision_db`
- ✅ Другие БД (`postgres`, `template1`, и т.д.) **НЕ затрагиваются**
- ✅ Если таблицы уже существуют, они будут перезаписаны (только в `hikvision_db`)

### Вариант 2: Создание новой БД и восстановление

```bash
# Создать новую БД
psql -U postgres -c "CREATE DATABASE hikvision_db;"

# Восстановить в новую БД
pg_restore -U postgres -h localhost -d hikvision_db backup.dump
```

**Что происходит:**
- ✅ Создается новая БД `hikvision_db`
- ✅ Другие БД **НЕ затрагиваются**
- ✅ Это самый безопасный вариант

## Проверка перед восстановлением:

### 1. Посмотреть список всех БД:

```sql
psql -U postgres -c "\l"
```

Вы увидите что-то вроде:
```
   Name    |  Owner   | Encoding | Collate | Ctype |   Access privileges   
-----------+----------+----------+---------+-------+-----------------------
 postgres  | postgres | UTF8     | ...     | ...   | 
 template0 | postgres | UTF8     | ...     | ...   | 
 template1 | postgres | UTF8     | ...     | ...   | 
 other_db  | postgres | UTF8     | ...     | ...   |  <- Другие БД
 hikvision_db | postgres | UTF8 | ...     | ...   |  <- Ваша БД
```

### 2. Проверить, существует ли БД `hikvision_db`:

```sql
psql -U postgres -c "SELECT datname FROM pg_database WHERE datname = 'hikvision_db';"
```

### 3. Если БД существует, посмотреть таблицы:

```sql
psql -U postgres -d hikvision_db -c "\dt"
```

## Безопасная процедура восстановления:

### Шаг 1: Создать бэкап существующей БД (на всякий случай)

```bash
# Если БД уже существует, сделайте бэкап перед восстановлением
pg_dump -U postgres -h localhost -d hikvision_db -F c -f hikvision_db_backup_before_restore.dump
```

### Шаг 2: Восстановить БД

**Вариант A: БД не существует (самый безопасный)**
```bash
# Создать новую БД
psql -U postgres -c "CREATE DATABASE hikvision_db;"

# Восстановить
pg_restore -U postgres -h localhost -d hikvision_db backup.dump
```

**Вариант B: БД уже существует**
```bash
# Удалить старую БД (ВНИМАНИЕ: удалит данные в hikvision_db!)
psql -U postgres -c "DROP DATABASE IF EXISTS hikvision_db;"

# Создать новую
psql -U postgres -c "CREATE DATABASE hikvision_db;"

# Восстановить
pg_restore -U postgres -h localhost -d hikvision_db backup.dump
```

### Шаг 3: Проверить, что другие БД не затронуты

```sql
# Проверить список всех БД
psql -U postgres -c "\l"

# Проверить таблицы в другой БД (например, other_db)
psql -U postgres -d other_db -c "\dt"
```

## Что НЕ будет затронуто:

✅ **Другие базы данных** - `postgres`, `template0`, `template1`, и любые другие БД  
✅ **Системные таблицы PostgreSQL** - они в системных БД  
✅ **Пользователи и роли** - они глобальные, не привязаны к конкретной БД  
✅ **Настройки PostgreSQL** - `postgresql.conf`, `pg_hba.conf`  
✅ **Другие схемы** - если они в других БД  

## Что БУДЕТ затронуто:

⚠️ **Только база данных `hikvision_db`** - все таблицы в этой БД будут восстановлены/перезаписаны

## Рекомендации:

1. **Всегда делайте бэкап** перед восстановлением, если БД уже существует
2. **Проверяйте список БД** перед восстановлением
3. **Используйте отдельную БД** для каждого проекта
4. **Тестируйте на тестовой БД** перед восстановлением на продакшене

## Пример безопасного восстановления:

```bash
# 1. Проверить существующие БД
psql -U postgres -c "\l"

# 2. Сделать бэкап существующей БД (если есть)
pg_dump -U postgres -h localhost -d hikvision_db -F c -f backup_before_restore.dump

# 3. Создать/пересоздать БД
psql -U postgres -c "DROP DATABASE IF EXISTS hikvision_db;"
psql -U postgres -c "CREATE DATABASE hikvision_db;"

# 4. Восстановить
pg_restore -U postgres -h localhost -d hikvision_db hikvision_db_20252412_175544.dump

# 5. Проверить, что другие БД не затронуты
psql -U postgres -c "\l"
psql -U postgres -d other_db -c "\dt"  # Проверить другую БД
```

## Итог:

✅ **Восстановление БД безопасно для других БД**  
✅ **Затрагивается только указанная БД** (`hikvision_db`)  
✅ **Другие базы данных останутся нетронутыми**

