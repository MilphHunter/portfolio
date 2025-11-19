import datetime
import time
from tokenize import cookie_re
from django.db.models import Q

import requests

from concurrent.futures import ThreadPoolExecutor

from load_django import *
from django.utils import timezone
from parser_app.models import Event, Ticket

from zenrows import ZenRowsClient

API_KEY="b860aa033bbb92f70a7e15f55daa4fa9c6df5c84"
COUNT = 0
params = {
    "js_render": "true",
    "premium_proxy": "true",
    "proxy_country": "us",
    "wait": 10000,
    "custom_headers": 'true',
}

client = ZenRowsClient(API_KEY)

def make_headers(datadome):
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "uk,en-US;q=0.9,en;q=0.8,ru;q=0.7",
        "client-platform": "web",
        "content-type": "application/json",
        "forter-token-cookie": "ee4452942d304d4fbe24c4ecc9397b74_1759300677033__UDF43-mnts-a4_15ck_Kay3KFUZKVI%3D-4666-v2",
        "origin": "https://www.tickpick.com",
        "priority": "u=1, i",
        "referer": "https://www.tickpick.com/",
        "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "session-id": "0fkbCxy6Uml0ZWbTAsWlcRtiVwCgQCUL",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "utm-campaign": "3476091",
        "utm-content": "Online Tracking Link_656088",
        "utm-medium": "Smart Influence GmbH",
        "utm-source": "impact",
        "x-client-id": "tickpick",
        "x-datadome-clientid": datadome
    }

    return headers

def build_ticket_url(ticket: dict) -> str:
    link = "https://www.tickpick.com/checkout/?listingId={}&quantity={}&listingType={}&price={}".format(
        ticket["id"],
        ticket["q"],
        ticket["t"],
        ticket["p"],
        ticket["eid"],
        ticket["sid"],
        ticket["r"],
    )

    try:
        link += f"&dt={ticket["dt"]}"
    except KeyError:
        pass

    try:
        link += f"&dv={ticket["dv"]}"
    except KeyError:
        pass

    try:
        link += f"&e={ticket["e"]}"
    except KeyError:
        pass

    try:
        link += f"&s={ticket["s"]}"
    except KeyError:
        pass

    try:
        link += f"&r={ticket["r"]}"
    except KeyError:
        pass

    return link

def process_ticket(ticket):
    data = {
        "ticket_id": ticket["id"],
        "event": event.event_id,
        "section": ticket["sid"],
        "row": ticket["r"],
        "url": build_ticket_url(ticket).replace(" ", "%20"),
    }

    try:
        data["quantity"] = ticket["q"]
    except KeyError:
        data["quantity"] = None

    try:
        data["price"] = ticket["p"]
    except KeyError:
        data["price"] = None

    try:
        if ticket["n"] == "":
            data["note"] = None
        else:
            data["note"] = ticket["n"]
    except KeyError:
        data["note"] = None

    try:
        data["is_eticket"] = ticket["e"]
    except KeyError:
        data["is_eticket"] = False

    try:
        data["is_instant_delivery"] = ticket["i"]
    except KeyError:
        data["is_instant_delivery"] = False

    try:
        date = datetime.datetime.fromisoformat(ticket["ihd"])
        data["event_date"] = timezone.make_aware(date)
    except KeyError:
        data["event_date"] = None

    try:
        data["delivery_text"] = ticket["dt_text"]
    except KeyError:
        data["delivery_text"] = None

    try:
        data["is_active"] = ticket["a"]
    except KeyError:
        data["is_active"] = False

    try:
        data["is_agent_only"] = ticket["agent_only"]
    except KeyError:
        data["is_agent_only"] = False

    try:
        data["quality"] = ticket["grade"]
    except KeyError:
        data["quality"] = False

    try:
        data["is_best_deal"] = ticket["best_deal"]
    except KeyError:
        data["is_best_deal"] = False

    try:
        data["is_low_price"] = ticket["lp"]
    except KeyError:
        data["is_low_price"] = False

    try:
        data["is_money_saver"] = ticket["ms"]
    except KeyError:
        data["is_money_saver"] = False

    try:
        data["deal_value"] = ticket["dv"]
    except KeyError:
        data["deal_value"] = None

    try:
        data["face_value"] = ticket["fv"]
    except KeyError:
        data["face_value"] = None

    # print("=" * 50)
    # for key, value in data.items():
    #     print(f"    {key}: {value}")

    obj, created = Ticket.objects.get_or_create(**data)
    if created:
        print("Created:", data["ticket_id"])
    else:
        print("Duplicate:", data["ticket_id"])

def fetch_event_tickets(event: Event) -> None:
    url = f"https://api.tickpick.com/1.0/listings/internal/event-v2/{event.event_id}?trackView=true"

    DATADOME = '3jvVNJ2DVpIzOHM2YxCnXkQawiXsRJ7X1RQmXJlw0V6VHAAFEVnvZSPgTKf6FTnBoDb9k6hscl19YKDoagBYQ_Hi3lOU0HpWgCgAhed3VZNEJGVXNpiLxcS6kCUNTJ3S'

    response = requests.get(url, headers=make_headers(DATADOME))#, params=params)
    print("[LOG] Status Code:", response.status_code)

    if response.status_code != 200:
        DATADOME = input('New datadome: ')
        response = requests.get(url, headers=make_headers(DATADOME))
        if response.status_code != 200:
            return

    print('+1')

    try:
        json_data = response.json()
    except Exception as e:
        print(e)
        print("Raw Response:")
        print(response.text)
        return

    tickets = json_data["listings"]
    with ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(process_ticket, tickets)

    event.status = "Done"
    event.save()


if __name__ == '__main__':
    events = Event.objects.filter(
        Q(status="New"),
        Q(date__startswith="2025-10-")
    )
    start_time = time.time()

    for event in events:
        fetch_event_tickets(event)
        time.sleep(5)

    print(f'[LOG] Time: {time.time() - start_time}')