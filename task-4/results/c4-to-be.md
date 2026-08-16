# Task 4. C4 To Be — Spring Batch

Исходный Draw.io: [c4-to-be.drawio](c4-to-be.drawio).

```mermaid
C4Container
    title TradeWare To Be: приёмка отчёта и Spring Batch
    Person(wh, "Сотрудник склада", "Сдаёт складской отчёт в конце смены")
    Container(web, "Веб-интерфейс ERP", "Angular, WebSocket", "Загрузка CSV, статус приёмки и прогона")
    System_Boundary(backend, "GCP") {
        Container(monolith, "Монолит ERP", "WildFly, Java 11", "Приёмка файла, ошибка формата, уведомление по WebSocket")
        Container(batch, "Обработка складского отчёта", "Spring Boot, Spring Batch", "Прогон: валидация, обогащение, запись остатков")
        ContainerDb(stock, "БД остатков", "PostgreSQL", "Складские остатки (в задании: БД номенклатуры)")
        ContainerDb(ref, "Справочник товаров", "PostgreSQL", "Характеристики и промоакции")
        ContainerDb(jobrepo, "Job repository", "PostgreSQL", "Состояние прогонов Spring Batch")
        Container(gcs, "Файловое хранилище", "GCS", "Принятые CSV")
    }
    Rel(wh, web, "загружает CSV")
    Rel(web, monolith, "REST JSON/HTTP")
    Rel(monolith, gcs, "сохраняет принятый отчёт")
    Rel(monolith, batch, "событие «отчёт принят» / уведомление о завершении")
    Rel(batch, gcs, "читает CSV")
    Rel(batch, ref, "обогащение SQL")
    Rel(batch, stock, "запись остатков SQL")
    Rel(batch, jobrepo, "чекпоинты job")
    Rel(monolith, web, "WebSocket: принято / обработано / ошибка прогона")
```

WildFly больше не пишет остатки построчно из HTTP. Прогон живёт в сервисе рядом — шаг к выносу из монолита.
