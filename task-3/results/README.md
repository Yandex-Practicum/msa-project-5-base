# Task 3. Distributed Scheduling — k8s CronJob

Ежедневная аналитическая выгрузка таблицы `shipments` в CSV. Расписание: **20:00** (`0 20 * * *`, Europe/Moscow).

## Состав

- `Dockerfile` — образ Python-экспорта
- `app/export.py` — чтение одной таблицы Postgres → CSV
- `k8s/postgres.yaml` — Namespace, Secret, Postgres с тестовыми данными, PVC
- `k8s/cronjob.yaml` — CronJob с cron-конфигурацией
- `k8s/verify-output.yaml` — вспомогательный под: показать содержимое выгруженного файла
- `screenshots/` — демонстрация работы в MiniKube

Экспортируемая таблица задаётся переменной `EXPORT_TABLE` (разрешены `shipments`, `shipment_events`, `drivers`, `vehicles`, `clients`).

## MiniKube

```bash
minikube start
cd task-3/results
docker build -t shipment-export:local .
minikube image load shipment-export:local
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/cronjob.yaml
kubectl -n analytics-export rollout status deploy/postgres
```

Расписание 20:00 на демо не ждут — разовый прогон из того же CronJob:

```bash
kubectl -n analytics-export create job shipment-export-manual --from=cronjob/shipment-analytics-export
kubectl -n analytics-export wait --for=condition=complete job/shipment-export-manual --timeout=120s
kubectl -n analytics-export get cronjob,job,pods -o wide
kubectl -n analytics-export logs job/shipment-export-manual
```

Проверить сам файл в томе:

```bash
kubectl apply -f k8s/verify-output.yaml
kubectl -n analytics-export logs pod/verify-output
```

Фактический результат прогона: `Exported 5 rows to /data/shipments_2026-08-16.csv`, в файле заголовок и 5 строк.
