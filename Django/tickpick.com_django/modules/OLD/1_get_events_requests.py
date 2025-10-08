import datetime
import json
from email.policy import default
from pprint import pprint

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

from load_django import *
from django.utils import timezone
from parser_app.models import *

import asyncio
import aiohttp
from asgiref.sync import sync_to_async

HEADERS = {
    "accept": "*/*",
    "accept-language": "uk,en-US;q=0.9,en;q=0.8,ru;q=0.7",
    "client-platform": "web",
    "content-type": "application/json",
    "forter-token-cookie": "ee4452942d304d4fbe24c4ecc9397b74_1758608284640__UDF43-m4_15ck_dKSo22v/JUA%3D-5971-v2",
    "origin": "https://www.tickpick.com",
    "priority": "u=1, i",
    "referer": "https://www.tickpick.com/",
    "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "session-id": "3653201a-92f7-4fec-8df4-7efb3dcf8fd7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "utm-campaign": "3476091",
    "utm-content": "Online Tracking Link_656088",
    "utm-medium": "Smart Influence GmbH",
    "utm-source": "impact",
    "x-client-id": "tickpick",
    "x-datadome-clientid": "WO7cn5szbud3v_6VPeKZbeMod90x7SoFTE1bEuNLktvMaq4bW6NAZBLvPrYMsyrR_xgU76n9j~xd40vx6Y4beoMWLvoLZMzg3qe9sVZeRhTvtsvEeR8E6mUq35QbfVwK"
}

@sync_to_async
def save(data):
    event_id = data.get('event_id')
    obj, created = Event.objects.update_or_create(
        event_id=event_id,
        defaults=data
    )

    if created:
        print(f'[LOG] Event {event_id} created.')
    else:
        print(f'[LOG] Event {event_id} already exists.')

async def scrape_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    events_article = soup.find('article', id='events')
    if events_article:
        ls_json = events_article.find_all('script', {'type' : 'application/ld+json'})
        if not ls_json:
            return False
        event_info = {}
        for event in ls_json:
            data = json.loads(event.text)
            event_info['name'] = data.get('name')
            event_info['description'] = data.get('description')
            event_info['type'] = data.get('@type')
            event_info['startDate'] = data.get('startDate')
            event_info['url'] = 'https://www.tickpick.com' + data.get('url')

            location = data.get('location', {}).get('address', {})
            event_info['location'] = (f'{location.get('addressCountry')}, '
                                      f'{location.get('addressLocality')}, '
                                      f'{location.get('addressRegion')}')

            event_info['event_id'] = data.get('url').split('/')[-2]

            await save(event_info)
        return True
    return False

async def get_tickets(sem, session, url):
    async with sem:
        offset = 20
        while True:
            payload = [
                "arizona-diamondbacks",
                {
                    "offset": offset,
                    "lat": 40.6943,
                    "long": -73.9249
                }
            ]
            print(offset)
            async with session.post(url=url, json=payload, headers=HEADERS) as response:

                if response.status != 200:
                    print('[LOG] Response status',response.status)
                    return [], response.status

                html = await response.text()

                result = await scrape_html(html)
                if result:
                    offset += 20
                    continue
                break

async def main():
    sem = asyncio.Semaphore(5)
    urls = ['https://www.tickpick.com/mlb/arizona-diamondbacks-tickets/',]
    async with aiohttp.ClientSession() as session:
        tasks = [get_tickets(sem, session, url) for url in urls]

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())