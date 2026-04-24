# Driveery

Driveery — сервис NL2SQL-аналитики для кейса Drivee: пользователь пишет вопрос на естественном языке, система генерирует SQL, проверяет безопасность запроса, выполняет его и показывает результат в таблице/графике.

## Быстрый запуск

Скопируйте шаблоны env-файлов:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Заполните `OPENROUTER_API_KEY` в `.env`.

```bash
docker compose up -d --build
```

После запуска:
- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Что умеет

- Запросы к данным на русском языке через чат
- Streaming reasoning в реальном времени
- Guardrails для SQL (блокировка опасных конструкций)
- Fallback для оффтоп-запросов и prompt injection
- Автоопределение `table`/`chart` по типу данных
- Сохраненные отчеты и аудит в `query_logs`

## Схема базы данных

![Схема БД](docs/db-schema.png)

Основные таблицы: `users`, `cities`, `drivers`, `trips`, `orders`, `saved_reports`, `query_logs`, `semantic_terms`.

## UserFlow (чат → backend)

![UserFlow](docs/user-flow.png)

## Архитектура backend

```text
backend/app/
  domain/           -> сущности и исключения
  application/      -> use case-слой (nl2sql, security, chart, intent fallback)
  infrastructure/   -> DB модели и OpenRouter клиент
  api/v1/           -> FastAPI роуты и схемы
```
