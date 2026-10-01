import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        reqs = []
        page.on('request', lambda r: reqs.append(r.url))
        
        await page.goto('http://127.0.0.1:8000/workspace/mars_hkairport01_quality', wait_until='networkidle')
        await page.wait_for_timeout(4000)

        print("Requests made:")
        for url in reqs:
            if '/api/' in url:
                print(f"  {url}")

        await browser.close()

asyncio.run(run())
