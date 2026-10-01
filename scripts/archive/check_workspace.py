import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width':1920,'height':1080})

        net_errors = []
        page.on('response', lambda r: net_errors.append((r.status, r.url)) if r.status >= 400 else None)

        await page.goto('http://127.0.0.1:8000/workspace/mars_hkairport01_quality', wait_until='networkidle')
        await page.wait_for_timeout(3000)

        print("Network errors from workspace load:")
        for status, url in net_errors[:20]:
            print(f"  {status}: {url}")

        # Get the actual text on screen
        text = await page.inner_text('body')
        print()
        print("Visible text (first 800 chars):")
        print(text[:800])

        await browser.close()

asyncio.run(run())
