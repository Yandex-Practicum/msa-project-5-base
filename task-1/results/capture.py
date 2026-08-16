"""Скриншоты Airflow и MailHog для демонстрации POC.

Использование: python capture.py <run_id> <имя-файла.png>
Граф снимается для конкретного прогона, иначе Airflow показывает граф без статусов.
"""

import sys
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "screenshots"
OUT.mkdir(exist_ok=True)
BASE = "http://127.0.0.1:8088"


def main(run_id: str, filename: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 950})
        page.set_default_timeout(60000)

        page.goto(f"{BASE}/login/", wait_until="domcontentloaded")
        page.locator("input[name='username']").fill("admin")
        page.locator("input[name='password']").fill("admin")
        page.locator("button[type='submit'], input[type='submit']").first.click()
        page.wait_for_timeout(3000)

        url = (
            f"{BASE}/dags/marketing_client_pipeline/grid"
            f"?tab=graph&dag_run_id={quote(run_id, safe='')}"
        )
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        page.screenshot(path=OUT / filename, full_page=True)

        page.goto("http://127.0.0.1:8025/", wait_until="domcontentloaded")
        page.wait_for_timeout(2500)
        page.screenshot(path=OUT / "05-mailhog-inbox.png", full_page=True)

        browser.close()
    print("saved", filename)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
