import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        net_errors = []
        page.on('response', lambda r: net_errors.append((r.status, r.url, r.headers.get('content-type', ''))) if r.status >= 400 or 'text/html' in r.headers.get('content-type', '') else None)

        await page.goto('http://127.0.0.1:8000/workspace/mars_hkairport01_quality', wait_until='networkidle')
        await page.wait_for_timeout(3000)

        await page.screenshot(path='mars_demo_viewer.png')
        print("Screenshot saved to mars_demo_viewer.png")

        print("Network anomalies (4xx/5xx or unexpected HTML):")
        for status, url, ctype in net_errors:
            if url != 'http://127.0.0.1:8000/workspace/mars_hkairport01_quality':
                print(f"  {status}: {url} ({ctype})")

        await browser.close()

asyncio.run(run())
