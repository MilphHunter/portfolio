import asyncio
import datetime
import json
import logging
import mimetypes
import os
import random
import re
import shutil
import sys
import time
import ast
import urllib
import uuid
from asyncio import Queue, Event
from collections import defaultdict
from json import JSONDecodeError
from typing import Tuple, Type
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import aiofiles
import aiohttp
import aiosqlite
import cv2
import imagehash
import numpy as np
import psutil
import requests
from PIL import Image
from b2sdk._internal.exception import FileNotPresent
from b2sdk.v1 import InMemoryAccountInfo, B2Api
from gspread_formatting import get_user_entered_format, format_cell_range
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright
from pydub import AudioSegment
from sqlalchemy import Column, String, Integer, UniqueConstraint, Boolean, select, text, delete
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from skimage.metrics import structural_similarity as ssim
from dotenv import load_dotenv

import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

COMPLETED_URL = os.environ.get("COMPLETED_URL")
LOCK_FILE = os.environ.get("LOCK_FILE")
PROCESS_END = os.environ.get("PROCESS_END")
MEDIA_FOLDER = os.environ.get("MEDIA_FOLDER")
EXCEL_FILE_NAME = os.environ.get("EXCEL_FILE_NAME")

cookie_data_index = []
cookies = {}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

file_handler = logging.FileHandler("parser.log", encoding='utf-8', errors='replace')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

Base = declarative_base()
DuplicateBase = declarative_base()
InfoBase = declarative_base()
os.environ["PATH"] += r";C:\ffmpeg\bin"
download_semaphore = asyncio.Semaphore(100)
write_queue = Queue()
info_write_queue = Queue()

APPLICATION_KEY_ID = os.environ.get("APPLICATION_KEY_ID")
APPLICATION_KEY = os.environ.get("APPLICATION_KEY")
BUCKET_NAME = os.environ.get("BUCKET_NAME")

info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", APPLICATION_KEY_ID, APPLICATION_KEY)
bucket = b2_api.get_bucket_by_name(BUCKET_NAME)

SERVICE_ACCOUNT_FILE = os.environ.get("SERVICE_ACCOUNT_FILE")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


class RateLimitExceeded(Exception):
    pass


class Ad(Base):
    __tablename__ = 'ads'
    id = Column(Integer, primary_key=True, index=True)
    archive_id = Column(String, unique=True, index=True, nullable=False)
    display_format = Column(String, nullable=True)
    end_time = Column(Integer, nullable=True)
    publish = Column(Integer, nullable=True)
    active = Column(Boolean, nullable=False, default=True)  # Будет храниться как 0 или 1
    real_fp_id = Column(String, nullable=True)
    fp_name = Column(String, nullable=True)
    platforms = Column(String, nullable=True)
    geo = Column(String, nullable=False, default='GB')
    offer = Column(String, nullable=False, default='Гембла')
    v = Column(String, nullable=False, default='Гембла')
    ad_text = Column(String, nullable=True)
    link_type = Column(String, nullable=True)
    ad_type = Column(String, nullable=True)
    ad_link = Column(String, nullable=True)
    fp_id = Column(String, nullable=True)
    ad_src = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('archive_id', name='uix_archive_id'),
    )


# New model for duplicate ads
class DuplicateAd(Base):
    __tablename__ = 'duplicate_ads'
    id = Column(Integer, primary_key=True, index=True)
    archive_id = Column(String, unique=True, index=True, nullable=False)


class Info(InfoBase):
    __tablename__ = 'info'
    link = Column(String, nullable=False, primary_key=True)
    date = Column(String, nullable=False, primary_key=True)
    country = Column(String, nullable=False)
    elements = Column(Integer, nullable=False)
    unique_elements = Column(Integer, nullable=False)
    archive_id = Column(String, nullable=True)


DATABASE_URL = "sqlite+aiosqlite:///ads_data.db?timeout=30"
INFO_DATABASE_URL = "sqlite+aiosqlite:///statistic.db?timeout=30"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

info_engine = create_async_engine(INFO_DATABASE_URL, echo=False)
InfoSessionLocal = sessionmaker(
    bind=info_engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with info_engine.begin() as conn:
        await conn.run_sync(InfoBase.metadata.create_all)
    logger.info("Все базы данных инициализированы")


# Функция для коммита с логикой повторных попыток
async def commit_with_retry(
        session,
        archive_id: str,
        retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: Tuple[Type[Exception], ...] = (OperationalError,),
        retry_on_messages: Tuple[str, ...] = ("database is locked",)
) -> bool:
    """
    Attempts to commit the session with retries on specified exceptions.

    Args:
        session: The database session to commit.
        archive_id: Identifier for logging purposes.
        retries: Number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.
        max_delay: Maximum delay in seconds between retries.
        exceptions: Tuple of exception classes to catch for retry.
        retry_on_messages: Tuple of substrings to check in exception messages to qualify for retry.

    Returns:
        True if commit succeeded, False otherwise.

    Raises:
        Exception: Re-raises exceptions that are not eligible for retry.
    """
    for attempt in range(1, retries + 1):
        try:
            await session.commit()
            logger.info(f"Данные добавлены. archive_id: {archive_id}")
            return True
        except exceptions as e:
            error_message = str(e).lower()
            should_retry = any(msg in error_message for msg in retry_on_messages)
            if should_retry:
                delay = min(base_delay * 2 ** (attempt - 1), max_delay)
                # Adding jitter: +/- 10%
                jitter = delay * 0.1
                delay = delay + random.uniform(-jitter, jitter)
                logger.warning(
                    f"Ошибка при сохранении объявления {archive_id}: {e}. "
                    f"Повтор через {delay:.2f} секунд... (Попытка {attempt}/{retries})"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(f"Непредвиденная ошибка при сохранении объявления {archive_id}: {e}")
                raise
    logger.error(f"Не удалось сохранить объявление {archive_id} после {retries} попыток.")
    return False


def validate_snapshot_body(snapshot_body):
    required_keys = ['text']
    if not all(key in snapshot_body for key in required_keys):
        return False
    return True


downloaded_resources = 0
link_download_resources_counter = {}
page_content_end = set()


async def get_html_body(html: str):
    response_text = html.split('search_results_connection":')[1]
    response_text = response_text.split('},"page"')[0]
    response_text = json.loads(response_text)
    return response_text['edges']


async def process_url(playwright, page_url, SessionLocal, proxy, download_tasks, exclude_domains, batch_cookies,
                      scroll_duration=20):
    html_find = False

    async def handle_response(response, geo, session_factory, download_tasks, last_ad_time, exclude_domains, page_url):
        url = response.url
        method = response.request.method
        nonlocal empty_edges_counter
        nonlocal skip_empty_edges
        nonlocal html_find
        if (url.startswith('https://www.facebook.com/api/graphql/') and method == 'POST') or url == page_url:
            try:
                if url == page_url and html_find == False:
                    if response.status < 300:
                        edges = await response.text()
                        edges = await get_html_body(edges)
                        html_find = True
                        logger.info(f'Получен ответ от первых элементов.')
                    else:
                        logger.warning(f"Пропущен ответ из-за редиректа: {response.status}, text: {response.text}")
                        return
                else:
                    if response.status != 200:
                        logger.warning(f"Unexpected status code: {response.status}")
                        if response.status == 500:
                            logger.info('Page content ended')
                            page_content_end.add(page_url)
                        return

                    try:
                        json_data = await response.json()
                    except (PlaywrightError, JSONDecodeError) as e:
                        logger.warning(f"Could not parse response JSON: {e}")
                        return

                    if not json_data:
                        logger.warning("Пустой JSON-ответ.")
                        return

                    try:
                        typename = json_data["data"]["viewer"]["actor"].get("__typename")
                        if typename == "LoggedOutUser":
                            logger.error("Non-working cookies")
                            return "Cookies_Error"
                    except KeyError as e:
                        logger.info("Cookies are still working")

                    # Проверка на наличие ошибок в ответе
                    if 'errors' in json_data:
                        for error in json_data['errors']:
                            if error.get('code') == 1348007:
                                logger.error('Non-working cookies')
                                return "Cookies_Error"
                            if error.get('code') == 2334008:
                                logger.error("Non-working cookies")
                                return "Cookies_Error"
                            if error.get('message') == "Rate limit exceeded" or error.get(
                                    'message') == 'A server error rate_limit_exceeded occured. Check server logs for details.':
                                logger.error("Превышен лимит запросов")
                                return "Cookies_Error"

                        # Log other errors
                        logger.error(f"Ошибки в ответе: {json_data['errors']}")
                        return

                    data = json_data.get('data', {})
                    ad_library_main = data.get('ad_library_main', {})
                    search_results = ad_library_main.get('search_results_connection', {})
                    edges = search_results.get('edges', [])
                    if not skip_empty_edges:
                        if search_results and not edges:
                            empty_edges_counter += 1
                            logger.warning(f"Количество пустых response: {empty_edges_counter}")
                        if empty_edges_counter > 2:
                            c = f"{batch_cookies[0]['value']}:{batch_cookies[1]['value']}\n"
                            with open('settings/cookie_chill.txt', 'a') as f:
                                f.write(c)
                            logger.error("Non-working cookies")
                            global multiplier
                            multiplier += 1
                            return "Cookies_Error"

                for edge in edges:
                    if not isinstance(edge, dict):
                        continue
                    skip_empty_edges = True
                    node = edge.get('node', {})
                    collated_results = node.get('collated_results', [])

                    for ad in collated_results:
                        try:
                            start_date = ad.get('start_date')
                            snapshot = ad['snapshot']
                            if len(ad['targeted_or_reached_countries']) > 0:
                                logger.info(f"TARGETED COUNTRIES: {ad['targeted_or_reached_countries']}")
                            result = {
                                'ad_id': ad.get('ad_archive_id'),
                                'page_id': ad.get('page_id'),
                                'page_name': ad.get('page_name'),
                                'eu_total_reach': ad.get('eu_total_reach'),
                                'target_ages': ad.get('target_ages'),
                                'target_gender': ad.get('target_gender'),
                                # 'target_locations': process_locations(ad.get('target_locations')),
                                'creative_bodies': ad.get('creative_bodies'),
                                'creative_link_captions': ad.get('creative_link_captions'),
                                'creative_link_descriptions': ad.get('creative_link_descriptions'),
                                'creative_link_titles': ad.get('creative_link_titles'),
                                'publish': start_date,
                                'display_format': snapshot.get('display_format'),
                                'fp_id': snapshot.get('page_profile_uri'),
                                'items': []
                            }

                            # Convert Unix timestamps to readable dates
                            # if 'startDate' in ad_props:
                            #    from datetime import datetime
                            #    start_time = datetime.fromtimestamp(ad_props.get('startDate'))
                            #    result['ad_delivery_start_time'] = start_time.strftime('%Y-%m-%d %H:%M:%S')

                            if 'end_date' in ad:
                                from datetime import datetime
                                end_time = datetime.fromtimestamp(ad.get('end_date'))
                                result['ad_delivery_stop_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')

                            result['is_active'] = ad.get('is_active')
                            result['platforms'] = ad.get('publisher_platform', [])

                            # Get display format
                            display_format = snapshot.get('display_format', '').lower()

                            archive_id = ad.get('ad_archive_id')
                            media_src_list = []

                            # For photo and video formats
                            if display_format in ['photo', 'video', 'image']:

                                videos = snapshot.get('videos', [])
                                images = snapshot.get('images', [])

                                # Обработка медиа из 'videos' и 'images' и объединение их в общий список

                                video_src_list = await process_media_items(videos, archive_id, media_type='video',
                                                                           download_tasks=download_tasks)
                                image_src_list = await process_media_items(images, archive_id, media_type='image',
                                                                           download_tasks=download_tasks)

                                # Добавляем обработанные ссылки в общий массив
                                media_src_list.extend(video_src_list)
                                media_src_list.extend(image_src_list)

                                if not media_src_list:
                                    cards = snapshot.get('cards', [])
                                    if cards:
                                        card_image_urls, card_video_urls = extract_media_from_cards(cards)

                                        # Обработка медиа из 'cards'
                                        card_image_src_list = await process_media_urls(card_image_urls, archive_id,
                                                                                       media_type='image',
                                                                                       download_tasks=download_tasks)
                                        card_video_src_list = await process_media_urls(card_video_urls, archive_id,
                                                                                       media_type='video',
                                                                                       download_tasks=download_tasks)

                                        media_src_list.extend(card_image_src_list)
                                        media_src_list.extend(card_video_src_list)

                                media_src_list = [src for src in media_src_list if 'preview' not in src]
                                media_src = ','.join(media_src_list) if media_src_list else None

                                body_text = ''
                                snapshot_body = snapshot.get('body', {})
                                if snapshot_body and validate_snapshot_body(snapshot_body):
                                    body_text = snapshot_body.get('text', '')
                                    if "{{product.brand}}" in body_text:
                                        body_text = ''

                                item = {
                                    'index': 0,  # Add index as requested
                                    'display_format': display_format,
                                    'link_url': snapshot.get('link_url'),
                                    'cta_type': snapshot.get('cta_type'),
                                    'title': snapshot.get('title'),
                                    'body': body_text,
                                    'caption': snapshot.get('caption'),
                                    'image_url': ad.get('original_image_url') or ad.get(
                                        'image_url') or snapshot.get(
                                        'original_image_url') or snapshot.get('resized_image_url'),
                                    'video_hd_url': ad.get('video_hd_url') or snapshot.get('video_hd_url'),
                                    'video_sd_url': ad.get('video_sd_url') or snapshot.get('video_sd_url'),
                                    'video_preview_image_url': ad.get('video_preview_image_url') or snapshot.get(
                                        'video_preview_image_url'),
                                    'link_description': snapshot.get('link_description'),
                                    'ad_src': media_src
                                }
                                result['items'].append(item)

                            # For dpa/dco formats with cards
                            elif display_format in ['dpa', 'dco'] or 'cards' in snapshot:
                                cards = snapshot.get('cards', [])

                                for idx, card in enumerate(cards):
                                    # Skip cards with Amazon links if needed
                                    link_url = card.get('link_url', '')
                                    if 'amazon' in link_url.lower() or 'fb.me' in link_url.lower() or 'facebook.com' in link_url.lower() or 'https://www.' in link_url.lower() or 'http://www.' in link_url.lower() or 'product' in link_url.lower() or 'products' in link_url.lower() or 'google' in link_url.lower():
                                        continue

                                    try:

                                        card_image_urls, card_video_urls = extract_media_from_cards(cards)

                                        # Обработка медиа из 'cards'
                                        card_image_src_list = await process_media_urls(card_image_urls, archive_id,
                                                                                       media_type='image',
                                                                                       download_tasks=download_tasks)
                                        card_video_src_list = await process_media_urls(card_video_urls, archive_id,
                                                                                       media_type='video',
                                                                                       download_tasks=download_tasks)

                                        media_src_list.extend(card_image_src_list)
                                        media_src_list.extend(card_video_src_list)

                                        media_src_list = [src for src in media_src_list if 'preview' not in src]
                                        media_src = ','.join(media_src_list) if media_src_list else None

                                        parsed_url = urllib.parse.urlparse(link_url)
                                        domain = parsed_url.netloc.lower()

                                        # Список нежелательных доменных зон
                                        unwanted_tlds = ['.de', '.ar', '.com.ar', '.in', '.me', '.ch', '.bo', '.us',
                                                         '.bd', '.at', '.br',
                                                         '.id', ".il", '.tr', '.mx', '.pe', '.pl', '.it', '.hu', '.cz',
                                                         ".pt", ".ro", '.bg',
                                                         '.it', '.es', '.si', '.sk', '.gt', '.sl', '.lt', '.lv', '.mx',
                                                         '.uk', '.fr', '.gr',
                                                         '.gov', '.co']

                                        if any(domain.endswith(tld) for tld in unwanted_tlds):
                                            continue
                                        body_text = ''
                                        snapshot_body = snapshot.get('body', {})
                                        if snapshot_body and validate_snapshot_body(snapshot_body):
                                            body_text = snapshot_body.get('text', '')
                                            if "{{product.brand}}" in body_text:
                                                body_text = ''
                                        item = {
                                            'index': card.get('index', idx),
                                            # Use card index or fallback to iteration index
                                            'display_format': display_format,
                                            'link_url': link_url,
                                            'cta_type': card.get('cta_type'),
                                            'title': card.get('title'),
                                            'body': body_text,
                                            'caption': card.get('caption'),
                                            'link_description': card.get('link_description'),
                                            'image_url': card.get('original_image_url') or card.get(
                                                'resized_image_url') or ad.get(
                                                'original_image_url') or ad.get('image_url'),
                                            'video_hd_url': card.get('video_hd_url') or ad.get('video_hd_url'),
                                            'video_sd_url': card.get('video_sd_url') or ad.get('video_sd_url'),
                                            'video_preview_image_url': card.get('video_preview_image_url',
                                                                                '') or ad.get(
                                                'video_preview_image_url', ''),
                                            'ad_src': media_src
                                        }

                                        result['items'].append(item)
                                    except:
                                        pass

                            now = datetime.now()
                            link_download_resources_counter[now.strftime("%d-%m-%Y")][page_url].append(
                                archive_id)

                            logger.debug("Добавляю данные в очередь.")
                            await write_queue.put(result)
                            last_ad_time['time'] = time.time()
                        except Exception as e:
                            print(f"Error processing ad props: {str(e)}")
                            return None
            except Exception as e:
                logger.exception(f"Ошибка при обработке ответа: {e}")

    try:
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled',
            ],
            proxy=proxy

        )

        context = await browser.new_context(
            permissions=['geolocation'],
        )
        while True:
            await context.add_cookies(batch_cookies)
            page = await context.new_page()
            last_ad_time = {'time': time.time()}
            cookies_error_event = Event()
            empty_edges_counter = 0
            skip_empty_edges = False
            geo = page_url.split('country=')[1].split('&')[0]

            async def handle_response_wrapper(response):
                global page_content_end
                nonlocal handle_response
                try:
                    if page_url in page_content_end:
                        logger.debug("Ошибка 500. Завершаем сбор ответов")
                    else:
                        result = await asyncio.wait_for(
                            handle_response(response, geo, SessionLocal, download_tasks, last_ad_time, exclude_domains,
                                            page_url),
                            timeout=60
                        )
                        if result == "Cookies_Error":
                            cookies_error_event.set()


                except asyncio.TimeoutError:
                    logger.error("Обработчик handle_response завис. Пропускаем страницу.")
                    return

            # Добавляем обработчик ответа
            page.on("response", lambda response: asyncio.create_task(handle_response_wrapper(response)))

            logger.info(f"[{page_url}] Переход на страницу: {page_url} через прокси {proxy.get('server')}")
            now = datetime.datetime.now()
            link_download_resources_counter[now.strftime("%d-%m-%Y")][page_url] = []
            success = await load_page_with_retries(page, page_url, geo)
            if success == 'Account_blocked':
                logger.warning("Перезапуск из-за ошибки Cookies_Error")
                batch_cookies = await update_cookie()
                await page.close()
                continue  # Перезапуск цикла
            if not success:
                await asyncio.sleep(5)
                await browser.close()
                logger.error(f"[{page_url}] Прерываю процесс из-за неудачи загрузки.")
                return
            if cookies_error_event.is_set():  # CHECK
                logger.warning("Перезапуск из-за ошибки Cookies_Error")
                batch_cookies = await update_cookie()
                await page.close()
                continue  # Перезапуск цикла
            break

        if download_tasks:
            await asyncio.gather(*download_tasks)

        # Закрываем браузер
        await asyncio.sleep(5)
        await browser.close()
        logger.info(f"[{page_url}] Браузер закрыт.")
    except RateLimitExceeded as rate_limit:
        logger.error(f"[{page_url}] RateLimitExceeded. Stopping")
    except Exception as e:
        logger.error(f"[{page_url}] Общая ошибка в process_url: {e}")
    finally:
        if browser:
            await asyncio.sleep(5)
            await browser.close()
            logger.info(f"[{page_url}] Браузер закрыт.")


multiplier = 1


async def scroll_to_bottom(page, url):
    prev_height = 0
    global page_content_end
    while True:
        global multiplier
        delay = random.uniform(2, 7) * multiplier
        if multiplier >= 5:
            multiplier = 1
        await asyncio.sleep(delay)
        if url in page_content_end:
            logger.info('Конец страницы')
            page_content_end.remove(url)
            break

        # Прокручиваем страницу до самого концаu
        curr_height = await page.evaluate("""() => {
            window.scrollTo(0, document.body.scrollHeight);
            return document.body.scrollHeight;
        }""")

        # Даем время на подгрузку контента
        await asyncio.sleep(.55)

        images = page.locator('img[src="/images/checkpoint/epsilon/comet/intro.png"]')

        # Если изображение найдено, выводим уведомление
        if await images.count() > 0:
            return "Page error"

        while True:
            more_btn = page.locator('a._8n_3')
            if await more_btn.count() > 0 and await more_btn.is_visible():
                if await more_btn.is_enabled():
                    await more_btn.click(force=True)
                    await asyncio.sleep(1)
            else:
                break

        element = await page.query_selector("#code_in_cliff")
        if element:
            return "Page error"
        element = await page.query_selector(
            'span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.x1xmvt09.x1lliihq.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.xudqn12.x3x7a5m.x6prxxf.xvq8zen.xo1l8bm.xi81zsa')
        if element:
            return "Page error"

        while True:
            await asyncio.sleep(.55)
            page_load_el = await page.query_selector('svg.x1ka1v4i.x7v9bd0.x1esw782.xa4qsjk.xxymvpz')
            if not page_load_el:
                logger.info("Финальная проверка конца страницы")
                await asyncio.sleep(5)
                page_load_el = await page.query_selector('svg.x1ka1v4i.x7v9bd0.x1esw782.xa4qsjk.xxymvpz')
                if not page_load_el:
                    break
        if curr_height == prev_height:
            logger.info('Конец страницы')
            break
        prev_height = curr_height

        net_error = await page.query_selector("svg.x1lliihq.x1tzjh5l.x1k90msu.x2h7rmj.x1qfuztq.xfx01vb")
        if net_error:
            logger.warning('Проблема с интернетом при загрузке страницы')
            await asyncio.sleep(5)
            continue


async def load_page_with_retries(page, url, geo, max_retries=3, timeout=200000):
    for attempt in range(max_retries):
        try:
            logger.info(f"[Попытка {attempt + 1}] Загрузка страницы: {url}")
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0"
            })
            await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            await page.wait_for_load_state()
            try:
                element = await page.query_selector(
                    "div[role='heading'].x8t9es0.x1uxerd5.xrohxju.x108nfp6.xq9mrsl.x1h4wwuj.x117nqv4.xeuugli")

                if element:
                    text = await element.text_content()
                    match = re.search(r"\d[\d\s,]*", text)

                    if match:
                        number = match.group(0).replace(" ", "").replace(",", "")
                        logger.info(f"Found ads: {number}")
                    else:
                        logger.info(f"Found ads number not found: {text}")
                else:
                    logger.debug("ELM not found")
            except Exception as e:
                logger.error(f"Elements coun not found: {e}")
                pass
            account_blocked = await scroll_to_bottom(page, url)
            if account_blocked == "Page error":
                return 'Account_blocked'
            logger.info(f"[{url}] Страница успешно загружена на попытке {attempt + 1}.")
            global data
            index = next((i for i, item in enumerate(data['data']) if item['link'] == url), None)
            if index is not None:
                await append_statistic(url, geo)
            return True

        except Exception as e:
            logger.error(f"[Попытка {attempt + 1}] Ошибка при переходе на страницу {url}: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Повторная попытка загрузки страницы через 5 секунд...")
                await asyncio.sleep(5)  # Задержка перед повторной попыткой

    logger.error(f"[{url}] Не удалось загрузить страницу после {max_retries} попыток.")
    return False


async def append_statistic(page_url, geo):
    now = datetime.datetime.now()
    date_str = now.strftime("%d-%m-%Y")

    if page_url in link_download_resources_counter.get(date_str, {}):
        elements = link_download_resources_counter[date_str][page_url]
        statistic_data = {
            'link': page_url,
            'date': date_str,
            'country': geo,
            'elements': len(elements),
            'unique_elements': 0,
            'archive_id': ', '.join(elements)
        }
        await info_write_queue.put(statistic_data)


async def process_media_urls(urls, archive_id, media_type='image', download_tasks=None):
    """
    Processes a list of media URLs by generating unique names and downloading them.

    :param urls: List of media URLs.
    :param archive_id: The ID of the ad archive.
    :param media_type: Type of media ('image' or 'video').
    :param download_tasks: List to collect download tasks.
    :return: List of media source names.
    """
    media_src_list = []

    if not isinstance(urls, list) or not urls:
        return media_src_list  # Вернуть пустой список

    for idx, url in enumerate(urls):
        if not url:
            continue

        try:
            # Генерируем уникальное имя файла
            unique_id = str(uuid.uuid4())
            media_src = f"{archive_id}_{idx}"
            media_src = ensure_file_extension(media_src, media_type)
            media_src_list.append(media_src)
            logger.debug(f"Запуск загрузки {media_type}: {url} с именем: {media_src}")
            # Передаём список из одного URL
            task = asyncio.create_task(download_media([url], media_src, media_type=media_type))
            if download_tasks is not None:
                download_tasks.append(task)

        except Exception as e:
            logger.error(f"Ошибка при обработке {media_type} URL {url}: {e}")

    return media_src_list


async def process_media_items(media_items, archive_id, media_type='video', download_tasks=None):
    media_src_list = []
    if not isinstance(media_items, list) or not media_items:
        logger.debug("Список медиа пуст или не является списком.")
        return media_src_list

    for idx, media in enumerate(media_items):
        if media is None:
            logger.debug("Пропущен пустой медиа-элемент.")
            continue

        primary_url = None
        backup_url = None
        video_preview_image_url = None

        try:
            if media_type == 'video':
                primary_url = media.get('video_hd_url')
                backup_url = media.get('video_sd_url')
                video_preview_image_url = media.get('video_preview_image_url')
            elif media_type == 'image':
                primary_url = media.get('original_image_url')
                backup_url = media.get('resized_image_url')
        except Exception as e:
            logger.error(f"Ошибка при получении URL {media_type}: {e}")
            continue

        media_urls = [url for url in [primary_url, backup_url] if url]
        if media_urls:
            unique_id = str(uuid.uuid4())
            media_src = f"{archive_id}_{idx}"
            media_src = ensure_file_extension(media_src, media_type)
            media_src_list.append(media_src)
            try:
                logger.debug(f"Запуск загрузки {media_type}: {media_urls} с именем: {media_src}")
                task = asyncio.create_task(download_media(media_urls, media_src, media_type))
                if download_tasks is not None:
                    download_tasks.append(task)
            except Exception as e:
                logger.error(f"Ошибка при создании задачи загрузки {media_type}: {e}")

        if video_preview_image_url:
            preview_src = f"{archive_id}_{idx}_preview"
            preview_src = ensure_file_extension(preview_src, 'image')
            media_src_list.append(preview_src)
            try:
                task = asyncio.create_task(download_media([video_preview_image_url], preview_src, 'image'))
                if download_tasks is not None:
                    download_tasks.append(task)
            except Exception as e:
                logger.error(f"Ошибка при создании задачи загрузки preview-изображения: {e}")

    return media_src_list


def extract_media_from_cards(cards):
    """
    Extracts image and video URLs from the given list of card dictionaries.

    :param cards: List of card dictionaries.
    :return: Tuple of two lists: (image_urls, video_urls)
    """
    card_image_urls = []
    card_video_urls = []

    for card in cards:
        url = card.get('original_image_url')
        if url:
            card_image_urls.append(url)

        url = card.get('video_hd_url')
        if url:
            card_video_urls.append(url)

    return card_image_urls, card_video_urls


def ensure_file_extension(filename, media_type):
    """
    Проверяет и добавляет необходимое расширение к имени файла.

    :param filename: Исходное имя файла или URL.
    :param media_type: Тип медиа ('video' или 'image').
    :return: Имя файла с правильным расширением.
    """
    required_extension = '.mp4' if media_type == 'video' else '.jpg'

    # Извлекаем базовое имя файла
    base_name = os.path.basename(filename)

    # Разделяем имя файла и расширение
    name, ext = os.path.splitext(base_name)

    # Если расширение не соответствует требуемому, заменяем его
    if ext.lower() != required_extension:
        new_filename = f"{name}{required_extension}"
        logger.debug(f"Расширение файла изменено с {ext} на {required_extension}: {new_filename}")
        return new_filename
    return filename


def extract_media_name(media_url, media_type='video'):
    """
    Extracts the media filename from the given URL.

    :param media_url: The URL of the media.
    :param media_type: Type of media ('video' or 'image').
    :return: Filename of the media or None if extraction fails.
    """
    try:
        parsed_url = urlparse(media_url)
        path = parsed_url.path
        filename = os.path.basename(path)
        if not filename:
            # Если имя файла пустое, попробуем извлечь из query parameters
            query_params = parse_qs(parsed_url.query)
            if 'url' in query_params:
                # Если в параметрах есть 'url', рекурсивно вызовем функцию с новым URL
                return extract_media_name(query_params['url'][0], media_type)
            else:
                logger.error(f"Не удалось извлечь имя {media_type} из URL: {media_url}")
                return None
        else:
            # Удаляем потенциальные суффиксы типа '?_nc_cat=...', оставляя только имя файла
            filename = filename.split('?')[0]
            return filename
    except Exception as e:
        logger.error(f"Ошибка при извлечении имени {media_type}: {e}")
        return None


async def download_media(media_urls, src_name, media_type):
    async with download_semaphore:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.facebook.com/'
        }

        timeout = 150  # или больше
        max_attempts = 5  # Максимальное количество попыток для каждого URL

        # Домены для смены
        alternate_domain = "https://scontent-waw2-1.xx.fbcdn.net"

        for media_url in media_urls:
            attempt = 0
            while attempt < max_attempts:
                try:
                    # Проверяем, если попытки превышают 2, меняем домен в URL
                    if attempt > 2:
                        logger.debug(f"Попытка {attempt + 1}: смена домена для {media_url}")
                        media_url = media_url.replace("video-yyz1-1.xx.fbcdn.net", "scontent-waw2-1.xx.fbcdn.net")

                    logger.debug(f"Скачивание {media_type} с URL: {media_url}, попытка {attempt + 1}")

                    conn = aiohttp.TCPConnector(ssl=False)
                    async with aiohttp.ClientSession(connector=conn, trust_env=True, headers=headers,
                                                     timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                        async with session.get(media_url, allow_redirects=True) as resp:
                            # Проверяем статус ответа и выбрасываем исключение при ошибке
                            resp.raise_for_status()
                            content_type = resp.headers.get('Content-Type', '').lower()
                            logger.debug(f"Полученный Content-Type: {content_type} для {src_name}")

                            # Определяем ожидаемый Content-Type префикс
                            expected_prefix = 'image/' if media_type == 'image' else 'video/'

                            # Проверяем, соответствует ли Content-Type ожидаемому или является application/octet-stream
                            if not (content_type.startswith(
                                    expected_prefix) or content_type == 'application/octet-stream'):
                                logger.warning(
                                    f"Expected {media_type} but got {content_type} for {src_name}. Файл будет скачан с добавлением расширения.")
                                # Добавляем расширение, если его нет или оно некорректно
                                src_name = ensure_file_extension(src_name, media_type)
                            else:
                                # Если Content-Type корректный, убедимся, что расширение тоже корректное
                                src_name = ensure_file_extension(src_name, media_type)

                            # Читаем содержимое ответа
                            content = await resp.read()
                            logger.debug(f"Получено {len(content)} байт для {src_name}")

                            # Проверяем, что содержимое не пустое
                            if len(content) == 0:
                                logger.warning(f"Пустое содержимое для {src_name}")
                                return

                            file_path = os.path.join(MEDIA_FOLDER, src_name)

                            # Используем aiofiles для асинхронной записи файла
                            async with aiofiles.open(file_path, 'wb') as f:
                                await f.write(content)

                            logger.debug(f"{media_type.capitalize()} {src_name} успешно скачано.")

                            global downloaded_resources
                            downloaded_resources += 1
                            logger.info("Количество загруженных ресурсов: " + str(downloaded_resources))
                            await asyncio.sleep(2)
                            return  # Успешная загрузка, выходим из функции

                except aiohttp.ClientResponseError as e:
                    logger.error(f"HTTP ошибка для {media_url}: {e}")
                except asyncio.TimeoutError:
                    logger.error(f"Таймаут при скачивании {media_url}")
                except Exception as e:
                    logger.error(f"Ошибка при скачивании {media_url}: {e}")
                finally:
                    attempt += 1

            logger.error(f"Не удалось скачать {media_url} после {max_attempts} попыток.")


count_added_cards = 0


async def writer_coroutine(session_factory):
    logger.info("Запущен writer_coroutine.")
    while True:
        try:
            ad_data = await write_queue.get()
            if ad_data is None:
                logger.info("Получен сигнал завершения writer_coroutine.")
                write_queue.task_done()
                break

            logger.info(f"Получены данные из очереди: {ad_data['ad_id']}")
            async with session_factory() as session:
                try:
                    # Проверка существования объявления
                    existing_ad = await session.execute(
                        select(Ad).where(Ad.archive_id == ad_data['ad_id'])
                    )
                    existing_ad = existing_ad.scalar_one_or_none()
                    if existing_ad:
                        logger.info(f"Объявление {ad_data['ad_id']} уже существует. Пропуск.")
                        continue  # Не вызываем task_done() здесь

                    # Создание нового объекта Ad
                    ad_record_data = {
                        'archive_id': ad_data.get('ad_id'),
                        'real_fp_id': ad_data.get('page_id'),
                        'fp_name': ad_data.get('page_name'),
                        'publish': ad_data.get('publish'),
                        'active': ad_data.get('is_active', True),
                        'end_time': int(datetime.datetime.strptime(ad_data['ad_delivery_stop_time'],
                                                                   "%Y-%m-%d %H:%M:%S").timestamp()) if ad_data.get(
                            'ad_delivery_stop_time') else None,
                        'platforms': ','.join(ad_data.get('platforms', [])) if isinstance(ad_data.get('platforms'),
                                                                                          list) else ad_data.get(
                            'platforms'),
                        'ad_type': ad_data.get('display_format'),
                        'ad_link': ad_data['items'][0]['link_url'] if ad_data.get('items') else None,
                        'ad_text': ad_data['items'][0]['body'] if ad_data.get('items') else None,
                        'link_type': ad_data['items'][0]['cta_type'] if ad_data.get('items') else None,
                        'ad_src': ad_data['items'][0]['ad_src'] if ad_data.get('items') else None,
                        'fp_id': ad_data.get('fp_id')
                    }
                    new_ad = Ad(**ad_record_data)
                    session.add(new_ad)
                    logger.info(f"Добавлено объявление {ad_data['ad_id']} в сессию.")
                    global count_added_cards
                    count_added_cards += 1
                    logger.info("Количество добавленных в бд данных: " + str(count_added_cards))

                    # Коммит с повторными попытками
                    await commit_with_retry(session, ad_data['ad_id'])

                except Exception as e:
                    await session.rollback()
                    logger.error(f"Ошибка при сохранении объявления {ad_data['ad_id']}: {e}")
                finally:
                    write_queue.task_done()
        except Exception as e:
            logger.error(f"Неожиданная ошибка в writer_coroutine: {e}")


async def info_writer_coroutine(session_factory):
    logger.debug("Запущен info_writer_coroutine.")
    while True:
        try:
            info_data = await info_write_queue.get()
            if info_data is None:
                logger.debug("Получен сигнал завершения info_writer_coroutine.")
                info_write_queue.task_done()
                break

            logger.debug(f"Получены данные из очереди: {info_data['link']} ({info_data['date']})")
            async with session_factory() as session:
                try:
                    existing_info = await session.execute(
                        select(Info).where(
                            (Info.link == info_data['link']) & (Info.date == info_data['date'])
                        )
                    )
                    existing_info = existing_info.scalar_one_or_none()

                    if existing_info:
                        logger.debug(
                            f"Запись с link {info_data['link']} за {info_data['date']} уже существует. Обновление.")
                        for key, value in info_data.items():
                            setattr(existing_info, key, value)
                    else:
                        new_info = Info(**info_data)
                        session.add(new_info)
                        logger.debug(f"Добавлена новая статистика {info_data['link']} за {info_data['date']} в сессию.")

                    await commit_with_retry(session, f"{info_data['link']} ({info_data['date']})")

                except Exception as e:
                    await session.rollback()
                    logger.error(f"Ошибка при сохранении статистики {info_data['link']} за {info_data['date']}: {e}")
                finally:
                    info_write_queue.task_done()
        except Exception as e:
            logger.error(f"Неожиданная ошибка в info_writer_coroutine: {e}")


def extract_archive_id(file_path):
    file_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(file_name)[0]
    parts = name_without_ext.split('_')
    if parts:
        return parts[0]
    return None


count_deleted_files = 0


async def remove_unused_files(db: AsyncSession):
    """Удаляет файлы из папки assets, если их нет в БД."""
    async with db.begin():
        result = await db.execute(select(Ad.ad_src).where(Ad.ad_src.isnot(None)))
        db_files = set(result.scalars().all())  # Получаем set имен файлов из БД

    if not os.path.exists(MEDIA_FOLDER):
        logger.warning(f"Директория {MEDIA_FOLDER} не существует.")
        return

    files_in_dir = {f for f in os.listdir(MEDIA_FOLDER) if "preview" not in f}

    unused_files = files_in_dir - db_files  # Файлы, которых нет в БД

    if unused_files:
        global count_deleted_files
        for file_name in unused_files:
            file_path = os.path.join(MEDIA_FOLDER, file_name)
            try:
                os.remove(file_path)
                count_deleted_files += 1
                logger.info(f"Удален файл: {count_deleted_files} - {file_name}, так как он отсутствует в БД.")
                # Если удаленный файл был видео (.mp4), удаляем его превью
                if file_name.endswith(".mp4"):
                    preview_file = f"{file_name[:-4]}_preview.jpg"
                    preview_path = os.path.join(MEDIA_FOLDER, preview_file)
                    try:
                        os.remove(preview_path)
                        count_deleted_files += 1
                        logger.info(f"Также удален файл превью: {count_deleted_files} - {preview_file}")
                    except FileNotFoundError:
                        logger.warning(f"Файл превью {preview_file} не найден, пропускаем.")
                    except Exception as e:
                        logger.error(f"Ошибка при удалении превью {preview_file}: {e}")
            except Exception as e:
                logger.error(f"Ошибка при удалении {file_name}: {e}")


async def has_moov_atom(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        cap.release()
        return False

    ret, _ = cap.read()
    cap.release()
    return ret  # Если кадр не прочитан, значит проблема с moov


invalid_video_counter = 0


async def check_and_delete_invalid_videos(folder_path):
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

    # Получаем список видеофайлов и изображений
    files = [
        os.path.join(folder_path, file)
        for file in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, file))
    ]

    video_files = [f for f in files if os.path.splitext(f)[1].lower() in video_extensions]

    for file_path in video_files:
        global invalid_video_counter
        invalid_video_counter += 1
        logger.info(f"Количество проверенных файлов: {invalid_video_counter}/{len(video_files)}")

        if not await has_moov_atom(file_path):
            logger.info(f"Удаление поврежденного файла: {file_path}")
            os.remove(file_path)


async def cv2_duplicates_check(ads_session_factory, max_concurrent_tasks=5):
    if not os.path.exists(MEDIA_FOLDER):
        logger.error(f"Директория {MEDIA_FOLDER} не существует.")
        return

    video_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

    # Получаем список видеофайлов и изображений
    files = [
        os.path.join(MEDIA_FOLDER, file)
        for file in os.listdir(MEDIA_FOLDER)
        if os.path.isfile(os.path.join(MEDIA_FOLDER, file))
    ]

    video_files = [f for f in files if os.path.splitext(f)[1].lower() in video_extensions]
    image_files = [f for f in files if os.path.splitext(f)[1].lower() in image_extensions]

    logger.info(f"Найдено {len(video_files)} видеофайлов и {len(image_files)} изображений для проверки.")

    unique_files = []
    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def check_duplicate(file):
        nonlocal unique_files

        async with semaphore:
            is_duplicate = False
            for original_file in unique_files:
                if await are_files_identical(file, original_file):
                    logger.info(f"Найден дубликат файла: {file}")
                    await process_duplicates(file, ads_session_factory)
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_files.append(file)
                logger.info(f"Количество уникальных элементов: {len(unique_files)}")

    await asyncio.gather(*(check_duplicate(file) for file in video_files + image_files))


async def are_files_identical(file1, file2):
    ext1, ext2 = os.path.splitext(file1)[1].lower(), os.path.splitext(file2)[1].lower()
    if ext1 in ['.mp4', '.avi', '.mov', '.mkv'] and ext2 in ['.mp4', '.avi', '.mov', '.mkv']:
        return await are_videos_identical(file1, file2)
    elif ext1 in ['.jpg', '.jpeg', '.png', '.bmp', '.gif'] and ext2 in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
        return are_images_identical(file1, file2)
    return False


async def are_videos_identical(video1_path, video2_path):
    try:
        if not os.path.exists(video1_path) or not os.path.exists(video2_path):
            return False

        if os.path.getsize(video1_path) != os.path.getsize(video2_path):
            return False

        cap1, cap2 = cv2.VideoCapture(video1_path), cv2.VideoCapture(video2_path)
        if not cap1.isOpened() or not cap2.isOpened():
            return False

        if int(cap1.get(cv2.CAP_PROP_FRAME_COUNT)) != int(cap2.get(cv2.CAP_PROP_FRAME_COUNT)):
            return False

        key_frames = [1, 50, 100]
        hashes1, hashes2 = [], []

        for frame_num in key_frames:
            cap1.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            cap2.set(cv2.CAP_PROP_POS_FRAMES, frame_num)

            ret1, frame1 = cap1.read()
            ret2, frame2 = cap2.read()

            if not ret1 or not ret2:
                break

            frame1, frame2 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY), cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            hash1, hash2 = imagehash.phash(Image.fromarray(frame1)), imagehash.phash(Image.fromarray(frame2))

            hashes1.append(hash1)
            hashes2.append(hash2)

        cap1.release()
        cap2.release()

        matches = sum(h1 - h2 <= 10 for h1, h2 in zip(hashes1, hashes2))
        return matches / len(hashes1) >= 0.9 or compare_videos_ssim(video1_path, video2_path)
    except:
        return False


def compare_videos_ssim(video1_path, video2_path):
    cap1, cap2 = cv2.VideoCapture(video1_path), cv2.VideoCapture(video2_path)
    cap1.set(cv2.CAP_PROP_POS_FRAMES, 50)
    cap2.set(cv2.CAP_PROP_POS_FRAMES, 50)

    ret1, frame1 = cap1.read()
    ret2, frame2 = cap2.read()

    cap1.release()
    cap2.release()

    if not ret1 or not ret2:
        return False

    frame1, frame2 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY), cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(frame1, frame2, full=True)

    return score > 0.9


def are_images_identical(image1_path, image2_path):
    try:
        if not os.path.exists(image1_path) or not os.path.exists(image2_path):
            return False

        if os.path.getsize(image1_path) != os.path.getsize(image2_path):
            return False

        img1, img2 = Image.open(image1_path).convert('L'), Image.open(image2_path).convert('L')
        hash1, hash2 = imagehash.phash(img1), imagehash.phash(img2)

        if hash1 - hash2 <= 10:
            return True

        img1, img2 = cv2.imread(image1_path, cv2.IMREAD_GRAYSCALE), cv2.imread(image2_path, cv2.IMREAD_GRAYSCALE)
        score, _ = ssim(img1, img2, full=True)

        return score > 0.9
    except:
        return False


async def process_duplicates(duplicate_file, session_factory):
    """
    Обрабатывает дубликаты: удаляет файл, перемещает archive_id в таблицу duplicate_ads и удаляет запись из таблицы ads.
    """
    archive_id = extract_archive_id(duplicate_file)
    now = datetime.datetime.now()
    date_key = now.strftime("%d-%m-%Y")
    removed = False
    for key in link_download_resources_counter.get(date_key, {}):
        if archive_id in link_download_resources_counter[date_key][key]:
            link_download_resources_counter[date_key][key].remove(archive_id)
            removed = True
            break
    if not removed:
        for date in list(link_download_resources_counter.keys()):
            for key in link_download_resources_counter[date]:
                if archive_id in link_download_resources_counter[date][key]:
                    link_download_resources_counter[date][key].remove(archive_id)
                    removed = True
                    break
            if removed:
                break
    if not archive_id:
        logger.error(f"Не удалось извлечь archive_id из имени файла: {duplicate_file}")
        return

    if not archive_id:
        logger.error(f"Не удалось извлечь archive_id из имени файла: {duplicate_file}")
        return

    # Удаляем файл и его превью (если есть)
    try:
        os.remove(duplicate_file)
        logger.info(f"Удален дубликат файла {duplicate_file}")

        if duplicate_file.endswith(".mp4"):
            preview_file = f"{duplicate_file[:-4]}_preview.jpg"
            preview_path = os.path.join(MEDIA_FOLDER, preview_file)
            try:
                os.remove(preview_path)
                logger.info(f"Также удален файл превью: - {preview_file}")
            except FileNotFoundError:
                logger.warning(f"Файл превью {preview_file} не найден, пропускаем.")
            except Exception as e:
                logger.error(f"Ошибка при удалении превью {preview_file}: {e}")

    except Exception as e:
        logger.error(f"Ошибка при удалении {duplicate_file}: {e}")

    # Работаем с базой данных через одно соединение
    async with session_factory() as session:
        async with session.begin():
            try:
                # Ищем рекламу по archive_id
                result = await session.execute(select(Ad).where(Ad.archive_id == archive_id))
                ad = result.scalar_one_or_none()

                if ad:
                    if ad.display_format != 'dco' and ad.display_format != 'dpa':
                        # Перемещаем archive_id в duplicate_ads
                        await session.execute(
                            text("INSERT OR IGNORE INTO duplicate_ads (archive_id) VALUES (:archive_id)"),
                            {'archive_id': archive_id}
                        )
                        logger.info(f"Перемещен archive_id {archive_id} в таблицу duplicate_ads")

                        # Удаляем запись из ads
                        await session.delete(ad)
                        logger.info(f"Удален archive_id {archive_id} из таблицы ads")
                    else:
                        logger.info(f"Дубликат рекламы {archive_id} имеет display_format 'DCO'; не удаляется")
                else:
                    logger.error(f"Реклама с archive_id {archive_id} не найдена в базе данных")

                await session.commit()

            except SQLAlchemyError as e:
                logger.error(f"Ошибка при обработке дубликатов: {e}")
                await session.rollback()


async def update_cookie():
    try:
        global cookie_data_index
        global cookies
        while True:
            index = random.randint(0, len(cookies) - 1)
            if index in cookie_data_index:
                continue
            else:
                cookie_data_index.append(index)
                logger.info(f'Индекс используемого куки: {index}')
                break
        key = list(cookies.keys())[index]
        c_user_value = key
        xs_value = cookies[key]
        return [
            {
                "domain": ".facebook.com",
                "httpOnly": False,
                "name": "c_user",
                "path": "/",
                "secure": True,
                "value": c_user_value
            },
            {
                "domain": ".facebook.com",
                "httpOnly": True,
                "name": "xs",
                "path": "/",
                "secure": True,
                "value": xs_value
            }
        ]
    except (FileNotFoundError, json.JSONDecodeError, IndexError) as e:
        logger.error(f"Ошибка обновления cookies: {e}")
        raise


# Асинхронная функция для загрузки файлов
def get_content_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)  # Получаем MIME-тип по расширению файла
    if mime_type is None:
        return None  # Если MIME-тип не определен, возвращаем None
    # Проверяем, является ли MIME-тип изображением или видео
    if mime_type.startswith('image'):
        return mime_type  # Тип изображения, например, image/jpeg
    elif mime_type.startswith('video'):
        return mime_type  # Тип видео, например, video/mp4
    return None  # Если файл не является изображением или видео, возвращаем None


# Асинхронная функция для загрузки файла на Backblaze B2
async def upload_file_to_backblaze(file_path, src_name, bucket):
    content_type = get_content_type(file_path)  # Автоматически определяем тип контента

    if content_type is None:
        logger.error(f"Файл {src_name} не является изображением или видео. Пропускаем.")
        return  # Пропускаем файлы, которые не являются изображениями или видео

    try:
        await asyncio.to_thread(bucket.get_file_info_by_name, src_name)  # Выполнение синхронной функции в потоке
        logger.info('Файл с таким именем уже загружен на backblaze.com')
    except FileNotPresent:
        logger.debug(f"Начало загрузки {src_name} на Backblaze B2.")
        async with aiofiles.open(file_path, 'rb') as file:
            file_content = await file.read()  # Асинхронно читаем содержимое файла
            await asyncio.to_thread(bucket.upload_bytes, file_content, src_name,
                                    content_type)  # Загружаем файл в отдельном потоке
        logger.debug(f"Файл {src_name} успешно загружен на Backblaze B2.")


async def get_proxy():
    with open('settings/proxy.json', 'r') as file:
        proxy = json.loads(file.read())
    if proxy:
        logger.info("Прокси успешно получены")
        return proxy
    return None


async def remove_ads_with_missing_files(db_sessionmaker, statistic_db):
    deleted_files = []
    async with db_sessionmaker() as db:  # Создаём экземпляр сессии
        async with db.begin():
            result = await db.execute(select(Ad))
            ads = result.scalars().all()

            ads_to_delete = []

            for ad in ads:
                if ad.ad_src:
                    file_names = [name.strip() for name in ad.ad_src.split(',')]
                    existing_files = []
                    for file_name in file_names:
                        file_path = os.path.join(MEDIA_FOLDER, file_name)
                        if os.path.exists(file_path):
                            existing_files.append(file_name)
                        else:
                            deleted_files.append(file_path)
                            logger.info(f"Файл не найден и будет удалён из ad.ad_src: {file_path}")

                    if existing_files:
                        ad.ad_src = ','.join(existing_files)
                    else:
                        ads_to_delete.append(ad)

            if ads_to_delete:
                for ad in ads_to_delete:
                    await db.delete(ad)
                await db.commit()
                logger.info(f"Удалено {len(ads_to_delete)} записей с отсутствующими файлами.")
            else:
                logger.info("Все файлы на месте, удаление не требуется.")
    deleted_files = [re.search(r'(\d+)_', f).group(1) for f in deleted_files if re.search(r'(\d+)_', f)]
    async with statistic_db() as session:
        async with session.begin():
            result = await session.execute(select(Info))
            rows = result.scalars().all()

            for row in rows:
                if row.archive_id:
                    archive_list = row.archive_id.split(", ")
                    updated_list = [file for file in archive_list if file not in deleted_files]

                    if len(updated_list) < len(archive_list):  # Если что-то удалилось
                        row.archive_id = ", ".join(updated_list) if updated_list else None
                        row.unique_elements = max(0, row.unique_elements - (len(archive_list) - len(updated_list)))

            await session.commit()


async def get_cookies():
    global cookies
    try:
        with open('settings/cookies.json', 'r') as f:
            cookies = json.load(f)
    except FileNotFoundError:
        logger.error('Отсутствет файл "cookies.json". Завершение программы.')
        sys.exit()


async def get_statistic(session_factory):
    info_dict = {}
    async with session_factory() as session:
        try:
            result = await session.execute(select(Info.link, Info.date, Info.archive_id))
            rows = result.fetchall()

            for link, date, archive_id in rows:
                archive_list = archive_id.split(", ") if archive_id else []

                if date not in info_dict:
                    info_dict[date] = {}

                if link in info_dict[date]:
                    info_dict[date][link].extend(archive_list)
                else:
                    info_dict[date][link] = archive_list

            logger.debug(f"Загружены данные из info: {info_dict}")
        except Exception as e:
            logger.error(f"Ошибка при получении данных из info: {e}")

    return info_dict


excel_data = []


async def get_urls_from_excel():
    try:
        global excel_data
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)

        gc = gspread.authorize(creds)

        sh = gc.open(EXCEL_FILE_NAME)

        worksheet = sh.sheet1

        info = worksheet.get_all_values()[1:]

        seen = {}

        for row in info:
            key = row[3].lower()
            country = row[2]
            problem = row[4]

            full_key = (key, country)

            if full_key in seen:
                existing_row = seen[full_key]
                if problem != existing_row[4]:
                    existing_problems = set(existing_row[4].split(", "))
                    new_problems = set(problem.split(", "))
                    combined = ", ".join(sorted(existing_problems | new_problems))
                    existing_row[4] = combined
            else:
                seen[full_key] = row
                excel_data.append(row)

        grouped_by_key = defaultdict(list)
        for row in excel_data:
            grouped_by_key[row[3]].append(row)

        for rows in grouped_by_key.values():
            if len(rows) > 1:
                rows.sort(key=lambda r: len(set(r[4].split(", "))), reverse=True)
                max_problems = set(rows[0][4].split(", "))
                for r in rows[1:]:
                    current_problems = set(r[4].split(", "))
                    updated = ", ".join(sorted(current_problems | max_problems))
                    r[4] = updated

        urls = []
        for link in excel_data[1:]:
            if link[1].startswith('https'):
                if len(link) >= 6:
                    if 'start_date[min]=' not in link[1]:
                        if link[6] != '':
                            link[1] += f'&start_date[min]={link[6]}&start_date[max]'
                    else:
                        parsed_url = urlparse(link[1])
                        query_params = parse_qs(parsed_url.query)
                        query_params['start_date[min]'] = [link[6]]
                        new_query = urlencode(query_params, doseq=True)
                        link[1] = urlunparse(parsed_url._replace(query=new_query))
                        link[1] += '&start_date[max]'
                    urls.append(link[1])
            else:
                urls.append(
                    f'https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country={link[2]}&is_targeted_country=false&media_type=image_and_meme&q={link[3]}&search_type=keyword_unordered')
        if len(urls) == 0:
            logger.info("Количество полученных ссылок через excel = 0. Остановка скрипта.")
            sys.exit()
        else:
            logger.info(f"Общее количество полученных ссылок: {len(urls)}")
        completed_urls = await get_completed_urls()
        urls = [url for url in urls if url.split('&start_date[min]')[0] not in completed_urls]
        logger.info(f'Количество urls после отсеивания: {len(urls)}')
        urls = urls[:100]
        clean_urls = [url.split('&start_date[min]')[0] for url in urls]
        excel_data = [elements for elements in excel_data if elements[1].split('&start_date[min]')[0] in clean_urls]
        return urls, completed_urls
    except Exception as e:
        logger.error(f'Возникла ошибка при чтении excel файла: {e}')


async def update_excel():
    global excel_data  # список списков: каждый row должен содержать минимум 3 элемента

    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open(EXCEL_FILE_NAME)
    worksheet = sh.sheet1

    headers = worksheet.row_values(1)

    if "Последний Парсинг" not in headers:
        headers.append("Последний Парсинг")
        worksheet.update(values=[headers], range_name='A1')
        style = get_user_entered_format(worksheet, 'A1')
        format_cell_range(worksheet, f"{gspread.utils.rowcol_to_a1(len(headers), 1)}", style)

    # Индекс колонки для "Последний Парсинг"
    last_parse_index = headers.index("Последний Парсинг")

    # Получаем все строки (кроме заголовка)
    all_rows = worksheet.get_all_values()[1:]  # без заголовка
    current_time = datetime.datetime.now().strftime("%Y-%m-%d")

    # Обновляем только строки, у которых совпадает 2-й и 3-й элемент
    updates = []
    row_indexes = []

    for i, row in enumerate(all_rows):
        for new_row in excel_data:
            if len(new_row) < 3 or len(row) < 3:
                continue

            if row[2] == new_row[2] and row[3] == new_row[3]:
                while len(row) < len(headers):
                    row.append("")
                row[last_parse_index] = current_time

                updates.append(row)
                row_indexes.append(i + 2)  # Excel rows start at 1, skip header
                break

    # Пакетное обновление
    if updates:
        start_row = min(row_indexes)
        end_row = max(row_indexes)
        range_a1 = f"A{start_row}:{gspread.utils.rowcol_to_a1(end_row, len(headers))}"

        # Подготовка всех строк (включая пропуски между ними, если есть)
        update_matrix = worksheet.get_values(f"A{start_row}:{gspread.utils.rowcol_to_a1(end_row, len(headers))}")

        for idx, row_num in enumerate(range(start_row, end_row + 1)):
            if row_num in row_indexes:
                update_matrix[idx] = updates[row_indexes.index(row_num)]

        worksheet.update(range_name=range_a1, values=update_matrix)

    logger.info("Завершено обновление совпадающих строк.")



async def get_completed_urls():
    if os.path.exists(COMPLETED_URL):
        async with aiofiles.open(COMPLETED_URL, mode='r', encoding='utf-8') as f:
            lines = await f.readlines()
            return [line.strip() for line in lines if line.strip()]
    return []


async def mark_url_as_completed(completed_urls: list[str]):
    async with aiofiles.open(COMPLETED_URL, mode='w', encoding='utf-8') as f:
        for url in completed_urls:
            await f.write(url.strip() + '\n')


# Основная функция
async def main():
    global data
    download_tasks = []
    await init_db()

    await get_cookies()
    global link_download_resources_counter
    link_download_resources_counter = await get_statistic(InfoSessionLocal)
    settings_folder = 'settings'
    domains_file = os.path.join(settings_folder, 'exclude_domains.json')

    if not os.path.exists(domains_file):
        logger.error(f"Domains file {domains_file} does not exist.")
        return

    os.makedirs(MEDIA_FOLDER, exist_ok=True)

    with open(domains_file, 'r', encoding='utf-8') as f:
        domains_data = json.load(f)
        domains = domains_data.get('domains', [])

        if not domains:
            logger.error("No domains found in the exclude domains file.")
            return

    # Парсинг прокси и создание семафоров
    all_proxies = []
    proxy_semaphores = {}
    proxies_data = await get_proxy()
    for proxy_item in proxies_data:
        proxy = {
            "server": proxy_item,
            "username": os.getenv('PROXY_USERNAME'),
            "password": os.getenv('PROXY_PASSWORD')
        }
        all_proxies.append(proxy)
        proxy_semaphores[proxy['server']] = asyncio.Semaphore(2)
    urls, completed_urls = await get_urls_from_excel()
    global data
    data['data'].extend({'link': url} for url in urls)
    country_start_time = time.time()

    now = datetime.datetime.now()
    link_download_resources_counter.setdefault(now.strftime("%d-%m-%Y"), {})

    async with async_playwright() as p:
        writer_task = asyncio.create_task(writer_coroutine(AsyncSessionLocal))
        info_writer_task = asyncio.create_task(info_writer_coroutine(InfoSessionLocal))


        batches = [urls[i:i + 3] for i in range(0, len(urls), 3)]

        for batch_number, batch in enumerate(batches, start=1):
            logger.info(f"Обработка батча {batch_number}/{len(batches)}.")
            batch_start_time = time.time()

            tasks = []
            random.shuffle(batch)

            for url in batch:
                batch_cookies = await update_cookie()
                random.shuffle(all_proxies)

                for proxy in all_proxies:
                    semaphore = proxy_semaphores[proxy['server']]
                    # Проверяем, доступен ли прокси (не более 2 задач)
                    if semaphore.locked() and semaphore._value == 0:
                        continue  # Этот прокси уже используется в 2 задачах
                    else:
                        # Нашли доступный прокси
                        break
                else:
                    logger.error("Нет доступных прокси для новой задачи.")
                    continue
                completed_urls.append(url.split('&start_date[min]')[0])
                await mark_url_as_completed(completed_urls)

                # Создаём задачу с использованием прокси и семафора
                task = asyncio.create_task(
                    process_task(p, url, AsyncSessionLocal, proxy, semaphore, download_tasks, domains,
                                 batch_cookies))
                tasks.append(task)

            # Запускаем задачи параллельно
            await asyncio.gather(*tasks)

            batch_elapsed_time = time.time() - batch_start_time
            formatted_batch_time = str(datetime.timedelta(seconds=batch_elapsed_time))
            logger.info(
                f"Батч {batch_number}/{len(batches)}  обработан за {formatted_batch_time}.")

        country_elapsed_time = time.time() - country_start_time
        formatted_country_time = str(datetime.timedelta(seconds=country_elapsed_time))
        logger.info(f"Обработка завершена за {formatted_country_time}.")

        duplicates_start_time = time.time()
        # await check_and_delete_invalid_videos(directory)
        await cv2_duplicates_check(AsyncSessionLocal)
        await remove_ads_with_missing_files(AsyncSessionLocal, InfoSessionLocal)
        duplicates_elapsed_time = time.time() - duplicates_start_time
        formatted_duplicates_time = str(datetime.timedelta(seconds=duplicates_elapsed_time))
        logger.info(f"Обработку дублей завершено за {formatted_duplicates_time}.")

        await update_info_table(InfoSessionLocal, link_download_resources_counter)
        await clean_info_db()
        async with AsyncSessionLocal() as db:
            await remove_unused_files(db)
        await merge_ads_data()
        await write_queue.join()
        await write_queue.put(None)
        await info_write_queue.join()
        await info_write_queue.put(None)
        await info_writer_task
        await writer_task

    # Ожидаем завершения всех задач загрузки
    if download_tasks:
        await asyncio.gather(*download_tasks)

    await delete_ads_with_patterns()
    await check_and_delete_missing_files()
    await update_excel()
    os.remove(PROCESS_END)
    logger.info("Скрипт завершён.")


async def update_info_table(session_factory, info_data):
    async with session_factory() as session:
        try:
            for date, link_data in info_data.items():
                for link, archive_list in link_data.items():
                    archive_str = ", ".join(map(str, archive_list))
                    unique_count = len(archive_list)

                    existing_info = await session.execute(
                        select(Info).where(Info.link == link, Info.date == date)
                    )
                    existing_info = existing_info.scalar_one_or_none()

                    if existing_info:
                        existing_info.unique_elements = unique_count
                        existing_info.archive_id = archive_str
                        logger.debug(
                            f"Обновлена запись для {link} (дата: {date}): unique_elements={unique_count}"
                        )
                    else:
                        new_info = Info(
                            link=link,
                            date=date,
                            country="Unknown",
                            elements=unique_count,
                            unique_elements=unique_count,
                            archive_id=archive_str
                        )
                        session.add(new_info)
                        logger.debug(f"Добавлена новая запись для {link} (дата: {date})")

            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Ошибка при обновлении таблицы info: {e}")


async def merge_ads_data():
    try:
        async with aiosqlite.connect("ads_data_copy.db") as source_db, \
                aiosqlite.connect("ads_data.db") as dest_db:
            source_cursor = await source_db.execute("SELECT * FROM ads")
            ads_copy = await source_cursor.fetchall()

            # Получаем данные из оригинальной базы
            dest_cursor = await dest_db.execute("SELECT * FROM ads")
            ads_original = await dest_cursor.fetchall()

            # Объединяем данные, избегая дубликатов
            ads_combined = list({tuple(ad) for ad in ads_copy + ads_original})

            await dest_db.execute("DELETE FROM ads")
            placeholders = ", ".join(["?"] * 18)
            await dest_db.executemany(f"INSERT INTO ads VALUES ({placeholders})", ads_combined)
            await dest_db.commit()
            logger.info("Данные успешно перенесены и объединены в ads_data.db")

        # Удаляем временный файл
        os.remove("ads_data_copy.db")
        logger.info("Файл ads_data_copy.db удалён")
    except Exception as e:
        logger.error(f"Ошибка при переносе данных: {e}")


def clean_ad_src(ad_src: str) -> str:
    """Обрезает ad_src до первого символа _ включительно справа."""
    return ad_src.rsplit("_", 1)[0] if "_" in ad_src else ad_src


async def get_ad_src_from_ads_db() -> set:
    """Получает все ad_src из ads_data.db и очищает их."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Ad.ad_src))
        ad_src_set = set()
        for row in result.scalars():
            if row:
                ad_src_set.update(clean_ad_src(src.strip()) for src in row.split(", "))
    return ad_src_set


REGEXP_PATTERNS = [
    '/share/middle', 'products', 'book_id', 'chapter', 'goodreels', 'Favoread',
    'noveltells', 'beenovels', 'readinkapp', 'goodnovel', 'stardust-tv', 'dramabox',
    'new-media', 'hishorttv', 'dramawave', 'readlife', 'yumread', 'novel',
    'mercurytheatre', 'ticketsource', 'getpassionapp', 'com.dreame.reader',
    'novreadtech', 'shorttv', 'lightreader', 'tapon.com', 'musl.ink',
    'healthylabco', 'product'
]


async def delete_ads_with_patterns():
    async with AsyncSessionLocal() as session:
        for pattern in REGEXP_PATTERNS:
            await session.execute(delete(Ad).where(Ad.ad_src.like(f"%{pattern}%")))
            await session.execute(delete(Ad).where(Ad.ad_text.like(f"%{pattern}%")))
        await session.commit()
        logger.info("Удалены объявления с нежелательными шаблонами.")


async def check_and_delete_missing_files():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Ad).where(Ad.ad_src.isnot(None)))
        ads = result.scalars().all()

        ads_to_delete = []

        for ad in ads:
            file_names = ad.ad_src.split(', ')
            for file_name in file_names:
                file_path = os.path.join(MEDIA_FOLDER, file_name)
                if not os.path.exists(file_path):
                    ads_to_delete.append(ad)
                    break

        if ads_to_delete:
            for ad in ads_to_delete:
                await session.delete(ad)
            await session.commit()
            logger.info(f"Удалено объявлений: {len(ads_to_delete)}")
        else:
            logger.info("Все файлы на месте.")


async def clean_info_db():
    """Очищает таблицу info от ненужных archive_id и удаляет дубликаты, удаляя более новые записи."""
    ad_src_set = await get_ad_src_from_ads_db()

    async with InfoSessionLocal() as session:
        result = await session.execute(select(Info))
        infos = result.scalars().all()

        now_date = datetime.datetime.strptime(datetime.datetime.now().strftime("%d-%m-%Y"), "%d-%m-%Y")

        # Словарь для отслеживания уникальных archive_id и их записей

        for info in infos:
            if info.archive_id:
                archive_ids = set(info.archive_id.split(", "))

                # Удаляем отсутствующие в ads_data.db archive_id
                missing_ids = archive_ids - ad_src_set
                if missing_ids:
                    archive_ids -= missing_ids
                    info.archive_id = ", ".join(archive_ids) if archive_ids else None
                    info.unique_elements = max(0, info.unique_elements - len(missing_ids))

        result = await session.execute(select(Info))
        infos = sorted(result.scalars().all(), key=lambda x: datetime.datetime.strptime(x.date, "%d-%m-%Y"),
                       reverse=True)

        global_el = set()
        data = {}

        for info in infos:
            if info.archive_id:
                # Очищаем archive_id внутри одной ячейки
                unique_ids = list(info.archive_id.split(", "))
                removed_ids = 0
                data[info] = [0, []]
                for archive_id in unique_ids:
                    if archive_id in global_el:
                        for cell in data:
                            find = False
                            for number in data[cell][1]:
                                if archive_id == number:
                                    data[cell][1].remove(number)
                                    data[cell][0] += 1
                                    find = True
                                    break
                            if find:
                                break
                        else:
                            unique_ids.remove(archive_id)
                            removed_ids += 1
                            data[info][0] = removed_ids
                        logger.info(f"Удалён {archive_id}")
                    else:
                        global_el.add(archive_id)

                data[info][1] = unique_ids

        for cell in data:
            cell.archive_id = ", ".join(data.get(cell)[1])
            cell.unique_elements = cell.unique_elements - data.get(cell)[0]
        await session.commit()
        logger.info("Очистка завершена.")


async def process_task(playwright, url, SessionLocal, proxy, semaphore, download_tasks, domains,
                       batch_cookies):
    async with semaphore:
        try:
            await process_url(
                playwright=playwright,
                page_url=url,
                SessionLocal=SessionLocal,
                proxy=proxy,
                download_tasks=download_tasks,
                scroll_duration=1250,
                exclude_domains=domains,
                batch_cookies=batch_cookies
            )
        except Exception as e:
            logger.error(f"Ошибка при обработке URL {url}: {e}")


def get_links(country, count):
    logger.info(f"Получаем {count} ссылок для {country}")
    url = "https://mtw.rest/api/v2/gambling/links/get_links.php"
    params = {
        "count": count,
        "geo": country
    }
    headers = {
        "X-Token": "AuKQ6CuEPpcdQktu1MDm2BeeBMGx4MCjV0gE9a1bmlCUTlxaMB0YhyEvbC8lDybu"
    }

    response = requests.get(url, json=params, headers=headers)
    if response.status_code == 200:
        logger.info("Ссылки успешно получены")
        return response.json()
    else:
        return None


def create_lock_file():
    with open(LOCK_FILE, "w") as f:
        f.write("Running")


def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def is_already_running():
    return os.path.exists(LOCK_FILE)


def copy_ads_db():
    source = "ads_data.db"
    destination = "ads_data_copy.db"

    try:
        shutil.copy2(source, destination)
        logger.info(f"Файл {source} успешно скопирован в {destination}")
    except FileNotFoundError:
        logger.error(f"Ошибка: файл {source} не найден")
    except PermissionError:
        logger.error("Ошибка: недостаточно прав для копирования файла")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")


def check_memory_usage(threshold=90):
    memory = psutil.virtual_memory()
    used_percent = memory.percent

    if used_percent > threshold:
        logger.error(
            f"⚠️ Внимание: Использовано {used_percent:.2f}% памяти! Свободной памяти осталось меньше {100 - threshold}%.")
        return False
    else:
        logger.info(f"✅ Памяти достаточно: Использовано {used_percent:.2f}%, свободно {100 - used_percent:.2f}%.")
        return True


if __name__ == "__main__":
    try:
        remove_lock_file()
        if is_already_running():
            logger.error("Скрипт уже запущен")
            sys.exit()
        create_lock_file()
        if not os.path.exists(PROCESS_END):
            copy_ads_db()
            with open(PROCESS_END, "w") as file:
                file.write("Process not ended.")
        else:
            logger.info("В прошлый раз процесс не был завершён. База данных не скопирована")
        data = {'data': []}
        if check_memory_usage():
            asyncio.run(main())
    finally:
        remove_lock_file()
