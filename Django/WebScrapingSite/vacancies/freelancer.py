import time

import aiohttp
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from selenium import webdriver
import json

HEADERS = {"UserAgent": UserAgent().random}


async def freelancer_com_vacancies(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}", headers=HEADERS) as response:
            r = await response.text()
            soup = bs(r, "html.parser")
            jobs = []
            for job in soup.find_all("div", {"class": "JobSearchCard-item-inner"}):
                job_primary = job.find_next()
                job_head = job_primary.find_next()
                job_title = job_head.find(
                    "a", {"class": "JobSearchCard-primary-heading-link"}
                )
                job_url = job_title.get("href")
                job_title = job_title.text.strip()
                if not job_title.startswith("Private project or contest"):
                    job_days_left = job_head.find_next("span").text.strip()
                    job_client_verify = (
                        "True"
                        if job_head.find(
                            "div",
                            {
                                "class": "JobSearchCard-primary-heading-status Tooltip--top"
                            },
                        )
                        else "False"
                    )
                    job_description = job_primary.find_next(
                        "p", {"class": "JobSearchCard-primary-description"}
                    ).text.strip()
                    job_all_tags = job_primary.findNext(
                        "div", {"class": "JobSearchCard-primary-tags"}
                    )
                    tags = ", ".join(
                        tag.text.strip() for tag in job_all_tags if tag.text.strip()
                    )
                    job_secondary = job_primary.find_next_sibling()
                    job_price = job_secondary.find_next().text.strip().splitlines()[0]
                    job_applicants = job_secondary.find(
                        "div", {"class": "JobSearchCard-secondary-entry"}
                    ).text.strip()[:-5]
                    job_info = {
                        "title": job_title,
                        "days_left": job_days_left,
                        "isVerify": job_client_verify,
                        "description": job_description,
                        "tags": tags,
                        "price": job_price,
                        "applicants": job_applicants,
                        "url": f"https://www.freelancer.com{job_url}",
                    }
                    job_info = json.dumps(job_info)
                    jobs.append(job_info)
            return jobs


async def upwork_com_vacancies(url):
    options = webdriver.ChromeOptions()
    options.add_argument("window-size=100x100")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(1)
    page_source = driver.page_source
    driver.quit()
    r = page_source
    jobs = []
    soup = bs(r, "html.parser")
    for job in soup.find_all(
        "article",
        {"class": "job-tile cursor-pointer px-md-4 air3-card air3-card-list px-4x"},
    ):
        job_header = job.find_next("div", {"class": "d-flex job-tile-header"})
        job_posted = job_header.find_next("small", {"data-v-03a16554": ""}).text.strip()
        job_title = job_header.find_next("a", {"class": "up-n-link"})
        job_url = (
            f'https://www.upwork.com/freelance-jobs/apply/{job_title.get("href")[6:]}'
        )
        job_title = job_title.text.strip()
        job_description = job_header.find_next_sibling()
        job_price_and_time = job_description.find_next(
            "ul", {"class": "job-tile-info-list text-base-sm mb-4"}
        )
        job_type = job_price_and_time.find_next(
            "li", {"data-test": "job-type-label"}
        ).text.strip()
        job_needed_exp = job_price_and_time.find_next(
            "li", {"data-test": "experience-level"}
        ).text.strip()
        try:
            job_duration = job_price_and_time.find_next(
                "li", {"data-test": "duration-label"}
            ).text.strip()
        except AttributeError:
            job_duration = ""
        job_content = job_price_and_time.find_next("p", {"class": "mb-0"}).text.strip()
        job_tags = job_description.find_all("span", {"class": "air3-token"})
        tags = ", ".join(tag.text.strip() for tag in job_tags)
        job_info = {
            "title": job_title,
            "posted": job_posted,
            "description": job_content,
            "tags": tags,
            "typeOfJob": job_type,
            "expNeeded": job_needed_exp,
            "duration": job_duration,
            "url": job_url,
        }
        job_info = json.dumps(job_info)
        jobs.append(job_info)
    return jobs


async def freelance_hunt_com_vacancies(url):
    async with aiohttp.ClientSession() as session:
        page = ""
        async with session.get(f"{url}", headers=HEADERS) as response:
            r = await response.text()
            soup = bs(r, "html.parser")
            pages_count = soup.find("ul", {"no-padding"})
            for p in pages_count:
                if p.text != "\n" and p.text != "\n→\n":
                    page = p.text.replace("\n", "")
        for i in range(1, int(page)):
            async with session.get(
                f"https://freelancehunt.com/ua/projects/skill/python/22.html?page={str(i)}"
            ):
                r = await response.text()
                soup = bs(r, "html.parser")
                jobs = []
                for job in soup.find_all("tr", {"style": "vertical-align: top"}):
                    main_info = job.find_next("td", {"class": "left"})
                    job_title = main_info.find_next("a", {"class": "biggest visitable"})
                    job_url = job_title.get("href")
                    job_title = job_title.text.strip()
                    job_description = main_info.find_next(
                        "p", {"style": "word-break: break-word"}
                    )
                    job_tags_and_info = job_description.find_next_sibling()
                    job_description = job_description.text.strip()
                    tags = job_tags_and_info.find_all("a")
                    job_tags = ", ".join(tag.text.strip() for tag in tags)
                    job_applicants = job_tags_and_info.text.strip().split("∙")
                    try:
                        job_applicants = job_applicants[1]
                    except IndexError:
                        job_applicants = "0 ставок"
                    job_cash_info = main_info.find_next_sibling().text.strip()
                    job_date_info = job.find_next("div", {"class": "with-tooltip"})
                    job_date_info = job_date_info.get("title")
                    job_info = {
                        "title": job_title,
                        "description": job_description,
                        "tags": job_tags,
                        "applicants": job_applicants,
                        "cash": job_cash_info,
                        "date": job_date_info,
                        "url": job_url,
                    }
                    job_info = json.dumps(job_info)
                    jobs.append(job_info)
                return jobs
