# Frontend для системы мониторинга сотрудников Hikvision

React + TypeScript приложение для визуализации статистики посещаемости сотрудников.

## Требования

- Node.js 18+ 
- npm или yarn

## Установка

1. Перейдите в папку frontend:
```bash
cd frontend
```

2. Установите зависимости:
```bash
npm install
```

## Настройка

Создайте файл `.env` в папке `frontend` для настройки API URL:

```
REACT_APP_API_URL=http://localhost:8000/api/v1
```

Если вы запускаете Django на другом хосте/порту, измените URL соответственно.

## Запуск в режиме разработки

```bash
npm start
```

Приложение откроется в браузере по адресу http://localhost:3000

## Сборка для продакшена

```bash
npm run build
```

Собранные файлы будут в папке `build/`. Эти файлы можно развернуть на веб-сервере или интегрировать с Django (см. ниже).

## Интеграция с Django

### Вариант 1: Отдельный dev сервер (рекомендуется для разработки)

1. Запустите Django сервер на http://localhost:8000
2. Запустите React dev сервер на http://localhost:3000
3. Настройте proxy в `package.json` (уже настроено)

### Вариант 2: Статические файлы Django (для продакшена)

1. Соберите React приложение: `npm run build`
2. Скопируйте содержимое папки `build` в папку `static` Django проекта
3. Настройте Django для раздачи статических файлов (см. Django settings)
4. Настройте маршруты в Django для обслуживания React приложения

## Структура проекта

```
frontend/
├── public/          # Статические файлы
├── src/
│   ├── api/        # API клиент
│   ├── components/ # React компоненты
│   │   ├── Sidebar/
│   │   ├── FiltersBar/
│   │   ├── KpiCards/
│   │   ├── ProgressBar/
│   │   └── EmployeesTable/
│   ├── pages/      # Страницы приложения
│   ├── types/      # TypeScript типы
│   └── App.tsx     # Главный компонент
├── package.json
└── tsconfig.json
```

## Используемые технологии

- React 18.2
- TypeScript 5.3
- React Router 6.21
- Axios для HTTP запросов
- date-fns для работы с датами
- CSS для стилизации (без фреймворков)

## API Endpoints

Приложение использует следующие API endpoints:

- `GET /api/v1/attendance-stats/` - Получение статистики посещаемости
- `GET /api/v1/departments/` - Получение списка отделов

## Функциональность

- ✅ Sidebar с навигацией
- ✅ Фильтры по периодам и отделам
- ✅ KPI карточки (Отработано, Продуктивно, Простой, Отвлечения)
- ✅ Таблица сотрудников с группировкой по отделам
- ✅ Прогресс-бары для визуализации статистики
- ✅ Поиск по сотрудникам
- ✅ Экспорт отчетов (в разработке)

## Решение проблем

### CORS ошибки

Если возникают CORS ошибки, убедитесь, что в Django settings.py настроен CORS:

```python
INSTALLED_APPS = [
    ...
    'corsheaders',
]

MIDDLEWARE = [
    ...
    'corsheaders.middleware.CorsMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

### API не отвечает

Проверьте, что Django сервер запущен и доступен по адресу, указанному в `REACT_APP_API_URL`.


