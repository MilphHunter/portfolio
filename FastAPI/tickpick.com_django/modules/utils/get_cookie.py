import asyncio

from playwright.async_api import async_playwright

proxy = {
        "server": "http://superproxy.zenrows.com:1337",
        "username": "xbJQ6dFTrdC2",
        "password": "xbJQ6dFTrdC2_country-us_ttl-30s_session-Z51KoZekPLPq"
    }

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(
            #proxy=proxy
        )

        page = await context.new_page()
        await page.goto('https: //google.com')

        await asyncio.sleep(300)

        await page.close()


if __name__ == '__main__':
    asyncio.run(main())