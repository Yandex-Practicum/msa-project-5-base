#!/usr/bin/env python3
"""Export one analytics table from PostgreSQL to CSV."""

from __future__ import annotations

import csv
import logging
import os
import sys
from datetime import datetime, timezone

import psycopg2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("shipment-export")

ALLOWED_TABLES = {
    "shipments",
    "shipment_events",
    "drivers",
    "vehicles",
    "clients",
}
TABLE = os.environ.get("EXPORT_TABLE", "shipments")
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/data")
DSN = os.environ["DATABASE_URL"]

if TABLE not in ALLOWED_TABLES:
    raise SystemExit(f"EXPORT_TABLE must be one of {sorted(ALLOWED_TABLES)}")


def main() -> int:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(OUTPUT_DIR, f"{TABLE}_{stamp}.csv")

    logger.info("Connecting to database, table=%s", TABLE)
    with psycopg2.connect(DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {TABLE}")
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)

    logger.info("Exported %s rows to %s", len(rows), path)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logger.exception("Analytics export failed")
        sys.exit(1)
