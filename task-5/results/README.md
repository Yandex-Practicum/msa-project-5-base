# Обоснование метрик для мониторинга системы обработки складских отчётов (v2, исправленная)

## 1. Метрики уровня приложения

### 1.1 Backend API (WildFly / Spring Boot)

| Метрика / Гистограмма | Обоснование |
| --- | --- |
| `http_server_requests_seconds_count` | Количество HTTP-запросов для подсчёта RPS через `rate()` |
| `http_server_requests_seconds_bucket` | Гистограмма Latency — для вычисления **p95 / p99** времени ответа |
| `http_server_requests_seconds_count{status=~"5.."}` | Ошибки сервера (5xx) — базовый показатель доступности |
| `jvm_memory_used_bytes` / `jvm_memory_max_bytes` | Использование Heap Memory — предупреждение риска OOM |
| `jvm_gc_pause_seconds_sum` (и `count`) | Длительность пауз Garbage Collector (Stop-The-World) |
| `jvm_threads_live_threads` | Количество активных потоков — выявление утечек потоков |
| `hikaricp_connections_pending` | Потоки, ожидающие соединение из пула — главный маркер зависания БД |
| `hikaricp_connections_timeout_total` | Таймауты получения соединения из пула |

### 1.2 Spring Batch Service

| Метрика | Обоснование |
| --- | --- |
| `spring_batch_job_duration_seconds` | Время выполнения batch-задач — контроль SLA обработки файлов |
| `spring_batch_job_status` | Статус выполнения (SUCCESS / FAILED) — мониторинг корректности ETL |
| `spring_batch_records_processed_total` | Количество обработанных записей — полнота обработки |
| `spring_batch_skip_count_total` | Пропущенные записи — качество входных данных |
| `spring_batch_item_read_seconds_errors` | Ошибки чтения/парсинга файлов (CSV/XLSX) |
| `spring_batch_item_write_seconds_errors` |  Ошибки записи пачки данных в БД |
| `batch_job_queue_size` | Размер очереди задач — выявление backlog |

### 1.3 Web UI (Angular)

| Метрика | Обоснование |
| --- | --- |
| `page_load_time_seconds` | Время загрузки страниц (RUM / Core Web Vitals) |
| `api_request_error_rate` | Процент ошибок API-вызовов на клиенте |
| `active_users_count` | Количество активных сессий (для отслеживания нагрузки) |

---

## 2. Метрики уровня баз данных (PostgreSQL)

| Метрика | Обоснование |
| --- | --- |
| `postgres_connections_active` | Активные подключения — нагрузка на БД |
| `postgres_query_duration_seconds` | Время выполнения запросов (медленные query) |
| `postgres_transactions_per_second` | Интенсивность записи/чтения (TPS) |
| `postgres_deadlocks_total` | Количество deadlock'ов — проблемы конкурентного доступа |
| `pg_stat_database_xact_rollback` | Откаченные транзакции — признак сбоев в бизнес-логике/БД |
| `pg_statio_user_tables_heap_blks_hit` | Cache Hit Ratio — эффективное использование shared_buffers |
| `postgres_replication_lag_seconds` | Задержка репликации (если есть standby) |

---

## 3. Метрики уровня инфраструктуры

### 3.1 Google Cloud Storage

| Метрика | Обоснование |
| --- | --- |
| `gcs_bucket_size_bytes` | Общий размер хранилища — планирование capacity |
| `gcs_api_request_errors_total` | Ошибки API GCS — проблемы доступа к файлам/сеть |

### 3.2 System Metrics (Node Exporter)

| Метрика | Обоснование |
| --- | --- |
| `node_cpu_seconds_total` | Загрузка CPU по режимам |
| `node_memory_MemAvailable_bytes` | Доступная RAM (без сваливания в swap) |
| `node_filesystem_avail_bytes` | Свободное место на дисках |
| `node_network_receive_bytes_total` | Сетевой трафик (входящий/исходящий) |

---

## 4. Метрики уровня логов (ELK)

| Поле / Показатель | Обоснование |
| --- | --- |
| `log.level: ERROR` | Ключевые ошибки приложений и стактрейсы |
| `log.level: WARN` | Предупреждения (включая медленные запросы > 2s) |
| `error.exception_type` | Классификация причин падений |
| `batch.job.id` / `trace_id` | Сквозная трассировка конкретной задачи от UI до БД |

---

## 5. Бизнес-метрики

| Метрика | Обоснование |
| --- | --- |
| `files_uploaded_total` | Загружено файлов пользователями |
| `files_processed_total` | Успешно обработано файлов системой |
| `processing_time_p95_seconds` | SLA обработки 95% файлов от момента загрузки до импорта |
| `data_quality_error_rate` | Процент невалидных строк в складских отчётах |

---

## 6. Пороговые значения для алертов (PromQL)

### Критические алерты (P1)

* **5xx Errors:** `rate(http_server_requests_seconds_count{status=~"5.."}[5m]) > 0.05` *(более 5% ошибок за 5 мин)*
* **JVM Heap OOM Risk:** `jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes{area="heap"} > 0.9`
* **HikariCP Exhaustion:** `hikaricp_connections_pending > 5` в течение 1 мин
* **Postgres Connections:** `postgres_connections_active / pg_settings_max_connections > 0.85`
* **Batch Execution Failed:** `spring_batch_job_status{status="FAILED"} > 0`
* **Disk Space Low:** `node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1`

### Предупреждения (P2)

* **High Latency (p95):** `histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket[5m])) by (le)) > 2.0`
* **Long GC Pauses:** `rate(jvm_gc_pause_seconds_sum[5m]) > 0.2` *(более 200ms пауз в секунду)*
* **Spring Batch Long Duration:** `spring_batch_job_duration_seconds > 1800` *(задача идёт > 30 мин)*
* **Postgres Slow Queries:** `postgres_query_duration_seconds > 5`

---

## 7. Заключение

Выбранные метрики покрывают:
- **Техническое здоровье** системы (CPU, memory, errors)
- **Производительность** (latency, throughput)
- **Бизнес-логику** (обработанные файлы, качество данных)
- **Пользовательский опыт** (время отклика, доступность)

Это позволяет:
1. Быстро обнаруживать инциденты (MTTD < 5 мин)
2. Оперативно диагностировать проблемы (MTTR < 30 мин)
3. Планировать масштабирование на основе трендов
4. Гарантировать SLA для бизнес-процессов