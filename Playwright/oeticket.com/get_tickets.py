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


class OEticket:
    def __init__(self):
        pass

    @staticmethod
    def oe_events(
    ) -> list:
        categories = ('Freizeit', 'Gutscheine', 'Kabarett & Comedy', 'Konzerte', 'Kultur', 'Musical & Show', 'Sport')
        oe_events = []
        for category in categories:
            url = f'https://public-api.eventim.com/websearch/search/api/exploration/v2/productGroups?webId=web__oeticket-at&categories={category}&sort=Recommendation'
            response = requests.get(url)
            if response.status_code == 200:
                oe_events.extend(item for item in response.json()['productGroups'])
        return oe_events

    @staticmethod
    def oe_tickets(events: dict = None):
        for event in events['products']:
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

                logging.info(f"Navigating to {event['link']} ...")
                try:
                    page.goto(event['link'], wait_until="networkidle", timeout=60_000)
                except Exception as e:
                    logging.error(f"Navigation exception: {e} — попробуем продолжить и собрать, что есть.")

                time.sleep(2)
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                scripts = soup.find_all("script", {"type": "application/configuration"})
                for script in scripts:
                    if not script.string:
                        continue
                    raw_json = script.string.strip()
                    if raw_json.startswith('{\n"fansale"'):
                        try:
                            data = json.loads(raw_json)
                            browser.close()
                            return data
                        except json.JSONDecodeError:
                            logging.error("Не удалось распарсить JSON из <script type='application/configuration'>")
                            continue

                logging.warning("Билеты не доступны. Повторная попытка")
                try:
                    prices = page.query_selector_all(".js-tooltipster.u-cursor-default.tooltipstered")
                    if prices:
                        price_dict = {'prices': [btn.inner_text().strip() for btn in prices]}
                        logging.info('Цены на билеты найдены')
                        return price_dict
                    else:
                        logging.error("Цены на билеты не найдены")
                except Exception as e:
                    logging.error(f"Ошибка при поиске цен: {e}")

                browser.close()
                return None



def get_some_id_info(event_id = None):
    with open("oe_data.json", "r", encoding="utf-8") as f:
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
    oe_data = []
    oeTicket_events = OEticket.oe_events()
    logging.info(f"Result of getting OE events: {oeTicket_events}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(OEticket.oe_tickets, event): event
            for event in oeTicket_events[:30]
        }

        for future in as_completed(futures):
            event = futures[future]
            try:
                oe_tickets = future.result()
                if oe_tickets is None:
                    continue
                if 'prices' in oe_tickets.keys():
                    for price in oe_tickets['prices']:
                        clean = re.sub(r"[^\d,\.]", "", price)
                        clean = clean.replace(",", ".")
                        value = float(clean)
                        oe_data.append({
                            "event_id": event['productGroupId'],
                            "source": "oeticket",
                            "ticket_id": None,
                            "section": None,
                            "row": None,
                            "price_with_fees": f"€ {value + 1.5:.2f}",
                            "price": f"{price[:-1]}",
                            "quantity": None,
                            "url": event['link'],
                            "multi_tickets": str(len(oe_tickets['prices']))
                        })
                else:
                    for _, ticket in oe_tickets['price'].items():
                        oe_data.append({
                                "event_id": event['productGroupId'],
                                "source": "oeticket",
                                "ticket_id": ticket['priceCategoryId'],
                                "section": None,
                                "row": ticket['rowRuleApplicable'],
                                "price_with_fees": f"€ {ticket['defaultPriceAsInt']/1000 + 1,5}",
                                "price": f"€ {ticket['defaultPriceAsInt']/1000}",
                                "quantity": ticket['maxAmount'],
                                "url": event['link'],
                                "multi_tickets": str(len(oe_tickets['price']))
                            })

            except Exception as e:
                logging.error(f"[{event['id']}] Ошибка в future: {e}")

        with open("oe_data.json", "w", encoding="utf-8") as f:
            json.dump(oe_data, f, ensure_ascii=False, indent=2)

        logging.info("All data from sympla collected to oe_data.json")


if __name__ == "__main__":
    # Можно установить парсинг данных раз в несколько часов
    main()
    print(len(get_some_id_info()))
