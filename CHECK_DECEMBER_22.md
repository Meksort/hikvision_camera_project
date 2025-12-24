# Проверка данных за 22 декабря 2025

Созданы два способа проверки данных за 22 декабря:

## Способ 1: Через API (самый простой)

Откройте в браузере:

```
http://192.168.1.25:8000/api/v1/entries-exits/check-date/?date=2025-12-22
```

Или для другой даты:

```
http://192.168.1.25:8000/api/v1/entries-exits/check-date/?date=2025-12-23
```

API вернет JSON с:
- Все события CameraEvent за эту дату
- Все записи EntryExit за эту дату
- Список проблем (кто есть в событиях, но нет в EntryExit)

## Способ 2: Через скрипт (более детальный вывод)

### Если проект запущен в Docker:

1. Откройте терминал в папке проекта
2. Выполните:

```bash
docker-compose exec web python check_december_22.py
```

### Если проект запущен локально:

1. Откройте терминал в папке проекта
2. Выполните:

```bash
python check_december_22.py
```

Скрипт выведет:
- Все сырые события из CameraEvent
- Все рассчитанные записи EntryExit
- Проблемные случаи (кто есть в событиях, но нет полной записи)

## Что делать после проверки?

1. **Если видите проблемы** - данные есть в CameraEvent, но нет в EntryExit:
   
   ### Вариант A: Через API (если Django сервер запущен)
   
   Выполните POST запрос:
   ```
   POST http://192.168.1.25:8000/api/v1/entries-exits/full-recalculate/
   ```
   
   С параметрами даты (в теле запроса или query params):
   ```json
   {
     "start_date": "2025-12-22",
     "end_date": "2025-12-22"
   }
   ```
   
   Или через cURL:
   ```bash
   curl -X POST "http://192.168.1.25:8000/api/v1/entries-exits/full-recalculate/?start_date=2025-12-22&end_date=2025-12-22"
   ```
   
   ### Вариант B: Локальный скрипт (без Docker, без запущенного сервера)
   
   **Через Python:**
   ```bash
   python recalculate_entries_exits.py --start-date 2025-12-22 --end-date 2025-12-22
   ```
   
   **Через bat-файл (Windows):**
   ```bash
   recalculate_entries_exits.bat --start-date 2025-12-22 --end-date 2025-12-22
   ```
   
   Или просто для одной даты:
   ```bash
   recalculate_entries_exits.bat --start-date 2025-12-22
   ```
   
   После пересчёта снова запустите проверку (`check_december_22.py` или API) и проверьте, появились ли записи EntryExit.

2. **Если данных вообще нет** - значит события за 22 декабря не пришли от камер Hikvision

3. **Если все в порядке** - данные есть и правильно рассчитаны, значит проблема в экспорте Excel (нужно проверить SQL запрос)

## Пример вывода API

```json
{
  "date": "2025-12-22",
  "summary": {
    "total_camera_events": 45,
    "total_entry_exits": 20,
    "employees_with_events": 15,
    "employees_with_entry_exits": 10,
    "problems_count": 5
  },
  "problems": [
    {
      "hikvision_id": "00000025",
      "employee_name": "Еременко Роза",
      "events_count": 2,
      "has_partial_entry_exit": true,
      "message": "Есть события CameraEvent, но нет полной записи EntryExit (нет выхода)"
    }
  ],
  "camera_events": {
    "00000025": {
      "employee_name": "Еременко Роза",
      "events_count": 2,
      "events": [
        {
          "id": 12345,
          "time": "09:05:00",
          "device_name": "Вход 1",
          "raw_data": {...}
        },
        {
          "id": 12346,
          "time": "18:01:00",
          "device_name": "Выход 1",
          "raw_data": {...}
        }
      ]
    }
  },
  "entry_exits": {
    "00000025": {
      "employee_name": "Еременко Роза",
      "entries_count": 1,
      "entries": [
        {
          "id": 5678,
          "entry_time": "09:05:00",
          "exit_time": null,
          "duration": "0ч 0м",
          "is_complete": false
        }
      ]
    }
  }
}
```

