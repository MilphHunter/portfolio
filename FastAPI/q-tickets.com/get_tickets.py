import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

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


class Qtickets:
    def __init__(self):
        pass

    @staticmethod
    def q_events():
        url = "https://q-tickets.com/Movie/BookTickets"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            page.goto(url, wait_until="domcontentloaded")

            time.sleep(3)

            html = page.content()

            soup = BeautifulSoup(html, "html.parser")

            details_divs = soup.find_all("div", class_="tile__details")

            events = []
            for div in details_divs:
                event = {}
                title_div = div.find("div", class_="tile__title")
                if title_div:
                    event['title'] = title_div.get_text(strip=True)
                    try:
                        link = title_div.find("a", class_="hover-btn")["href"]
                        event['link'] = 'https://q-tickets.com' + title_div.find("a", class_="hover-btn")[
                            "href"] if link else None
                        link = event.get('link')
                        part = link.split("/")[4] if link else None
                        event['id'] = part
                    except Exception as e:
                        event['link'] = None
                        event['id'] = None
                    events.append(event)

            browser.close()
            return events

    @staticmethod
    def q_tickets(event_id: int = 44896):
        url = f"https://q-tickets.com/MovieDetailsList/{event_id}"

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            page.goto(url, wait_until="domcontentloaded")

            # Follow Us
            i = 0
            while i < 10:
                try:
                    close_button_selector = ".close.modalClose"
                    page.wait_for_selector(close_button_selector, timeout=1000)
                    page.click(close_button_selector)
                    break
                except Exception:
                    logging.error("Кнопка закрытия модального окна не найдена, пробуем ещё...")
                    i += 1
                    time.sleep(1)
            if i >= 9:
                browser.close()
                return None
            # Сеанс
            try:
                buttons = page.query_selector_all(".getshowId.btn.btn-green")
                if buttons:
                    buttons[-1].click()
                    logging.info("Кликнули на последнюю кнопку 'getshowId btn btn-green'")
                    time.sleep(2)
                else:
                    logging.info("Кнопки 'getshowId btn btn-green' не найдены")
                    browser.close()
                    return None
            except Exception as e:
                logging.error(f"Ошибка при поиске кнопок: {e}")

            # MIDNIGHT SESSION
            try:
                midnight_selector = "a#latemidok"
                page.wait_for_selector(midnight_selector, timeout=1000)
                page.click(midnight_selector)
            except Exception as e:
                pass

            # Disclaimer
            try:
                close_button_selector = ".btn.btn-purple.p-8-40"
                page.wait_for_selector(close_button_selector, timeout=1000)
                page.click(close_button_selector)
                time.sleep(1)
            except Exception:
                logging.error("Кнопка закрытия модального окна не найдена, пробуем ещё...")
                time.sleep(1)

            # Vouchers
            try:
                midnight_selector = "a#okvip"
                page.wait_for_selector(midnight_selector, timeout=1000)
                page.click(midnight_selector)
                browser.close()
                return None
            except Exception as e:
                pass
            # How Many Seats?
            i = 0
            while i < 10:
                try:
                    close_button_selector = ".btn.btn-purple.my-15"
                    try:
                        page.wait_for_selector(close_button_selector, timeout=1000)
                        page.click(close_button_selector)
                        break
                    except Exception as e:
                        try:
                            midnight_selector = "a#proceed-Qty"
                            page.wait_for_selector(midnight_selector, timeout=1000)
                            page.click(midnight_selector)
                            break
                        except Exception as e:
                            pass
                except Exception:
                    logging.error("Кнопка закрытия модального окна не найдена, пробуем ещё...")
                    i += 1
                    time.sleep(1)
            if i >= 9:
                browser.close()
                return None

            # Choose a place
            try:
                buttons = page.query_selector_all(".block.available")
                if buttons:
                    buttons[-1].click()
                    logging.info("Кликнули на последнюю кнопку 'getshowId btn btn-green'")
                    time.sleep(1)
                    enter_btn = '.btn.btn-purple.resp-btn-sl'
                    page.click(enter_btn)
                else:
                    logging.info("Кнопки 'getshowId btn btn-green' не найдены")
            except Exception as e:
                logging.error(f"Ошибка при поиске кнопок: {e}")

            # Collect price
            while True:
                try:
                    rows = page.query_selector_all("table.payment-table tbody tr")

                    if not rows:
                        continue
                    data = {}
                    for row in rows:
                        cols = row.query_selector_all("td")
                        if len(cols) == 2:
                            key = cols[0].inner_text().strip()
                            value = cols[1].inner_text().strip()
                            data[key] = value
                    break
                except Exception:
                    time.sleep(1)

            browser.close()
            return data


def get_some_id_info(event_id=None):
    with open("qTicket_data.json", "r", encoding="utf-8") as f:
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
    qTicket_events = Qtickets.q_events()
    qTicket_events = [event for event in qTicket_events if event['id'] is not None]
    logging.info(f"Result of getting Qticket events: {qTicket_events}")

    qTicket_data = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(Qtickets.q_tickets, event["id"]): event
            for event in qTicket_events
        }

        for future in as_completed(futures):
            event = futures[future]
            try:
                qTicket_tickets = future.result()
                if not qTicket_tickets:
                    logging.error(f"[{event['id']}] Ошибка получения билетов")
                    continue

                qTicket_data.append({
                    "event_id": event["id"],
                    "source": "qTicket",
                    "ticket_id": None,
                    "section": None,
                    "row": None,
                    "price_with_fees": f"{qTicket_tickets['Grand Total']}",
                    "price": f"{qTicket_tickets['Total Price']}",
                    "quantity": None,
                    "url": event["link"],
                    "multi_tickets": None
                })

            except Exception as e:
                logging.error(f"[{event['id']}] Ошибка в future: {e}")

    with open("qTicket_data.json", "w", encoding="utf-8") as f:
        json.dump(qTicket_data, f, ensure_ascii=False, indent=2)

    logging.info("All data from sympla collected to qTicket_data.json")


if __name__ == "__main__":
    # Можно установить парсинг данных раз в несколько часов
    # main()
    print(len(get_some_id_info()))
