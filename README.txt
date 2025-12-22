ПРОЕКТ ДЛЯ ПРИЕМА ДАННЫХ ОТ КАМЕР HIKVISION

БЫСТРЫЙ СТАРТ:

Вариант 1: Запуск в Docker (рекомендуется)
1. Установите Docker Desktop: https://www.docker.com/products/docker-desktop
2. Запустите: docker-start.bat
3. Откройте: http://192.168.1.129:8000/
Подробнее: DOCKER_SETUP.md

Вариант 2: Локальный запуск
1. Активируйте виртуальное окружение: .\venv\Scripts\Activate.ps1
2. Установите зависимости: pip install -r requirements.txt
3. Выполните миграции: python manage.py migrate
4. Запустите сервер: start.bat (или python manage.py runserver 0.0.0.0:8000)
5. Откройте в браузере: http://localhost:8000/report/

ДОСТУП ИЗ ЛОКАЛЬНОЙ СЕТИ:
IP адрес сервера: 192.168.1.129
- http://192.168.1.129:8000/ - главная страница
- http://192.168.1.129:8000/admin/ - админка (admin/admin123)
- http://192.168.1.129:8000/report/ - отчеты
- http://192.168.1.129:8000/attendance-stats/ - статистика

Админка: http://localhost:8000/admin/ (или http://192.168.1.129:8000/admin/)
Логин: admin
Пароль: admin123

API:
- События: http://localhost:8000/api/camera-events/ (или http://192.168.1.129:8000/api/camera-events/)
- Входы/выходы: http://localhost:8000/api/entries-exits/
- Экспорт Excel: http://localhost:8000/api/entries-exits/export-excel/
- Статистика: http://localhost:8000/api/attendance-stats/

Настройка камер:
URL: http://192.168.1.129:8000/api/camera-events/
Method: POST
Content Type: multipart/form-data
Event Type: AccessControllerEvent

ПЕРЕСЧЕТ СТАТИСТИКИ:
- Для ручного пересчета статистики используйте: python recalculate_attendance_stats.py
- Или через API: POST http://localhost:8000/api/attendance-stats/recalculate/
- Подробнее см. MANUAL_RECALCULATE.md

