# Исправление ошибки с большим файлом в Git

## Проблема
Файл бэкапа БД (886 MB) превышает лимит GitHub (100 MB) и не может быть загружен.

## Решение

### Шаг 1: Удалить файл из истории Git

Выполните следующие команды в PowerShell:

```powershell
# 1. Удалить файл из индекса Git (но оставить на диске)
git rm --cached backups/hikvision_db_20252412_175544.dump

# 2. Закоммитить удаление
git commit -m "Remove large backup file from repository"

# 3. Если файл уже был в предыдущих коммитах, нужно очистить историю
# ВАЖНО: Это перепишет историю Git!
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch backups/hikvision_db_20252412_175544.dump" --prune-empty --tag-name-filter cat -- --all

# Или используйте более современный способ (если установлен git-filter-repo):
# git filter-repo --path backups/hikvision_db_20252412_175544.dump --invert-paths
```

### Шаг 2: Принудительно запушить изменения

```powershell
# ВНИМАНИЕ: Это перезапишет историю на удаленном репозитории!
git push origin main --force
```

**⚠️ ВАЖНО:** `--force` перезапишет историю на GitHub. Убедитесь, что никто другой не работает с этим репозиторием!

### Альтернативный способ (если файл только в последнем коммите):

```powershell
# 1. Отменить последний коммит (но сохранить изменения)
git reset --soft HEAD~1

# 2. Удалить файл из индекса
git rm --cached backups/hikvision_db_20252412_175544.dump

# 3. Закоммитить снова (без большого файла)
git commit -m "Your commit message"

# 4. Запушить
git push origin main --force
```

## Проверка

После исправления проверьте:

```powershell
# Проверить размер файлов в репозитории
git ls-files | ForEach-Object { Get-Item $_ } | Measure-Object -Property Length -Sum

# Убедиться, что файл не отслеживается
git ls-files backups/
```

## Предотвращение в будущем

1. ✅ Файл `.gitignore` уже обновлен - папка `backups/` теперь игнорируется
2. ✅ Все файлы `.dump`, `.sql`, `.backup` теперь игнорируются

## Рекомендации

- **НЕ коммитьте бэкапы БД в Git** - они слишком большие
- Храните бэкапы отдельно (OneDrive, внешний диск, облачное хранилище)
- Используйте `.gitignore` для исключения больших файлов
- Если нужно хранить бэкапы в репозитории, используйте Git LFS (Large File Storage)

