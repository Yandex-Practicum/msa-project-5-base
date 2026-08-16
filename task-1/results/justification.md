# Task 1. Обоснование решения для пакетной обработки данных

## Выбор: Apache Airflow

Маркетинговый пайплайн собирает данные клиента из файлового хранилища CSV, PostgreSQL (заказы и платежи), расширенного профиля пользователя и Kafka (цепочка событий изменения заказа). Один прогон — порядка миллиона записей. Нужны гибкий граф шагов, ветвление, интеграция с BigQuery, Redshift, Kafka и Spark, встроенный мониторинг и оповещения.

**Apache Airflow** закрывает этот набор без самодельного оркестратора. Альтернативы хуже стыкуются с чеклистом задания:

| Вариант | Почему не выбран |
|---|---|
| Spring Batch | Сильный ETL внутри JVM, но нет графа с event-triggers, Kafka/Spark/BigQuery-операторов и UI пайплайна из коробки |
| Prefect / Dagster | Современные оркестраторы, но ревью и дальнейшая эксплуатация в компании проще опереть на Airflow: больше готовых провайдеров и облачных managed-сервисов |
| Spark как оркестратор | Движок расчёта, не планировщик пайплайна. Его подключаем *шагом* Airflow, а не вместо него |
| K8s CronJob | Хватает на один скрипт по расписанию (это Task 2 и Task 3), не на ветвящийся пайплайн с датчиками и алертами |

Ниже — ответы на вопросы задания.

## Интеграция с BigQuery, Redshift, Kafka и Spark

Готовые пакеты провайдеров ускоряют разработку: шаг пайплайна — это Operator/Hook, а не самописный клиент.

| Система | Провайдер / модуль | Что даёт из коробки |
|---|---|---|
| **BigQuery** | `apache-airflow-providers-google` | `BigQueryInsertJobOperator`, `BigQueryToGcsOperator`, хуки к GCS/BQ |
| **Redshift** | `apache-airflow-providers-amazon` | `RedshiftDataOperator`, `S3ToRedshiftOperator`, перенос S3 ↔ Redshift |
| **Kafka** | `apache-airflow-providers-apache-kafka` | `ProduceToTopicOperator`, `ConsumeFromTopicOperator`, сенсор новых сообщений |
| **Spark** | `apache-airflow-providers-apache-spark` | `SparkSubmitOperator`, запуск job на standalone/YARN/K8s |

Локальный POC эти облачные системы не поднимает: для скринов достаточно Postgres + CSV. В облаке те же DAG-файлы получают connection'ы через секрет-стор Composer/MWAA.

## Ветвление, условные операторы, event-triggers

Да.

- **Ветвление** — `BranchPythonOperator` / `@task.branch`. В POC: если заказов 0, идём в `empty_source_fail`, иначе — в чтение CSV.
- **Условия** — `ShortCircuitOperator`, `AirflowSkipException`, `trigger_rule` (`all_success`, `one_failed`, `none_failed_min_one_success`) для развилок и fallback-веток.
- **Event-triggers** — сенсоры (`FileSensor`, `SqlSensor`, `Kafka` sensors) и Datasets (Airflow 2.4+): DAG стартует не только по cron, но по появлению файла, партиции или сообщения.

## Fallback, retry, email из коробки

Да, без самописного фреймворка.

- **Retry** — `retries` и `retry_delay` на шаге. В POC у чтения Postgres и CSV: 2 повтора с паузой 30 секунд. Есть `retry_exponential_backoff`.
- **Fallback** — отдельная ветка с `trigger_rule=one_failed` (запасной источник, деградация, ручной callback). Airflow не называет это «FallbackOperator», но паттерн штатный.
- **Email** — `email`, `email_on_failure`, `email_on_retry` в `default_args` (письмо о провале Airflow шлёт сам) и `EmailOperator` как явный шаг для письма об успехе. Отдельного `email_on_success` в Airflow нет: успех оформляется шагом-оператором в конце ветки. SMTP задаётся в конфигурации. В POC письма принимает MailHog, чтобы факт отправки было видно на скрине.

## Развёртывание в облаке

Один и тот же DAG-код уезжает в managed Airflow или в Kubernetes:

1. **Google Cloud Composer** — управляемый Airflow в GCP, родные connection'ы к BigQuery/GCS, секреты в Secret Manager.
2. **AWS MWAA** — то же для Redshift/S3/MSK.
3. **Самостоятельный Helm на GKE/EKS** — если нужен контроль версий провайдеров; executor Celery или KubernetesExecutor, чтобы прогон на ~1 млн строк масштабировался воркерами, а не одним процессом.

Локальный Docker Compose в этой папке — учебный контур с тем же DAG. Это не Composer: нет HA scheduler и облачных identity. Для сдачи курса он демонстрирует пайплайн; в компании следующий шаг — выкатить те же `dags/` в Composer.

## Что делает POC

Пайплайн `marketing_client_pipeline`:

1. Читает заказы из **PostgreSQL** (`shop.orders`).
2. Читает статусы доставок из **CSV**.
3. **Ветвится**: пустой источник → неуспех; иначе → анализ и объединение.
4. Шлёт **email** на успех (`EmailOperator` в конце ветки) и на провал (`email_on_failure` в `default_args`).
5. На шагах чтения стоит **retry-политика** (`retries=2`, `retry_delay=30s`).

Как запустить и что снято на скринах — в `README.md`.
