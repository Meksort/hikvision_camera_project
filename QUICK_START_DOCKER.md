# Быстрый запуск в Docker

## Шаг 1: Установите Docker Desktop

Скачайте и установите: https://www.docker.com/products/docker-desktop

## Шаг 2: Запустите проект

Просто запустите:
```bash
docker-start.bat
```

Или вручную:
```bash
docker-compose up --build -d
```

## Шаг 3: Откройте в браузере

- **Локально:** http://localhost:8000/
- **Из сети:** http://192.168.1.129:8000/

### Админка:
- URL: http://192.168.1.129:8000/admin/
- Логин: `admin`
- Пароль: `admin123`

## Остановка

```bash
docker-stop.bat
```

Или:
```bash
docker-compose down
```

## Просмотр логов

```bash
docker-compose logs -f
```

## Что происходит автоматически

✅ Миграции БД выполняются автоматически  
✅ Суперпользователь создается автоматически (admin/admin123)  
✅ База данных сохраняется между перезапусками  

## Проблемы?

См. подробную документацию: `DOCKER_SETUP.md`



















