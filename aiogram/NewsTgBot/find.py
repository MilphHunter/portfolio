import aiohttp
from bs4 import BeautifulSoup as BS
from fake_useragent import UserAgent

HEADERS = {"User-Agent": UserAgent().random}


async def find_news(url):
    title = []
    link = []
    photo = []
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://itc.ua/ua/?s={url}", headers=HEADERS) as response:
            r = await response.text()
            soup = BS(r, "html.parser")
            items = soup.findAll("div", {"class": "row"})
            for item in items:
                if item is not None:
                    temp_title = item.find("a", {"rel": "bookmark"})
                    temp_photo = item.find("a", {"class": "thumb-responsive"})
                    if temp_photo is not None:
                        temp_photo = temp_photo.get("data-bg")
                    if temp_title is not None:
                        title.append(temp_title.text.strip())
                        link.append(temp_title.get("href"))
                        photo.append(temp_photo)
            return title, link, photo

