# Парсер Амазон
### Цей файл містить 2 виконувані файли:
## 1. `main.py` - вітрина та видача JSON для зібраних товарів (FastAPI)


#### Цей сервіс:
- Рендерить головну сторінку зі списком товарів 
- Віддає останній JSON-файл зі збором 
- Читає дані з папки `json_results/` (значення береться з `amazon_dp_extract.JSON_FOLDER_NAME`) 
- Надає зручні ендпоінти для UI та завантаження


### Що робить:

- Знаходить останній файл формату `results_<UNIX_TS>.json` у `json_results/` 

- Рендерит сторінку / з товарами та міткою часу останнього оновлення 

- Файл на скачування `/download_json.` 

- Повертає товари конкретної категорії `/get_category/{category_name}`


### Залежності та оточення:

- Python 3.11+ 

- FastAPI, Starlette (Jinja2Templates, StaticFiles) 

- Стандартна бібліотека: zoneinfo, pathlib, re, json, datetime 

- Модуль проекту: amazon_dp_extract (константа JSON_FOLDER_NAME → зазвичай "json_results") 

### Структура директорій:

- `templates/` - повинен містити `main.html`
- `static/` - ваші стилі/скрипти/зображення
- `json_results/` - сюди складаються результати парсингу: `results_<timestamp>.json`

### Формат вхідного JSON

Очікується словник категорій, де значення – список елементів (зазвичай результат парсингу з вашого скрапера):

```json
"Amazon Devices & Accessories": [
  {
    "url": "https://www.amazon.com/dp/B08JHCVHTY",
    "result": {
      "asin": "B08JHCVHTY",
      "title": "",
      "rank": null,
      "price": null,
      "list_price": null,
      "discount_percent": null,
      "rating": null,
      "reviews_count": null,
      "is_prime": true,
      "best_sellers_rank": null,
      "bullet_points": [],
      "main_image_url": "",
      "dp_url": "https://www.amazon.com/dp/B08JHCVHTY"
    }
  }, ...
],
"Arts, Crafts & Sewing": [...]
```
### Ендпоінти
#### 1. /GET 
- Рендерить `templates/main.html`
- Контекст:
  - `products` – дані з останнього JSON (як вище)
  * `dt` – дата/час останнього файлу (з імені results_<ts>.json, таймзона Europe/Kyiv)
* Якщо жодного файлу немає – products буде `[]`, а `dt` – дефолтний рядок

#### 2. /GET download_json

- Повертає останній JSON-файл як вкладення для скачування
- Помилки:
  - 404 — якщо файл не знайдено

#### 3. /GET get_category/{category_name}
- Повертає масив товарів для цієї категорії: `{ "products": [ ... ] }`


### Помилки

- Якщо категорії немає даних, FastAPI викине KeyError → варто обробити на фронті

- Логіка вибору "останнього" файлу

- Шукається відповідність `results_<число>.json;` береться файл із максимальним числом

- Якщо таких немає - береться найсвіжіший по mtime будь-який `*.json`

- Якщо папка порожня/не існує, повертається `[]`

### Швидкий старт 

1.  Переконайтеся, що у вас є `templates/main.html`, `static/`, і `json_results/` лежить хоча б один `results_<ts>.json`

2. Запустіть програму:`uvicorn your_module_name:app --host 0.0.0.0 --port 8000` , де `your_module_name` - ім'я файлу без `.py`

3. Відкрийте:
- Сторінка: http://localhost:8000/ 

- Скачування: http://localhost:8000/download_json

- Категорія: http://localhost:8000/get_category/Books

---

## 2. `amazon_dp_extract.py` - FastAPI + Playwright Amazon Scraper

#### Міні-сервіс на FastAPI для збирання карток товарів Amazon:

- Бере зі сторінок категорій список ASIN із фонового XHR componentbuilder

- Парсить кожну картку `/dp/<ASIN>` (DOM + AOD/"Other sellers")

- Повертає JSON і зберігає результат у файл

- За розкладом оновлює дані раз на 24 години (APScheduler)

### Можливості

- Отримання ASIN зі сторінки бестселерів/категорії (перехоплення XHR componentbuilder)

- Скрейп карток: ціна, стара ціна, знижка, рейтинг, кількість відгуків, BSR, буллети, картинка, Prime

- Доповнення даними з AOD (Ajax Other Deals)

- Антибот-поведінка: рандомні паузи, скролл, урізання сітки, stealth-ініціалізація

- Паралельна обробка (ThreadPoolExecutor)

- Автозбереження в `json_results/results_<timestamp>.json`

- Планувальник: автозапуск завдання раз на 24 години на старті програми

### Стек

- Python 3.11+

- FastAPI, Starlette

- Playwright (Chromium)

- BeautifulSoup4

- APScheduler

### Встановлення
#### 1. Клонуємо репозиторій та створюємо оточення
```cmd
python -m venv .venv
. .venv/bin/activate 
```
Windows: 
```cmd
.venv\Scripts\activate
```
#### 2. Встановлюємо залежності
```cmd
pip install -U pip wheel
pip install fastapi uvicorn[standard] playwright beautifulsoup4 apscheduler
```
#### 3. Ставимо браузери Playwright
```cmd
python -m playwright install chromium
```
  Linux:
```cmd
python -m playwright install-deps
```


### Конфігурація

- **Змінні оточення (опціонально):**

  - PROXY – проксі для Playwright (наприклад, http://user:pass@host:port)

  - USER_AGENT - якщо заданий, перевизначить випадковий User-Agent

- **Файл вхідних посилань:** `category_link.json` (обов'язковий). Приклад `category_link.json`:

  - ``` json 
    {
    "Amazon Devices & Accessories": "https://www.amazon.com/Best-Sellers-Amazon-Devices-Accessories/zgbs/amazon-devices/ref=zg_bs_nav_amazon-devices_0",
    "Amazon Renewed": "https://www.amazon.com/Best-Sellers-Amazon-Renewed/zgbs/amazon-renewed/ref=zg_bs_nav_amazon-renewed_0",
    }
    ```

  - Ключ - ім'я категорії (довільно), значення - URL сторінки категорії/бестселерів, де є XHR componentbuilder.

### Як запустити
1. **Варіант A:** як API-сервіс (рекомендовано)
```
uvicorn amazon_dp_extract:app --host 0.0.0.0 --port 8000
```

Тепер можна смикнути endpoint:
```
GET http://localhost:8000/get_data
```
2. **Варіант В:** одноразовий запуск збору
```
python amazon_dp_extract.py
```

Скрипт запустить збір і збереже результат у `json_results/results_<timestamp>.json`.

### Маршрут API
#### 1. /GET get_data

*Тригерить повний пайплайн:*

- читає category_link.json

- за кожною категорією отримує список ASIN

- для перших 10 ASIN парсить картки (паралельно)

- сортує результати за початковим порядком ASIN

- зберігає в `json_results/…`

- Повертає JSON із даними по всіх категоріях.

*Приклад відповіді (скорочено):*
```json
"Amazon Devices & Accessories": [
    {
      "url": "https://www.amazon.com/dp/B08JHCVHTY",
      "result": {
        "asin": "B08JHCVHTY",
        "title": "",
        "rank": null,
        "price": null,
        "list_price": null,
        "discount_percent": null,
        "rating": null,
        "reviews_count": null,
        "is_prime": true,
        "best_sellers_rank": null,
        "bullet_points": [],
        "main_image_url": "",
        "dp_url": "https://www.amazon.com/dp/B08JHCVHTY"
      }
    },...],
"Arts, Crafts & Sewing": [...
```
*Як це працює (коротко за модулями):*

1. **MainPage**

- Відкриває сторінку категорії

- Перехоплює XHR/Fetch componentbuilder і дістає asinList з POST-тіла

2. **PagesParser**

- Парсить картку /dp/<ASIN>: DOM-скриптом забирає ціну/рейтинг/BSR/і т.д.

- Доповнює даними з AOD (через Ajax)

- Повертає словник із полями товару

3. `/get_data`

- Завантажує `category_link.json`

- Для кожної категорії бере перші 10 ASIN

- Паралельно збирає картки та сортує згідно з вихідним порядком

- Зберігає загальний результат у `json_results/results_<timestamp>.json`

### Повторний збір за розкладом

При старті програми включається APScheduler, котрий кожні 24 години запускає `get_data()`:
```
scheduler.add_job(scheduled_task, "interval", hours=24)
```

---

### Приклад зовнішнього вигляду сайту:
![img_1.png](img_1.png)