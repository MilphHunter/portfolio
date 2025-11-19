import asyncio
import json
import os
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
from urllib.parse import urlparse, urlencode

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Error as PWError
from starlette.responses import JSONResponse

from fastapi import FastAPI, HTTPException
from starlette.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
JSON_FOLDER_NAME = "json_results"


class ScrapeHelpers:
    """Общие утилиты: UA/viewport, паузы/ретраи, создание браузера/контекста, клики по cookies, скроллы, блокировщик сетки."""

    DEFAULT_ARGS = [
        "--disable-background-networking",
        "--disable-background-timer-throttling",
        "--disable-renderer-backgrounding",
        "--disable-features=Translate",
        "--no-sandbox",
    ]

    @staticmethod
    def pick_user_agent(candidates: list[str]) -> str:
        """
        Возвращает случайный User-Agent из списка `candidates`.
        Если в окружении задан USER_AGENT, используется он.
        """
        return os.getenv("USER_AGENT") or random.choice(candidates)

    @staticmethod
    def random_viewport():
        """
        Генерирует случайные размеры окна браузера (viewport) и коэффициент масштабирования.
        """
        w = random.choice([1200, 1280, 1366, 1440, 1536, 1600, 1680, 1920])
        h = random.choice([720, 800, 864, 900, 960, 1024, 1080])
        return {"width": w, "height": h, "device_scale_factor": random.choice([1, 1.25, 1.5])}

    @staticmethod
    def jitter(a=0.35, b=0.85):
        """
        Возвращает случайное число с плавающей точкой в диапазоне [a, b].
        Используется для имитации случайных пауз (антибот-поведение).
        """
        return random.uniform(a, b)

    @staticmethod
    async def retry_async(coro_factory, retries=2, base=0.8, jitter_bounds=(0.2, 0.6)):
        """
        Асинхронно выполняет функцию `coro_factory` с возможностью повторов при ошибках.
        Повторяет до `retries` раз, с экспоненциальной задержкой + случайный джиттер.
        """
        for attempt in range(retries + 1):
            try:
                return await coro_factory()
            except Exception:
                if attempt == retries:
                    raise
                jmin, jmax = jitter_bounds
                await asyncio.sleep((base * (2 ** attempt)) + ScrapeHelpers.jitter(jmin, jmax))

    @staticmethod
    async def accept_cookies_if_any(page):
        """
        Пытается принять cookies (кнопка согласия), если такой элемент найден на странице.
        """
        try:
            btn = await page.wait_for_selector(
                "#sp-cc-accept, input#sp-cc-accept, [name='accept'], [data-action-params*='accept']",
                timeout=2000
            )
            if btn:
                await asyncio.sleep(ScrapeHelpers.jitter(0.2, 0.6))
                await btn.click()
                await asyncio.sleep(ScrapeHelpers.jitter(0.2, 0.5))
        except:
            pass

    @staticmethod
    async def human_scroll(page, steps: int = 5, min_delta: int = 300, max_delta: int = 900):
        """
        Выполняет "человеческий" скролл страницы:
        несколько шагов со случайным смещением, имитируя прокрутку мышью.
        """
        for _ in range(steps):
            dy = random.randint(min_delta, max_delta)
            try:
                await page.mouse.wheel(0, dy)
            except Exception:
                await page.evaluate("window.scrollBy(0, arguments[0])", dy)
            await asyncio.sleep(ScrapeHelpers.jitter(0.25, 0.85))

    @staticmethod
    async def new_browser_and_context(
            pw,
            *,
            headless: bool,
            proxy: str | None,
            user_agent: str,
            stealth_script: str,
            extra_headers: dict[str, str] | None = None,
            add_cookies: list[dict] | None = [{"name": "session-token",
                                               "value": "KGPcrkW19a3g8d8gsuiw9eXKFNgaicLZ9XzWJvbxjeeInMja3gsUOIIaDqY+6AxKbmD4nqM/zzW/TcBQM78W6XLWjkYnPKWbGmdD+wK1pMUYxfHmSYiZtZ8w0XYVjeEbXAONuEeSw96+MoPWpVKQJYsbgji7QNmsggnFCLzpvEQ8uUAvuW81zCP2ZMSQEpplZTuH/pnSBwZXrAqN72kuTrSAihPzGbGuKtDk3UcEyx6X10PvIIazjFoKEv6Ug33r8GoqUCola6EYlJOiffrKOkiV06uiusf2uCsopLqQIqPgdHgfqR/zwJFyg5LoKle9Uw8DZ9jYX2AUJgIz5NcDapDn0mC+qZbq",
                                               "domain": ".amazon.com", "path": "/", "httpOnly": True, "secure": True},
                                              {"name": "session-id", "value": "146-5002975-9384914",
                                               "domain": ".amazon.com", "path": "/", "httpOnly": True, "secure": True},
                                              {"name": "session-id-time", "value": "2082787201l",
                                               "domain": ".amazon.com", "path": "/", "httpOnly": True, "secure": True},
                                              {"name": "ubid-main", "value": "133-0690448-2083543",
                                               "domain": ".amazon.com", "path": "/", "httpOnly": True, "secure": True}],
            service_workers: str = "block",
    ):
        """
        Создаёт новый браузер и контекст в Playwright с настройками:
        - headless/видимый режим
        - поддержка прокси
        - случайный viewport
        - кастомные заголовки
        - подключение stealth-скрипта
        - установка cookies (по умолчанию Amazon-сессия)
        """
        launch_kwargs = {"headless": headless, "args": ScrapeHelpers.DEFAULT_ARGS.copy()}
        if proxy:
            launch_kwargs["proxy"] = {"server": proxy}
        browser = await pw.chromium.launch(**launch_kwargs)

        vp = ScrapeHelpers.random_viewport()
        headers = {"Accept-Language": "en-US,en;q=0.9", "DNT": "1", "Upgrade-Insecure-Requests": "1"}
        if extra_headers:
            headers.update(extra_headers)

        context = await browser.new_context(
            user_agent=user_agent,
            locale="en-US",
            viewport={"width": vp["width"], "height": vp["height"]},
            device_scale_factor=vp["device_scale_factor"],
            extra_http_headers=headers,
            service_workers=service_workers,
        )
        await context.add_init_script(stealth_script)
        if add_cookies:
            await context.add_cookies(add_cookies)
        return browser, context

    @staticmethod
    def make_generic_blocker(exempt_substr: str | None = None):
        """
        Создаёт функцию-блокировщик сетевых запросов для Playwright.
        Блокирует картинки, шрифты, рекламу и аналитику.
        Если задан `exempt_substr`, то запросы, содержащие эту подстроку, не блокируются.
        """
        def _block(rq):
            rt, u = rq.resource_type, rq.url
            if exempt_substr and exempt_substr in u:
                return False
            if rt in {"image", "media", "font", "stylesheet"}:
                return True
            if any(h in u for h in (
                    "amazon-adsystem.com", "doubleclick.net", "/uedata/", "/csm/",
                    "fls-na.amazon.com", "googletagmanager.com", "google-analytics.com",
                    "/beacon", "/pixel"
            )):
                return True
            if rt in {"xhr", "fetch"} and not (exempt_substr and exempt_substr in u):
                if any(p in u for p in ("/gp/product/", "/hz/")):
                    return False
                return True
            return False

        return _block


class MainPage:
    """Открывает страницу бестселлеров и выдает список ASIN из XHR 'componentbuilder'."""

    TARGET_SUBSTR = "componentbuilder"
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/126.0.0.0 Chrome/126.0.0.0 Safari/537.36",
    ]
    AMZN_HOSTS = (
        "amazon.com", "amazon.co.uk", "amazon.de", "amazon.it", "amazon.fr",
        "amazon.es", "amazon.ca", "amazon.com.au", "amazon.co.jp", "amazon.in",
        "media-amazon.com", "amazonaws.com"
    )
    USER_AGENT = ScrapeHelpers.pick_user_agent(USER_AGENTS)

    STEALTH_INIT = r"""
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    window.chrome = { runtime: {} };
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    try {
      const getParameter = WebGLRenderingContext.prototype.getParameter;
      WebGLRenderingContext.prototype.getParameter = function(parameter){
        if (parameter === 37445) return 'Intel Inc.';
        if (parameter === 37446) return 'Intel(R) Iris(TM) Graphics';
        return getParameter.apply(this, arguments);
      };
    } catch(e) {}
    """

    def __init__(self, url: str | None = None, timeout_sec: float = 60.0):
        self.url = url
        self.timeout_sec = timeout_sec

    def is_componentbuilder_request(self, url: str) -> bool:
        """
                Проверяет, относится ли URL к XHR/Fetch-запросу Amazon 'componentbuilder'
                (поиск подстроки TARGET_SUBSTR в пути и query). Возвращает True/False.
        """
        if not url:
            return False
        try:
            p = urlparse(url)
            candidate = (p.path or "") + "?" + (p.query or "")
        except Exception:
            candidate = url
        return self.TARGET_SUBSTR in candidate.lower()

    def _is_amazon_host(self, url: str) -> bool:
        """
        Определяет, принадлежит ли URL доменам Amazon (amazon.com, media-amazon.com и т.п.).
        Возвращает True/False.
        """
        try:
            host = urlparse(url).netloc.lower()
        except Exception:
            return False
        return any(host.endswith(h) for h in self.AMZN_HOSTS)

    def should_block(self, req):
        """
        Решает, нужно ли блокировать сетевой запрос Playwright.
        - Никогда не блокирует componentbuilder и XHR/Fetch/preflight.
        - Для амазоновских хостов режет тяжелые ресурсы (картинки, медиа, шрифты).
        - Блокирует рекламу/аналитику и шумные ендпоинты.
        Возвращает True (блокировать) или False (пропустить).
        """
        rt, u = req.resource_type, req.url
        if self.is_componentbuilder_request(u) or rt in {"xhr", "fetch", "preflight"}:
            return False
        if self._is_amazon_host(u):
            return rt in {"image", "media", "font"}
        if any(s in u for s in ("amazon-adsystem.com", "doubleclick.net", "googletagmanager.com",
                                "google-analytics.com", "facebook.net", "/uedata/", "/csm/", "/beacon", "/pixel")):
            return True
        return False

    async def run(self):
        """
        Открывает страницу бестселлеров, перехватывает XHR/Fetch 'componentbuilder'
        и извлекает список ASIN из его POST-тела. Возвращает список ASIN или None при таймауте.
        Пошагово:
          1) Запускает браузер/контекст (stealth, UA, прокси, блокировки ресурсов).
          2) Навешивает обработчики request/response для поиска целевого запроса.
          3) Загружает страницу с повторами, принимает cookies, проверяет капчу.
          4) Ждёт появление полезной нагрузки и парсит asinList.
        """
        proxy = os.getenv("PROXY")
        async with async_playwright() as pw:
            browser, context = await ScrapeHelpers.new_browser_and_context(
                pw,
                headless=True,
                proxy=proxy,
                user_agent=self.USER_AGENT,
                stealth_script=self.STEALTH_INIT,
            )
            await context.route("**/*", lambda r: r.abort() if self.should_block(r.request) else r.continue_())
            page = await context.new_page()
            page.set_default_timeout(20000)

            found_payload = asyncio.get_event_loop().create_future()
            request_bodies = {}

            page.on(
                "request",
                lambda req: request_bodies.setdefault(
                    req, {"post_data": (req.post_data if req.method in ("POST", "PUT", "PATCH") else None)}
                ) if self.is_componentbuilder_request(req.url) and req.resource_type in {"xhr", "fetch"} else None
            )

            async def on_response(resp):
                """
                Обработчик ответов: если это целевой XHR/Fetch,
                читает сохранённое POST-тело запроса и извлекает asinList.
                """
                req = resp.request
                if not (self.is_componentbuilder_request(req.url) and req.resource_type in {"xhr", "fetch"}):
                    return
                try:
                    raw = request_bodies.get(req, {}).get("post_data")
                    if isinstance(raw, (bytes, bytearray)):
                        raw = raw.decode("utf-8", errors="replace")
                    data = json.loads(raw) if raw else {}
                    asin_list = data.get("adaptiveWidgetContext", {}).get("asinList")
                    if asin_list and not found_payload.done():
                        found_payload.set_result(asin_list)
                except Exception as e:
                    if not found_payload.done():
                        found_payload.set_exception(e)

            page.on("response", lambda r: asyncio.create_task(on_response(r)))

            async def goto_factory():
                """
                Обёртка для перехода на страницу с небольшим джиттером —
                используется в механизме повторов.
                """
                await asyncio.sleep(ScrapeHelpers.jitter())
                return await page.goto(self.url, wait_until="domcontentloaded", timeout=30000)

            try:
                await ScrapeHelpers.retry_async(goto_factory, retries=2, base=0.9)
                await asyncio.sleep(ScrapeHelpers.jitter(3, 6))
                await page.reload(wait_until="domcontentloaded")
            except Exception as e:
                await context.close()
                await browser.close()
                raise RuntimeError(f"Не удалось открыть страницу: {e}")

            await ScrapeHelpers.accept_cookies_if_any(page)

            if await page.query_selector("#captchacharacters, form[action*='validator'], form[action*='approach']"):
                await context.close()
                await browser.close()
                raise RuntimeError("CAPTCHA: измените прокси/профиль/частоту запросов.")

            try:
                asin_list = await asyncio.wait_for(found_payload, timeout=self.timeout_sec)
                print(f"[OK] Список asin найден: {asin_list}")
                return asin_list
            except asyncio.TimeoutError:
                print(f"[WARN] За {self.timeout_sec:.0f} с запрос '{self.TARGET_SUBSTR}' не обнаружен.")
                return None
            finally:
                await context.close()
                await browser.close()


class PagesParser:
    """Парсит карточки /dp/<ASIN>: DOM + AOD, параллельная обработка, сохранение JSON."""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/126.0.0.0 Chrome/126.0.0.0 Safari/537.36",
    ]
    USER_AGENT = ScrapeHelpers.pick_user_agent(USER_AGENTS)
    STEALTH_INIT = MainPage.STEALTH_INIT

    @staticmethod
    def to_float_money(s: str):
        """Преобразует строку с ценой в число float (учитывая точки и запятые)."""
        if not s:
            return None
        s = re.sub(r"[^0-9.,]", "", s)
        if s.count(",") == 1 and s.count(".") == 0:
            s = s.replace(",", ".")
        elif s.count(",") > 1:
            s = s.replace(",", "")
        try:
            return float(s)
        except ValueError:
            return None

    @staticmethod
    def asin_from_url(url: str):
        """Извлекает ASIN из URL вида /dp/ASIN."""
        m = re.search(r"/dp/([A-Z0-9]{10})", url)
        return m.group(1) if m else None

    @staticmethod
    async def extract_from_dom(page):
        """Выполняет JavaScript в DOM для извлечения данных о товаре (цена, рейтинг, отзывы, заголовок, фото и т.д.)."""
        script = r"""
() => {
  const getText = (sel) => document.querySelector(sel)?.textContent.trim() || '';
  const readMoney = (s) => {
    if (!s) return null;
    s = s.replace(/[^0-9.,]/g, '');
    if (s.includes(',') && !s.includes('.')) s = s.replace(',', '.');
    if ((s.match(/,/g)||[]).length > 1) s = s.replace(/,/g, '');
    const v = parseFloat(s);
    return Number.isFinite(v) ? v : null;
  };
  const priceSelectors = [
    '#corePriceDisplay_desktop_feature_div .a-price:not(.a-text-price) .a-offscreen',
    '#corePrice_feature_div .a-price:not(.a-text-price) .a-offscreen',
    '#apex_desktop .a-price:not(.a-text-price) .a-offscreen',
    'span.priceToPay .a-price .a-offscreen',
    '#price_inside_buybox',
    '#newBuyBoxPrice',
    '#priceblock_dealprice',
    '#priceblock_ourprice',
    '#sns-base-price',
    'div#buyNewSection .a-color-price'
  ];
  const isUnitPriceText = (t) => /\/|\bper\b|\beach\b/i.test(t);
  const priceTexts = priceSelectors
    .flatMap(sel => Array.from(document.querySelectorAll(sel)))
    .map(el => el.textContent.trim())
    .filter(t => t && !isUnitPriceText(t));
  let price = null;
  for (const t of priceTexts) {
    const v = readMoney(t);
    if (v && v > 0) { price = v; break; }
  }
  const listSelectors = [
    '#corePriceDisplay_desktop_feature_div .a-text-price .a-offscreen',
    '#price .a-text-price .a-offscreen',
    '.basisPrice .a-offscreen',
    '#listPrice'
  ];
  let list_price = null;
  for (const sel of listSelectors) {
    const el = document.querySelector(sel);
    if (el) { list_price = readMoney(el.textContent.trim()); if (list_price) break; }
  }
  if (!price) {
    const scripts = Array.from(document.querySelectorAll('script[type="application/ld+json"]'));
    for (const s of scripts) {
      try {
        const json = JSON.parse(s.textContent);
        const items = Array.isArray(json) ? json : [json];
        for (const it of items) {
          const offers = it?.offers;
          if (offers) {
            const offArr = Array.isArray(offers) ? offers : [offers];
            for (const off of offArr) {
              const pv = readMoney(String(off.price ?? off.lowPrice ?? off.highPrice ?? ''));
              if (pv && pv > 0) { price = pv; break; }
            }
          }
          if (price) break;
        }
      } catch {}
      if (price) break;
    }
  }
  let discount_percent = null;
  if (price != null && list_price != null && list_price > price) {
    discount_percent = Math.round((list_price - price) / list_price * 100);
  }
  const title = getText('#productTitle');
  const bullet_points = [...document.querySelectorAll('#feature-bullets li span.a-list-item')]
    .map(el => el.textContent.replace(/\s+/g, ' ').trim())
    .filter(Boolean)
    .slice(0, 5);
  const ratingText = getText('#acrPopover .a-icon-alt') || getText('span[data-hook="rating-out-of-text"]');
  let rating = null;
  if (ratingText) {
    const m = ratingText.replace(',', '.').match(/[\d.]+/);
    rating = m ? parseFloat(m[0]) : null;
  }
  const reviewsText = getText('#acrCustomerReviewText') || getText('span[data-hook="total-review-count"]');
  const reviews_count = reviewsText ? parseInt(reviewsText.replace(/[^\d]/g, ''), 10) : null;
  let main_image_url = '';
  const imgEl = document.querySelector('#landingImage');
  if (imgEl) {
    main_image_url = imgEl.currentSrc || imgEl.src || '';
    if (!main_image_url) {
      try {
        const dyn = imgEl.getAttribute('data-a-dynamic-image');
        if (dyn) main_image_url = Object.keys(JSON.parse(dyn))[0] || '';
      } catch {}
    }
  }
  let best_sellers_rank = null;
  {
    const details = document.querySelector('#productDetails_detailBullets_sections1')
      || document.querySelector('#detailBulletsWrapper_feature_div')
      || document.querySelector('#prodDetails');
    if (details) {
      const txt = details.textContent;
      const ranks = [];
      const re = /#([\d,]+)\s+in\s+([^\(\n]+)(?:\s*\([^)]+\))?/g;
      let m;
      while ((m = re.exec(txt)) !== null) {
        const rankNum = parseInt(m[1].replace(/,/g, ''), 10);
        if (!Number.isNaN(rankNum)) ranks.push({ rank: rankNum, category: m[2].trim() });
      }
      if (ranks.length) best_sellers_rank = ranks;
    }
  }
  const is_prime = !!document.querySelector('.a-icon-prime, [aria-label*="Prime"], .prime-logo');
  return { title, bullet_points, rating, reviews_count, main_image_url, best_sellers_rank, price, list_price, discount_percent, is_prime };
}
"""
        return await page.evaluate(script)

    @staticmethod
    def refine_from_aod(html, current):
        """Дополняет данные карточки офферами из блока AOD (Another Offer Display)."""
        soup = BeautifulSoup(html, "lxml")
        pinned = soup.select_one("#aod-pinned-offer") or soup.select_one(".aod-offer")
        if not pinned:
            return current
        aod_price = None
        price_node = (pinned.select_one(".a-price:not(.a-text-price) .a-offscreen")
                      or pinned.select_one(".a-price .a-offscreen"))
        if price_node:
            aod_price = PagesParser.to_float_money(price_node.get_text(" ", strip=True))
        aod_list = None
        strike_node = pinned.select_one(".a-price.a-text-price .a-offscreen")
        if strike_node:
            aod_list = PagesParser.to_float_money(strike_node.get_text(" ", strip=True))
        aod_prime = bool(
            pinned.select_one(".a-icon-prime, [aria-label*='Prime'], .prime-logo")
            or soup.select_one(".a-icon-prime, [aria-label*='Prime'], .prime-logo")
        )
        price = current.get("price") or aod_price
        list_price = current.get("list_price") or aod_list
        discount_percent = current.get("discount_percent")
        if price is not None and list_price is not None and list_price > price and discount_percent is None:
            discount_percent = round((list_price - price) / list_price * 100)
        current.update(
            {"price": price, "list_price": list_price, "discount_percent": discount_percent,
             "is_prime": bool(current.get("is_prime") or aod_prime)}
        )
        return current

    @staticmethod
    async def fetch_aod_html(context, page, aod_url, referer_url):
        """Запрашивает HTML блока AOD (список предложений) с учётом CSRF и антибот-защит."""
        anti = None
        try:
            anti = await page.get_attribute("#anti-csrftoken-a2z", "value")
        except:
            anti = None

        async def _attempt():
            headers = {"Referer": referer_url, "X-Requested-With": "XMLHttpRequest",
                       "Accept-Language": "en-US,en;q=0.9"}
            if anti:
                headers["anti-csrftoken-a2z"] = anti
            url = aod_url
            sep = "&" if "?" in url else "?"
            url += f"{sep}cb={int(time.time() * 1000)}&t={random.randint(1000, 9999)}"
            resp = await context.request.get(url, headers=headers)
            if not resp.ok:
                raise PWError(f"AOD HTTP {resp.status}")
            txt = await resp.text()
            if "automated access" in txt.lower() or "captcha" in txt.lower():
                raise PWError("AOD anti-bot page")
            return txt

        try:
            aod_html = await ScrapeHelpers.retry_async(_attempt, retries=2, base=0.8)
        except Exception:
            aod_html = None

        if not aod_html:
            try:
                aod_html = await page.evaluate(
                    """async (u) => { const r = await fetch(u, { credentials: 'include' }); return await r.text(); }""",
                    aod_url
                )
            except:
                aod_html = None

        return aod_html

    @classmethod
    async def scrape(cls, url: str):
        """Основной метод: открывает страницу товара, извлекает DOM, запрашивает AOD, объединяет и возвращает данные."""
        asin = cls.asin_from_url(url)
        if not asin:
            raise ValueError("Не удалось определить ASIN из URL (ожидается .../dp/ASIN).")
        domain = (urlparse(url).netloc) or "www.amazon.com"
        aod_url = f"https://{domain}/gp/aod/ajax/?{urlencode({'asin': asin, 'pc': 'dp'})}"
        proxy = os.getenv("PROXY")
        attempt = 1
        while attempt < 4:
            async with async_playwright() as pw:
                browser, context = await ScrapeHelpers.new_browser_and_context(
                    pw,
                    headless=True,
                    proxy=proxy,
                    user_agent=cls.USER_AGENT,
                    stealth_script=cls.STEALTH_INIT,
                )
                blocker = ScrapeHelpers.make_generic_blocker("/gp/aod/ajax")
                await context.route("**/*", lambda r: r.abort() if blocker(r.request) else r.continue_())

                page = await context.new_page()
                page.set_default_timeout(20000)

                async def goto_factory():
                    await asyncio.sleep(ScrapeHelpers.jitter())
                    return await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                try:
                    await ScrapeHelpers.retry_async(goto_factory, retries=2, base=0.9)
                    await asyncio.sleep(ScrapeHelpers.jitter(3, 6))
                    await page.reload(wait_until="domcontentloaded")
                    await asyncio.sleep(ScrapeHelpers.jitter(2, 4))
                except Exception as e:
                    await context.close()
                    await browser.close()
                    raise RuntimeError(f"Не удалось открыть страницу: {e}")

                await ScrapeHelpers.accept_cookies_if_any(page)

                if await page.query_selector("#captchacharacters, form[action*='validator'], form[action*='approach']"):
                    await context.close()
                    await browser.close()
                    raise RuntimeError("CAPTCHA: страница потребовала валидацию. Смените прокси/профиль/темп.")

                await ScrapeHelpers.human_scroll(page, steps=5)

                await asyncio.sleep(ScrapeHelpers.jitter(0.3, 0.9))
                try:
                    await page.wait_for_selector("#productTitle", timeout=5000)
                except:
                    pass

                dom_task = asyncio.create_task(cls.extract_from_dom(page))
                aod_task = asyncio.create_task(cls.fetch_aod_html(context, page, aod_url, url))
                dom_data, aod_html = await asyncio.gather(dom_task, aod_task)
                if aod_html:
                    dom_data = cls.refine_from_aod(aod_html, dom_data)

                await context.close()
                await browser.close()
            attempt += 1
            required_fields = ["title", "price", "rating", "reviews_count"]
            if all(dom_data.get(field) not in (None, "") for field in required_fields):
                break
        bsr = dom_data.get("best_sellers_rank") or []
        rank_value = bsr[0].get("rank") if isinstance(bsr, list) and bsr else None
        return {
            "asin": asin,
            "title": dom_data.get("title"),
            "rank": rank_value,
            "price": dom_data.get("price"),
            "list_price": dom_data.get("list_price"),
            "discount_percent": dom_data.get("discount_percent"),
            "rating": dom_data.get("rating"),
            "reviews_count": dom_data.get("reviews_count"),
            "is_prime": dom_data.get("is_prime"),
            "best_sellers_rank": dom_data.get("best_sellers_rank"),
            "bullet_points": dom_data.get("bullet_points"),
            "main_image_url": dom_data.get("main_image_url"),
            "dp_url": url,
        }

    @classmethod
    def _worker_scrape(cls, url: str):
        """Обёртка для scrape() внутри потока, возвращает результат или ошибку."""
        try:
            return {"url": url, "result": asyncio.run(cls.scrape(url))}
        except Exception as e:
            return {"url": url, "error": str(e)}

    @classmethod
    def run(cls, urls, max_workers: int = 5):
        """Запускает scrape() параллельно для списка URL через ThreadPoolExecutor."""
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(cls._worker_scrape, u) for u in urls]
            for fut in as_completed(futures):
                results.append(fut.result())
        return results

    @staticmethod
    def save_json(data, outfile: str | None = None) -> str:
        """Сохраняет данные в JSON файл (по указанному пути или в results/)."""
        if outfile:
            os.makedirs(os.path.dirname(outfile), exist_ok=True)
            path = outfile
        else:
            os.makedirs(JSON_FOLDER_NAME, exist_ok=True)
            path = os.path.join(JSON_FOLDER_NAME, f"results_{int(time.time())}.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path


app = FastAPI()


@app.get("/get_data")
async def get_data():
    """
    GET /get_data?limit=5&save=false
    1) Получает список ASIN со страницы бестселлеров
    2) Берёт первые `limit` штук
    3) Параллельно парсит карточки /dp/<ASIN>
    4) (опционально) сохраняет результат в файл
    """

    def run_one(url: str):
        sleep(random.randint(1, 10))
        return asyncio.run(MainPage(url=url).run())

    with open('category_link.json', 'r', encoding="utf-8") as f:
        urls = json.load(f)

    def run_all(urls_map: dict[str, str], max_workers: int = 1) -> dict[str, list] | dict[str, dict]:
        results: dict[str, list] = {}
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_key = {pool.submit(run_one, url): key for key, url in urls_map.items()}
            for fut in as_completed(future_to_key):
                key = future_to_key[fut]
                try:
                    asin_list = fut.result()
                    results[key] = asin_list
                except Exception as e:
                    results[key] = {"error": str(e)}
        return results

    category_elements = run_all(urls, max_workers=5)
    if not category_elements:
        raise HTTPException(status_code=424, detail="Список ASIN не обнаружен")
    data = {}
    current_category = 1
    for category in category_elements:
        print(f'Обработка категории {current_category}/{len(category_elements)}')
        current_category += 1
        try:
            if len(category_elements[category]) != 0:
                urls = [f"https://www.amazon.com/dp/{asin}" for asin in category_elements[category][:10]]
                results = PagesParser.run(urls, max_workers=5)
                data[category] = results
        except Exception as e:
            print(f"Ошибка при парсинге элементов: {e}")

    for category, asin_order in category_elements.items():
        if category in data:
            order_index = {asin: i for i, asin in enumerate(asin_order)}
            data[category].sort(
                key=lambda item: order_index.get(item["result"]["asin"], float("inf"))
            )

    PagesParser.save_json(data)
    payload = {"items": data}
    return JSONResponse(content=payload)


def scheduled_task():
    loop = asyncio.get_event_loop()
    loop.create_task(get_data())


@app.on_event("startup")
async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_task, "interval", hours=24)
    scheduler.start()
    print("Планировщик запущен")


if __name__ == "__main__":
    asyncio.run(get_data())
