# Демонстрация работы k8s CronJob в MiniKube

| Файл | Что показывает |
|---|---|
| `minikube-cronjob-job.png` | CronJob `0 20 * * *` (Europe/Moscow), Job `Complete 1/1`, логи экспорта, содержимое выгруженного CSV |
| `kubectl-get.txt` | `kubectl get cronjob,job,pods -o wide` |
| `job-logs.txt` | `Exported 5 rows to /data/shipments_2026-08-16.csv` |
| `exported-csv.txt` | Содержимое файла в томе: заголовок и 5 строк `shipments` |

Изображение отрисовано из живого вывода `kubectl`, текстовые файлы — тот же вывод без обработки.
