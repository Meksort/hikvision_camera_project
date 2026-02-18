# Как получить данные из приложения в Docker

Приложение доступно по адресу **http://localhost:8000** (порт проброшен из контейнера).

---

## 1. Через REST API (браузер, curl, Postman, фронт)

Базовый URL: **http://localhost:8000/api/v1/**

| Данные | URL |
|--------|-----|
| События камер | `GET http://localhost:8000/api/v1/camera-events/` |
| Входы/выходы | `GET http://localhost:8000/api/v1/entries-exits/` |
| Подразделения | `GET http://localhost:8000/api/v1/departments/` |
| Статистика посещаемости | `GET http://localhost:8000/api/v1/attendance-stats/` |
| Топ опоздавших | `GET http://localhost:8000/api/v1/top-late-employees/` |

**Пример в PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/departments/" -Method Get
```

**Пример в браузере:** откройте вкладку и перейдите по нужному URL.

---

## 2. Экспорт сотрудников в Excel (из контейнера)

Скрипт запускает экспорт **внутри** контейнера (с доступом к БД) и копирует файл на хост.

**PowerShell:**
```powershell
.\run_export_employees.ps1 employees_export.xlsx
```

**CMD:**
```cmd
run_export_employees.bat employees_export.xlsx
```

Файл `employees_export.xlsx` появится в папке проекта.

---

## 3. Любая команда внутри контейнера

Имя контейнера: **hikvision_web**.

**Запуск Python-скрипта:**
```powershell
docker exec -it hikvision_web python /app/export_employees.py /app/employees_export.xlsx
```

**Django management-команды:**
```powershell
docker exec -it hikvision_web python /app/manage.py shell
docker exec -it hikvision_web python /app/manage.py dumpdata camera_events.Employee > employees_backup.json
```

**Скопировать созданный файл из контейнера на хост:**
```powershell
docker cp hikvision_web:/app/employees_export.xlsx ./employees_export.xlsx
```

---

## 4. Админка Django

**URL:** http://localhost:8000/admin/

Через админку можно просматривать и выгружать данные по моделям (события, сотрудники, подразделения и т.д.).

---

## 5. База данных

Если БД в Docker — подключайтесь к контейнеру БД.  
Если БД на хосте (`DB_HOST=host.docker.internal`) — подключайтесь к PostgreSQL на хосте (порт 5432) теми же учётными данными, что в `.env` / `docker-compose`.

---

## Проверка, что контейнер запущен

```powershell
docker ps -f "name=hikvision_web"
```

Если контейнер не запущен: `docker-compose up -d`.
