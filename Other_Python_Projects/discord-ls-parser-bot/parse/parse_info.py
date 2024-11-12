import asyncio

import aiohttp

from fake_useragent import UserAgent

HEADERS = {"User-Agent": UserAgent().random}
PROXY = "http://81.168.120.249:50100"


async def get_goods_info(url: str) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS, proxy=PROXY) as responce:
            if responce.status == 200:
                data = await responce.json()
                goods = []
                for good in data:
                    good_data = {good['id']: {
                        'org_name': good['orgName'],
                        'org_website': good['orgWebsite'],
                        'phone_numbers': good['phoneNumbers'],
                        'state_code': good['stateCode'],
                        'city_name': good['cityName'],
                        'postal_code_number': good['postalCodeNumber'],
                        'address': good['address'],
                        'latitude': good['latitude'],
                        'longitude': good['longitude'],
                        'utc_off_set': good['utcOffset'],
                        'name': good['name'],
                        'type_name': good['typeName']}
                    }
                    goods.append(good_data)
                return goods


async def fetch_info(session, item):
    async with session.get(f'https://www.estatesales.net/api/sale-details?bypass=byidsincludinginactive:{item}&include=dates,directions,plaintextshortdescription,mainpicture&explicitTypes=DateTime', headers=HEADERS, proxy=PROXY) as response:
        if response.status == 200:
            data = await response.json()
            goods_info = []
            for good in data:
                good_data = {
                    item: {
                        'main_picture': good['mainPicture'],
                        'dates': good['dates'],
                        'desc': good['plainTextShortDescription']
                    }
                }
                goods_info.append(good_data)
            return goods_info
        else:
            print(f"Exception: {response.status}")
            return None


async def get_info(id_list: list):
    goods_info = []
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_info(session, item) for item in id_list]
        results = await asyncio.gather(*tasks)
        for result in results:
            if result:
                goods_info.extend(result)
    return goods_info
