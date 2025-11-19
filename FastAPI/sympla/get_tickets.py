import random
import re
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
LOCALE = "en-US"
VIEWPORT = {"width": 1366, "height": 768}
EXTRA_HTTP_HEADERS = {"Accept-Language": "en-US,en;q=0.9"}


class Sympla:
    def __init__(self):
        pass

    @staticmethod
    def sympla_events(
            page: int = 1,
            target_url: str = (
                    "https://www.sympla.com.br/api/discovery-bff/search/category-type?"
                    "field_sort=&location_score=day-trending-score"
                    "&type=normal&events_ids=&range=&service=%2Fv4%2Fsearch%2Fquery&page=1"
            )
    ):
        target_url = target_url.replace("&page=1", f'&page={str(page)}')
        with sync_playwright() as p:
            launch_kwargs = {"headless": False}
            logging.info("Launching browser...")
            browser = p.chromium.launch(**launch_kwargs)

            context_kwargs = {
                "user_agent": USER_AGENT,
                "locale": LOCALE,
                "viewport": VIEWPORT,
                "extra_http_headers": EXTRA_HTTP_HEADERS,
            }

            context = browser.new_context(**context_kwargs)
            page = context.new_page()
            logging.info(f"Navigating to {target_url} ...")
            try:
                page.goto(target_url, wait_until="networkidle", timeout=60_000)
            except Exception as e:
                logging.error(f"Navigation exception: {e} — попробуем продолжить и собрать, что есть.")

            try:
                html = page.content().split("<pre>")[1].split("</pre>")[0]
                logging.info("Page HTML parsed successfully")
                html = json.loads(html)
                return html
            except Exception as e:
                logging.error(f"Не удалось обработать HTML: {e}")

            context.close()
            browser.close()
            logging.info("Browser closed. Done.")

    @staticmethod
    def sympla_tickets(
            event_id: int = 2858006,
            target_url: str = f"https://event-page.svc.sympla.com.br/api/event-bff/purchase/event/event_id/tickets"
    ):
        target_url = target_url.replace("event_id", str(event_id))
        with sync_playwright() as p:
            launch_kwargs = {"headless": False}
            logging.info("Launching browser...")
            browser = p.chromium.launch(**launch_kwargs)

            context_kwargs = {
                "user_agent": USER_AGENT,
                "locale": LOCALE,
                "viewport": VIEWPORT,
                "extra_http_headers": EXTRA_HTTP_HEADERS,
            }

            context = browser.new_context(**context_kwargs)
            page = context.new_page()

            def block_resources(route, request):
                if request.resource_type in ["image", "media", "font", "stylesheet"]:
                    route.abort()
                else:
                    route.continue_()

            page.route("**/*", block_resources)

            logging.info(f"Navigating to {target_url} ...")
            try:
                page.goto(target_url, wait_until="networkidle", timeout=60_000)
            except Exception as e:
                logging.error(f"Navigation exception: {e} — попробуем продолжить и собрать, что есть.")

            try:
                html = page.content().split("<pre>")[1].split("</pre>")[0]
                logging.info("Page HTML parsed successfully")
                html = json.loads(html)
                return html
            except Exception as e:
                logging.error(f"Не удалось обработать HTML: {e}")

            context.close()
            browser.close()
            logging.info("Browser closed. Done.")


def get_some_id_info(event_id = None):
    with open("sympla_data.json", "r", encoding="utf-8") as f:
        q_tickets_data = json.load(f)
    if event_id is not None:
        for item in q_tickets_data:
            if item.get("event_id") == str(event_id):
                return item
        else:
            return "id с таким элементом не обнаружено"
    else:
        return q_tickets_data


def main():
    sympla_data = []
    for i in range(10):
        sympla_events = Sympla.sympla_events(page=i+1)
        logging.info(f"Result of getting sympla events: {sympla_events}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(Sympla.sympla_tickets, event["id"]): event
                for event in sympla_events["data"]
            }

            for future in as_completed(futures):
                event = futures[future]
                try:
                    sympla_tickets = future.result()
                    if not sympla_tickets or isinstance(sympla_tickets, dict) and "data" not in sympla_tickets:
                        logging.error(f"[{event['id']}] Ошибка получения билетов")
                        continue

                    for ticket in sympla_tickets:
                        sympla_data.append({
                            "event_id": event["id"],
                            "source": "sympla",
                            "ticket_id": ticket["id"],
                            "section": None,
                            "row": None,
                            "price_with_fees": f"R$ {ticket['netValueMonetary']['decimal']}",
                            "price": f"R$ {ticket['salePriceMonetary']['decimal']}",
                            "quantity": ticket["maxQty"],
                            "url": event["url"],
                            "multi_tickets": str(len(sympla_tickets))
                        })

                except Exception as e:
                    logging.error(f"[{event['id']}] Ошибка в future: {e}")

    with open("sympla_data.json", "w", encoding="utf-8") as f:
        json.dump(sympla_data, f, ensure_ascii=False, indent=2)

    logging.info("All data from sympla collected to sympla_data.json")


if __name__ == "__main__":
    # Можно установить парсинг данных раз в несколько часов
    # main()
    print(len(get_some_id_info()))
