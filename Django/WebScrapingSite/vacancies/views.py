import asyncio
import json
import threading

from asgiref.sync import async_to_sync
from django.shortcuts import render
from django.conf import settings
from .freelancer import (
    freelancer_com_vacancies,
    upwork_com_vacancies,
    freelance_hunt_com_vacancies,
)
import redis

red = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB
)


def main_window(request):
    if request.method == "GET":
        freelancer = red.lrange("freelancer_com", 0, -1)
        upwork = red.lrange("upwork", 0, -1)
        freelanceHunt = red.lrange("freelance_hunt", 0, -1)
        freelancer_list = [json.loads(job.decode("utf-8")) for job in freelancer]
        upwork_list = [json.loads(job.decode("utf-8")) for job in upwork]
        freelanceHunt_list = [json.loads(job.decode("utf-8")) for job in freelanceHunt]
        context = {
            "freelancer": freelancer_list,
            "upwork": upwork_list,
            "freelanceHunt": freelanceHunt_list,
        }
        return render(request, "vacancies/snippets.html", context)
    return render(request, "vacancies/snippets.html")


async def update_bd():
    freelancer = await freelancer_com_vacancies(
        "https://www.freelancer.com/job-search/python/"
    )
    upwork = await upwork_com_vacancies(
        "https://www.upwork.com/nx/search/jobs/?per_page=50&q=Python&sort=recency"
    )
    freelanceHunt = await freelance_hunt_com_vacancies(
        "https://freelancehunt.com/ua/projects/skill/python/22.html"
    )
    return freelancer, upwork, freelanceHunt


def update_bd_call():
    freelancer, upwork, freelanceHunt = asyncio.get_event_loop().run_until_complete(
        update_bd()
    )
    red.delete("freelancer_com", "upwork", "freelance_hunt")
    for job in freelancer:
        red.rpush("freelancer_com", job)
    for job in upwork:
        red.rpush("upwork", job)
    for job in freelanceHunt:
        red.rpush("freelance_hunt", job)
