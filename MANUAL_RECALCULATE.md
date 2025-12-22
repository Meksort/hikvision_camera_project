# Ручной запуск пересчета статистики

Доступны следующие способы запуска пересчета статистики:

## Способ 1: Через API (рекомендуется)

### Запуск через POST запрос:

```bash
POST http://localhost:8000/api/attendance-stats/recalculate/
```

### С параметром даты начала:

```bash
POST http://localhost:8000/api/attendance-stats/recalculate/?start_date=2024-12-01
```

Или в теле запроса:
```json
{
  "start_date": "2024-12-01"
}
```

### Примеры использования:

**cURL:**
```bash
curl -X POST http://localhost:8000/api/attendance-stats/recalculate/
```

**Python requests:**
```python
import requests
response = requests.post('http://localhost:8000/api/attendance-stats/recalculate/', 
                        json={'start_date': '2024-12-01'})
print(response.json())
```

**JavaScript (fetch):**
```javascript
fetch('http://localhost:8000/api/attendance-stats/recalculate/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({start_date: '2024-12-01'})
})
.then(res => res.json())
.then(data => console.log(data));
```

## Способ 2: Через командную строку

Запустите скрипт напрямую:

```bash
python recalculate_attendance_stats.py
```

Или через bat файл:

```bash
recalculate_attendance_stats.bat
```

## Способ 3: Через планировщик Windows (для автоматизации по расписанию)

1. Откройте **Планировщик заданий Windows** (Task Scheduler)
2. Создайте новое задание
3. В действии (Action) укажите:
   - **Программа:** `C:\Users\nzhed\OneDrive\Desktop\hikvision_camera_project\recalculate_stats_scheduled.bat`
   - **Рабочая папка:** `C:\Users\nzhed\OneDrive\Desktop\hikvision_camera_project`
4. Настройте расписание (например, каждые 30 минут или каждый час)

## Преимущества нового подхода:

1. ✅ **Контроль** - вы сами решаете, когда запускать пересчет
2. ✅ **Производительность** - нет фоновых задач, которые могут мешать работе
3. ✅ **Гибкость** - можно запускать по требованию через API или по расписанию через планировщик Windows
4. ✅ **Надежность** - нет конфликтов с внутренними планировщиками

## Примечания:

- Пересчет запускается в фоновом режиме через API, поэтому ответ приходит сразу
- Для отслеживания прогресса проверяйте логи Django
- По умолчанию пересчет начинается с 1 декабря текущего года
- Можно указать любую дату начала через параметр `start_date`

