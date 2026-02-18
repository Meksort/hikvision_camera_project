# Инструкция по запуску Frontend

## Описание

Frontend часть проекта Hikvision Camera Project создана на React + TypeScript и предоставляет современный веб-интерфейс для мониторинга сотрудников.

## Требования

- Node.js 18 или выше
- npm или yarn

## Быстрый старт

### 1. Установка зависимостей

```bash
cd frontend
npm install
```

### 2. Запуск в режиме разработки

```bash
npm start
```

Приложение откроется автоматически в браузере по адресу http://localhost:3000

### 3. Сборка для продакшена

```bash
npm run build
```

Собранные файлы будут в папке `build/`.

## Структура проекта

```
frontend/
├── public/              # Статические файлы (index.html)
├── src/
│   ├── api/            # API клиент (client.ts)
│   ├── components/     # React компоненты
│   │   ├── Sidebar/    # Боковая панель навигации
│   │   ├── FiltersBar/ # Панель фильтров
│   │   ├── KpiCards/   # KPI карточки
│   │   ├── ProgressBar/# Прогресс-бар статистики
│   │   └── EmployeesTable/ # Таблица сотрудников
│   ├── pages/          # Страницы приложения
│   │   └── EmployeesPage.tsx # Главная страница мониторинга
│   ├── types/          # TypeScript типы
│   ├── App.tsx         # Главный компонент
│   └── index.tsx       # Точка входа
├── package.json
└── tsconfig.json
```

## Настройка API

По умолчанию frontend использует proxy для подключения к Django API (настроено в `package.json`):
- Dev сервер React: http://localhost:3000
- Django API: http://localhost:8000/api/v1

Если ваш Django сервер работает на другом хосте/порту, создайте файл `.env` в папке `frontend`:

```
REACT_APP_API_URL=http://your-django-host:8000/api/v1
```

## Используемые технологии

- **React 18.2** - UI библиотека
- **TypeScript 5.3** - типизация
- **React Router 6.21** - маршрутизация
- **Axios** - HTTP клиент
- **date-fns** - работа с датами
- **CSS** - стилизация (без фреймворков)

## Функциональность

✅ **Sidebar** - боковая панель с навигацией по разделам
✅ **FiltersBar** - фильтры по периодам (Сегодня, Неделя, Месяц, Квартал, Год, Диапазон) и отделам
✅ **KPI Cards** - карточки с метриками:
   - Отработано (синий)
   - Продуктивно (зеленый)
   - Простой (желтый)
   - Отвлечения (красный)
✅ **EmployeesTable** - таблица сотрудников с:
   - Группировкой по отделам
   - Прогресс-барами для визуализации статистики
   - Поиском по имени, должности, отделу
   - Отображением опозданий, ранних уходов, инцидентов
✅ **ProgressBar** - визуализация статистики с tooltip

## API Endpoints

Frontend использует следующие endpoints Django API:

- `GET /api/v1/attendance-stats/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&department=ID` - получение статистики
- `GET /api/v1/departments/` - получение списка отделов

## Решение проблем

### CORS ошибки

Если возникают CORS ошибки, убедитесь что в Django `settings.py` настроен CORS:

```python
INSTALLED_APPS = [
    ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    ...
]

CORS_ALLOW_ALL_ORIGINS = DEBUG  # Для разработки
```

### API не отвечает

1. Убедитесь что Django сервер запущен: `python manage.py runserver`
2. Проверьте что API доступен: http://localhost:8000/api/v1/attendance-stats/
3. Проверьте настройки proxy в `package.json` или `REACT_APP_API_URL` в `.env`

### Ошибки при установке зависимостей

Если возникают проблемы с установкой:
```bash
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

## Дальнейшая разработка

Для добавления новых компонентов:
1. Создайте компонент в `src/components/`
2. Добавьте типы в `src/types/` при необходимости
3. Используйте компонент в нужной странице

Для добавления новых API endpoints:
1. Добавьте метод в `src/api/client.ts`
2. Добавьте типы ответов в `src/types/index.ts`
3. Используйте в компонентах через хуки или прямое обращение к API

## Интеграция с Django

### Вариант 1: Отдельный dev сервер (рекомендуется для разработки)

Запустите оба сервера параллельно:
- Django: `python manage.py runserver` (http://localhost:8000)
- React: `npm start` (http://localhost:3000)

### Вариант 2: Статические файлы (для продакшена)

1. Соберите React: `npm run build`
2. Настройте Django для раздачи статических файлов из папки `build/`
3. Настройте маршруты в Django для обслуживания React SPA


