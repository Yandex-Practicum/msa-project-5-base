# Обоснование метрик для мониторинга системы обработки складских отчётов

## 1. Метрики уровня приложения

### 1.1 Backend API (WildFly)

| Метрика | Обоснование |
|---------|-------------|
| `http_server_requests_seconds_count` | Количество HTTP-запросов для отслеживания нагрузки на API |
| `http_server_requests_seconds_sum` | Время обработки запросов (latency) — выявление медленных эндпоинтов |
| `http_server_requests_seconds_count{status="5xx"}` | Ошибки сервера — критичный показатель стабильности |
| `jvm_memory_used_bytes` | Использование памяти JVM — предотвращение OOM |
| `jvm_threads_live_threads` | Количество активных потоков — выявление утечек потоков |
| `wildfly_datasource_pool_available` | Доступные соединения с БД — предотвращение исчерпания пула |

### 1.2 Spring Batch Service

| Метрика | Обоснование |
|---------|-------------|
| `spring_batch_job_duration_seconds` | Время выполнения batch-задач — контроль SLA обработки файлов |
| `spring_batch_job_status` | Статус выполнения (успех/ошибка) — мониторинг корректности ETL |
| `spring_batch_records_processed_total` | Количество обработанных записей — валидация полноты обработки |
| `spring_batch_skip_count_total` | Количество пропущенных записей — контроль качества данных |
| `batch_job_queue_size` | Размер очереди задач — выявление backlog |

### 1.3 Web UI (Angular)

| Метрика | Обоснование |
|---------|-------------|
| `page_load_time_seconds` | Время загрузки страницы — UX мониторинг |
| `api_request_error_rate` | Процент ошибок API вызовов — качество клиент-серверного взаимодействия |
| `active_users_count` | Количество активных пользователей — нагрузка на систему |

## 2. Метрики уровня баз данных

### 2.1 PostgreSQL

| Метрика | Обоснование |
|---------|-------------|
| `postgres_connections_active` | Активные подключения — нагрузка на БД |
| `postgres_query_duration_seconds` | Время выполнения запросов — выявление медленных query |
| `postgres_transactions_per_second` | Количество транзакций — интенсивность записи |
| `postgres_deadlocks_total` | Количество deadlock'ов — проблемы конкурентного доступа |
| `postgres_replication_lag_seconds` | Задержка репликации (если есть) — актуальность данных |

## 3. Метрики уровня инфраструктуры

### 3.1 Google Cloud Storage

| Метрика | Обоснование |
|---------|-------------|
| `gcs_objects_total` | Количество объектов — контроль роста хранилища |
| `gcs_bucket_size_bytes` | Размер хранилища — планирование capacity |
| `gcs_api_request_errors_total` | Ошибки API GCS — проблемы доступа к файлам |

### 3.2 System Metrics (все сервера)

| Метрика | Обоснование |
|---------|-------------|
| `node_cpu_seconds_total` | Загрузка CPU — ресурсы серверов |
| `node_memory_MemAvailable_bytes` | Доступная память — риск нехватки RAM |
| `node_filesystem_avail_bytes` | Свободное место на диске — риск переполнения |
| `node_network_receive_bytes_total` | Сетевой трафик — нагрузка на сеть |

## 4. Метрики уровня логов (ELK)

### 4.1 Логи приложений

| Поле/метрика | Обоснование |
|--------------|-------------|
| `log.level: ERROR` | Количество ошибок — базовый показатель здоровья |
| `log.level: WARN` | Предупреждения — раннее обнаружение проблем |
| `error.exception_type` | Типы исключений — классификация ошибок |
| `batch.job.id` | Идентификатор job — трассировка выполнения |
| `response.time.ms` | Время ответа из логов — дополнение к метрикам |

## 5. Бизнес-метрики

| Метрика | Обоснование |
|---------|-------------|
| `files_uploaded_total` | Количество загруженных файлов — активность пользователей |
| `files_processed_total` | Количество обработанных файлов — throughput системы |
| `processing_time_p95_seconds` | 95-й перцентиль времени обработки — SLA для пользователей |
| `data_quality_error_rate` | Процент записей с ошибками валидации — качество данных |

## 6. Пороговые значения для алертов

### Критические алерты (P1)
- `http_server_requests_seconds_count{status="5xx"} > 10` за 5 мин
- `jvm_memory_used_bytes / jvm_memory_max_bytes > 0.9`
- `postgres_connections_active > 80% от max_connections`
- `spring_batch_job_status = "FAILED"`
- `node_filesystem_avail_bytes < 10%`

### Предупреждения (P2)
- `http_server_requests_seconds_sum > 2s` (среднее время ответа)
- `spring_batch_job_duration_seconds > 30min`
- `postgres_query_duration_seconds > 5s`
- `active_users_count = 0` в рабочее время

## 7. Обоснование выбора стека

### Prometheus
- **Pull-модель** удобна для динамической инфраструктуры
- **Multidimensional data model** (labels) позволяет гибко агрегировать метрики
- **PromQL** мощный язык запросов для анализа
- **Native интеграция** со Spring Boot Actuator и Micrometer

### ELK Stack
- **Централизованное логирование** всех компонентов системы
- **Full-text search** для расследования инцидентов
- **Корреляция логов** между web_ui, backend и batch
- **Kibana** для ad-hoc анализа без написания кода

### Grafana
- **Единая панель** для метрик (Prometheus) и логов (Elasticsearch)
- **Alerting** с интеграцией в Slack/Telegram/Email
- **Annotations** для标记 событий (деплои, инциденты)
- **Rich visualization** для отчётов руководству

## 8. Cardinality метрик

Для предотвращения проблем с high cardinality в Prometheus:

**Хорошо:**
- `http_requests_total{method="GET", status="200", endpoint="/api/files"}`

**Плохо (высокая кардинальность):**
- `http_requests_total{user_id="12345", session_id="abc..."}`

**Рекомендация:** Не использовать user-specific labels в метриках, хранить такую информацию только в логах.

## 9. Retention policy

| Тип данных | Хранение | Обоснование |
|------------|----------|-------------|
| Prometheus metrics | 15 дней | Оперативный мониторинг и расследование |
| Elasticsearch logs | 30 дней | Compliance и аудит |
| Grafana dashboards | Бессрочно | История производительности |
| Alert history | 90 дней | Анализ инцидентов |

## 10. Заключение

Выбранные метрики покрывают:
- ✅ **Техническое здоровье** системы (CPU, memory, errors)
- ✅ **Производительность** (latency, throughput)
- ✅ **Бизнес-логику** (обработанные файлы, качество данных)
- ✅ **Пользовательский опыт** (время отклика, доступность)

Это позволяет:
1. Быстро обнаруживать инциденты (MTTD < 5 мин)
2. Оперативно диагностировать проблемы (MTTR < 30 мин)
3. Планировать масштабирование на основе трендов
4. Гарантировать SLA для бизнес-процессов