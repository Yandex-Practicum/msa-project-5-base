# Скриншоты POC

Сняты с локально развёрнутого Airflow 2.9.3 (Docker Compose) и MailHog.

| Файл | Что показывает |
|---|---|
| `00-login.png` | Локальный Airflow доступен на http://localhost:8088 |
| `01-home.png` | DAG `marketing_client_pipeline` в списке, включён |
| `01-dag-runs.png` | Сводка прогонов: 4 всего, 2 success, 2 failed |
| `02-graph-success.png` | **Успешный прогон**: Postgres → ветка → CSV → анализ → `notify_success_email` (success), `empty_source_fail` skipped |
| `03-graph-failure.png` | **Неуспешный прогон**: ветка ушла в `empty_source_fail` (failed), путь CSV skipped |
| `04-dag-details.png` | Детали DAG: 6 задач, `@task.branch` = 1, EmailOperator = 1 |
| `05-mailhog-inbox.png` | Письма: 2 об успехе (`EmailOperator`) и 2 об ошибке (`email_on_failure`) |
| `06-dag-code-retry.png` | Код DAG в UI: `retries=2`, `retry_delay=30s`, `email_on_failure` |

Скриншоты сняты скриптом `../capture.py` (Playwright), граф — для конкретного `dag_run_id`.
