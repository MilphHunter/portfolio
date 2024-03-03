import aiohttp
from bs4 import BeautifulSoup as BS
from fake_useragent import UserAgent

HEADERS = {"User-Agent": UserAgent().random}


async def main(url):
    title = []
    time = []
    description = []
    link = []
    photo = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as response:
            r = await response.text()
            soup = BS(r, "html.parser")
            items = soup.findAll("div", {"class": "col-sm-12"})
            for item in items:
                if item is not None:
                    temp_title = item.find("a", {"rel": "bookmark"})
                    temp_time = item.find("span", {"class": "date part"})
                    temp_description = item.find("div", {"class": "entry-excerpt"})
                    temp_photo = item.find("a", {"class": "thumb-responsive"})
                    temp_photo = temp_photo.get("data-bg")
                    if temp_title is not None:
                        title.append(temp_title.text.strip())
                        time.append(temp_time.text.strip())
                        description.append(temp_description.text.strip())
                        link.append(temp_title.get("href"))
                        photo.append(temp_photo)
            return title, time, description, link, photo
