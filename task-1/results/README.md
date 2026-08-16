# Task 1. Локальный POC Apache Airflow

## Что здесь

- `docker-compose.yml` — Airflow 2.9.3 (webserver + scheduler), PostgreSQL, MailHog
- `dags/marketing_client_pipeline.py` — пайплайн POC
- `sql/01-source.sql` — таблица заказов (источник «база данных»)
- `data/delivery_statuses.csv` — статусы доставок (источник «файловая система»)
- `justification.md` — обоснование выбора Airflow и ответы на вопросы задания
- `screenshots/` — демонстрация локального прогона
- `capture.py` — скрипт, которым сняты скриншоты

## Запуск

```bash
cd task-1/results
docker compose up -d
```

Дождаться healthy у `airflow-webserver`. Открыть:

- Airflow UI: http://localhost:8088 (логин `admin` / `admin`)
- MailHog UI: http://localhost:8025

Порт 8088, а не 8080, потому что 8080 часто занят другим локальным сервисом.

## Шаги пайплайна из задания

| Требование | Где в POC |
|---|---|
| Чтение из источника (БД, файловая система) | `extract_orders` (PostgreSQL `shop.orders`), `extract_delivery_csv` (CSV) |
| Анализ и ветвление по условию | `branch_on_order_count` (`@task.branch`): 0 заказов → `empty_source_fail`, иначе → CSV и `analyze_joined_data` |
| Email при успешном и неуспешном завершении | `notify_success_email` (`EmailOperator`) и `email_on_failure` в `default_args` |
| Retry-политика шагов | `retries=2`, `retry_delay=30s` на шагах чтения и в `default_args` |

## Счастливый путь

1. В UI включить DAG `marketing_client_pipeline`.
2. Trigger DAG.
3. Graph: `extract_orders` → `branch_on_order_count` → `extract_delivery_csv` → `analyze_joined_data` → `notify_success_email`, все success; `empty_source_fail` skipped.
4. В MailHog письмо `[Airflow] marketing_client_pipeline: успех`.

Снято на `screenshots/02-graph-success.png`.

## Неуспешный путь

```bash
docker compose exec airflow-webserver airflow variables set simulate_empty true
```

Снова Trigger DAG. Ожидаемо:

- ветка уходит в `empty_source_fail`, задача и прогон в состоянии failed, путь CSV skipped;
- в MailHog письмо `Airflow alert: <TaskInstance: ... empty_source_fail ... [failed]>`.

Снято на `screenshots/03-graph-failure.png`. Вернуть переменную:

```bash
docker compose exec airflow-webserver airflow variables set simulate_empty false
```

## Retry

`retries=2`, `retry_delay=0:00:30` видны в коде DAG на `screenshots/06-dag-code-retry.png` и в UI: Task Instance → Details.
