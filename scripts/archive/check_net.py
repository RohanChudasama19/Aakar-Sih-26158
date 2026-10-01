import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        net_errors = []
        page.on('response', lambda r: net_errors.append((r.status, r.url)) if r.status >= 400 else None)

        await page.goto('http://127.0.0.1:8000/workspace/mars_hkairport01_quality', wait_until='networkidle')
        await page.wait_for_timeout(3000)

        print("Network errors from workspace load (MARS):")
        if not net_errors: print("  NONE")
        for status, url in net_errors:
            print(f"  {status}: {url}")

        await browser.close()

asyncio.run(run())
