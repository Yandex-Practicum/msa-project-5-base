"""POC: маркетинговый пайплайн объединения заказов и статусов доставок."""

from __future__ import annotations

import csv
import logging
import os
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.exceptions import AirflowFailException
from airflow.models import Variable
from airflow.operators.email import EmailOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.trigger_rule import TriggerRule

logger = logging.getLogger(__name__)

RETRY_ARGS = {
    "retries": 2,
    "retry_delay": timedelta(seconds=30),
}

DEFAULT_ARGS = {
    "owner": "marketing-data",
    "email": ["marketing@local.dev"],
    "email_on_failure": True,
    "email_on_retry": True,
    **RETRY_ARGS,
}


@dag(
    dag_id="marketing_client_pipeline",
    description="POC: чтение Postgres+CSV, ветвление, retry, email на успех и провал",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["task1", "poc", "marketing"],
)
def marketing_client_pipeline():
    @task(task_id="extract_orders", **RETRY_ARGS)
    def extract_orders() -> int:
        if Variable.get("simulate_empty", default_var="false").lower() == "true":
            logger.warning("simulate_empty=true: имитируем пустой источник")
            return 0

        hook = PostgresHook(postgres_conn_id="source_postgres")
        rows = hook.get_records("SELECT id, customer_id, amount, status FROM shop.orders")
        logger.info("Прочитано заказов из Postgres: %s", len(rows))
        return len(rows)

    @task.branch(task_id="branch_on_order_count")
    def branch_on_order_count(order_count: int) -> str:
        if order_count == 0:
            logger.info("Ветка: пустой источник → неуспех")
            return "empty_source_fail"
        logger.info("Ветка: есть данные → обработка CSV")
        return "extract_delivery_csv"

    @task(task_id="extract_delivery_csv", **RETRY_ARGS)
    def extract_delivery_csv() -> int:
        path = os.environ.get("SOURCE_CSV_PATH", "/opt/airflow/data/delivery_statuses.csv")
        with open(path, newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        logger.info("Прочитано статусов доставки из CSV: %s", len(rows))
        return len(rows)

    @task(task_id="analyze_joined_data")
    def analyze_joined_data(order_count: int, csv_count: int) -> str:
        logger.info("Анализ: orders=%s, delivery_statuses=%s", order_count, csv_count)
        if csv_count == 0:
            raise AirflowFailException("CSV со статусами доставок пуст")
        return f"joined {order_count} orders with {csv_count} delivery rows"

    @task(task_id="empty_source_fail")
    def empty_source_fail() -> None:
        raise AirflowFailException("Источник заказов пуст: прогон пайплайна неуспешен")

    notify_success = EmailOperator(
        task_id="notify_success_email",
        to="marketing@local.dev",
        subject="[Airflow] marketing_client_pipeline: успех",
        html_content="<p>Прогон пайплайна завершился успешно: заказы и статусы доставок обработаны.</p>",
        trigger_rule=TriggerRule.ALL_SUCCESS,
    )

    order_count = extract_orders()
    branch = branch_on_order_count(order_count)
    csv_count = extract_delivery_csv()
    analyzed = analyze_joined_data(order_count, csv_count)
    failed = empty_source_fail()

    branch >> [csv_count, failed]
    csv_count >> analyzed >> notify_success


marketing_client_pipeline()
