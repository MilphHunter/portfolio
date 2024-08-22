import json
import re

import requests

payload = ""
headers = {
    "cookie": "__cf_bm=cFodCze1B5kGmwXUwqE4QdbuBR7O3njVZCOtndgoJ0M-1714385043-1.0.1.1-TZe6G2VynNCID_8qmHZfU0gmA7Aie3IORVmqyJZHTKMdBsfeUJCMDROLYEjTwOIzRZmftklzpEkgZg._STlS8g; slang=ua; uid=Cgo9D2YvbWKJ6y3J1BdPAg%3D%3D; xab_segment=110; xl_uid=Cgo8MmYvbWIEagt5HiNTAg%3D%3D; cart-modal=old; ab-auto-portal=openedAll; promo-horizontal-filters=verticalFilters; social-auth=old; ab_tile_filter=old",
    "User-Agent": "insomnia/9.0.0"
}


def try_print(result):
    if result:
        return result.group(1)
    else:
        print("Спiвпадiнь не знайдено")


def get_count_pages(url):
    response = requests.request("GET", url, data=payload, headers=headers)
    pattern = r'"total_pages":(.*?),'
    match = re.search(pattern, response.text)
    max_page = int(try_print(match))
    print(f'Total pages: {max_page}')
    return max_page


def get_products_id(max_page, current_page=1):
    products = {}
    print('Collecting data...')
    while current_page != max_page:
        url = f"https://hard.rozetka.com.ua/computers/c80095/page={current_page}/"
        response = requests.request("GET", url, data=payload, headers=headers)
        pattern = r'"ids":\[(.*?)\]'
        match = re.search(pattern, response.text)
        match = try_print(match)
        products[current_page] = match
        print(f'Current page: {current_page}')
        current_page += 1
    return products


def get_products_info(products):
    values = {}
    print('Get product info:')
    for page, product_z in products.items():
        url = f"https://xl-catalog-api.rozetka.com.ua/v4/goods/getDetails?product_ids={product_z}"
        response = requests.request("GET", url, data=payload, headers=headers)
        values[page] = json.loads(response.text)
        print(f'Current page: {page}')
    return values


def get_some_info(values):
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


if __name__ == '__main__':
    values = get_products_info({
        1: '351145002,401966055,328612738,429675329,392944998,369248514,292755783,389493627,401966109,392904981,422114610,333372670,392904969,280343533,345473515,402223506,369355302,348094158,392907894,386928564,422114919,392907918,371268198,424141023,424134642,352138650,292758158,429675332,369364893,401123061,346867971,422114913,351145518,395193924,389493645,422114916,424140828,392907942,393002715,389493651,401965830,351145176,424138854,401966160,218694013,392945592,424139817,354006669,370401240,392903670,328617982,336955975,392944584,218694037,337237039,410564649,396341649,336955963,364557195,416426397',
        2: '344578873,392112012,392907915,348080703,266009361,335752111,392945721,374928873,392904966,429829589,392907924,370434108,315771157,392904948,393002196,392945580,299376813,401123073,365397255,326890636,403370382,344578789,275060953,361468335,392945673,365396832,392903472,358394943,425010951,416730651,416426517,416340399,416426508,364899888,422499849,292758738,401123370,370338492,392907891,313186342,417563823,428590475,401123400,389493327,313623043,364871610,393475314,389493735,351145254,392907897,428404025,419344824,395974233,389493831,401123223,358395180,253903796,422522163,414078576,316012681'
    })
    get_some_info(values)
