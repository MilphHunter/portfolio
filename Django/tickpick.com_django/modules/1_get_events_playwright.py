import time
from pprint import pprint

from modules.load_django import *
from parser_app.models import *

from playwright.async_api import async_playwright, BrowserContext
import asyncio
from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup

from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

from utils.get_date import infer_year

from contextlib import suppress
from playwright.async_api import TimeoutError as PWTimeout

@sync_to_async
def save(data):
    event_id = data.get('event_id')
    obj, created = Event.objects.get_or_create(
        event_id=event_id,
        defaults=data
    )

    if created:
        print(f'[LOG] Event {event_id} created.')
    else:
        print(f'[LOG] Event {event_id} already exists.')

@sync_to_async
def get_cats():
    return list(Categories.objects.filter(status='New'))


async def get_events(sem, context: BrowserContext, cat: Categories):
    url = cat.url
    async with sem:
        try:
            page = await context.new_page()
            await page.goto(url)

            await page.wait_for_load_state('load', timeout=15_000)
            btn = page.locator("button[aria-label='Events Nearby']")
            await btn.wait_for(state="visible", timeout=15_000)

            while True:
                btns = page.get_by_role("button", name="View More")
                count = await btns.count()
                if count == 0:
                    html = await page.content()
                    await parse_html(html)
                    await asyncio.sleep(5)
                    break

                btn = btns.first
                try:
                    await btn.wait_for(state="visible", timeout=3000)
                    await btn.scroll_into_view_if_needed()
                    await btn.hover()
                    await btn.focus()
                    await btn.click()

                    with suppress(PWTimeout):
                        await btn.wait_for(state="detached", timeout=5000)

                    with suppress(PWTimeout):
                        await page.wait_for_load_state("networkidle", timeout=3000)

                except PWTimeout:
                    pass

                await asyncio.sleep(0.5)

            cat.status = 'Done'
            await sync_to_async(cat.save)()

        except Exception as e:
            cat.status = 'Failed'
            await sync_to_async(cat.save)()
            print(f'[LOG] Event error. Error: {e} --- {url}')

        finally:
            await page.close()


async def parse_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    event_tags = soup.find_all('section', {'aria-label':'Event Information'})
    for tag in event_tags:
        data = {}

        raw_date = soup.find('ul', {'aria-label': 'Event Date Information'})
        parts = [li.get_text(strip=True) for li in raw_date.find_all('li')]

        data['name'] = soup.find('h4').text
        data['location'] = soup.find('h5').text.strip()
        data['date'] = infer_year(parts[0], int(parts[1]), parts[2]).isoformat()
        data['url'] = 'https://www.tickpick.com' + tag.parent.get('href')
        data['event_id'] = data['url'].split('/')[-2]

        await save(data)

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()

        page = await context.new_page()
        await page.goto('https://google.com')

        sem = asyncio.Semaphore(3)
        categories = await get_cats()

        tasks = [get_events(sem, context, cat) for cat in categories]

        await asyncio.gather(*tasks)

        await page.close()


if __name__ == '__main__':
    start_time = time.time()

    asyncio.run(main())
    # 14:55
    print(f'[LOG] Time: {time.time() - start_time}s.')