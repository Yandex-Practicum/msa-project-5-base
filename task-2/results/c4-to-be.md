# Task 2. C4 To Be — выгрузка B2B-прайс-листов

Исходный `.drawio`: [c4-to-be.drawio](c4-to-be.drawio).

## System Context

```mermaid
C4Context
    title Контекст системы выгрузки B2B-прайс-листов
    Person(b2b, "B2B-клиент", "Забирает кастомный прайс-лист")
    Person(ops, "Дежурный DevOps", "Смотрит логи и алерты Job")
    System(shop, "Интернет-магазин", "Микросервисы каталога и цен в Kubernetes")
    System_Ext(storage, "Объектное хранилище", "CSV/XLS прайс-листы")
    Rel(shop, storage, "Пишет прайс-листы по расписанию 06:00")
    Rel(b2b, storage, "Скачивает свой прайс-лист")
    Rel(ops, shop, "Наблюдает CronJob")
```

## Container

```mermaid
C4Container
    title Контейнеры To Be
    Person(b2b, "B2B-клиент")
    System_Boundary(k8s, "Kubernetes") {
        ContainerDb(pg, "БД прайс-листов", "PostgreSQL", "products, categories, clients, client_prices")
        Container(cron, "Выгрузка прайс-листа", "k8s CronJob", "Ежедневно в 06:00: JOIN таблиц → CSV/XLS")
    }
    Container_Ext(bucket, "Объектное хранилище", "S3/GCS", "Кастомные прайс-листы")
    Rel(cron, pg, "SQL JOIN", "TCP 5432")
    Rel(cron, bucket, "Запись файлов", "HTTPS")
    Rel(b2b, bucket, "Скачивание прайс-листа")
```

Единственный новый контейнер внутри кластера — CronJob. Оркестратор Airflow и Spark-кластер не появляются.
