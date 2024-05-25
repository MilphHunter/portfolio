import json
import asyncio
import aiohttp
import re

payload = ""
headers = {
    "cookie": "cf_bm=cFodCze1B5kGmwXUwqE4QdbuBR7O3njVZCOtndgoJ0M-1714385043-1.0.1.1-TZe6G2VynNCID_8qmHZfU0gmA7Aie3IORVmqyJZHTKMdBsfeUJCMDROLYEjTwOIzRZmftklzpEkgZg._STlS8g; slang=ua; uid=Cgo9D2YvbWKJ6y3J1BdPAg%3D%3D; xab_segment=110; xl_uid=Cgo8MmYvbWIEagt5HiNTAg%3D%3D; cart-modal=old; ab-auto-portal=openedAll; promo-horizontal-filters=verticalFilters; social-auth=old; ab_tile_filter=old",
    "User-Agent": "insomnia/9.0.0"
}

def try_print(result):
    if result:
        return result.group(1)
    else:
        print("Спiвпадiнь не знайдено")

async def fetch_data(session, url):
    async with session.get(url, headers=headers) as response:
        return await response.text()

async def get_count_pages(url):
    async with aiohttp.ClientSession() as session:
        response_text = await fetch_data(session, url)
        pattern = r'"total_pages":(.*?),'
        match = re.search(pattern, response_text)
        max_page = int(try_print(match))
        print(f'Total pages: {max_page}')
        return max_page

async def get_products_id(max_page):
    products = {}
    print('Collecting data...')
    tasks = []
    async with aiohttp.ClientSession() as session:
        for current_page in range(1, max_page + 1):
            url = f"https://hard.rozetka.com.ua/computers/c80095/page={current_page}/"
            tasks.append(fetch_data(session, url))
        responses = await asyncio.gather(*tasks)
        for current_page, response_text in enumerate(responses, start=1):
            pattern = r'"ids":\[(.*?)\]'
            match = re.search(pattern, response_text)
            match = try_print(match)
            products[current_page] = match
            print(f'Current page: {current_page}')
    return products

async def get_products_info(products):
    values = {}
    print('Get product info:')
    tasks = []
    async with aiohttp.ClientSession() as session:
        for page, product_z in products.items():
            url = f"https://xl-catalog-api.rozetka.com.ua/v4/goods/getDetails?product_ids={product_z}"
            tasks.append(fetch_data(session, url))
        responses = await asyncio.gather(*tasks)
        for page, response_text in zip(products.keys(), responses):
            values[page] = json.loads(response_text)
            print(f'Current page: {page}')
    return values

async def get_some_info(values):
    print('Clarifying information...')
    result = []
    for page, val in values.items():
        for all_data in val['data']:
            result.append(
                (all_data['title'], all_data['id'], all_data['price'],
                 all_data['old_price'], all_data['href'], all_data['brand'],
                 all_data['brand_id'], all_data['docket'], all_data['image_main'],
                 page)
            )
        print(f'Current page: {page}')
    return result

async def main():
    max_page = await get_count_pages("https://hard.rozetka.com.ua/computers/c80095/")
    products = await get_products_id(max_page)
    values = await get_products_info(products)
    await get_some_info(values)

if __name__ == '__main__':
    asyncio.run(main())