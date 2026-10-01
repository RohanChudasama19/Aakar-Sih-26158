import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto('http://127.0.0.1:8000/workspace/mars_hkairport01_quality', wait_until='networkidle')
        await page.wait_for_timeout(3000)

        size = await page.evaluate('''() => {
            const canvas = document.querySelector('canvas');
            return canvas ? {w: canvas.width, h: canvas.height, cw: canvas.clientWidth, ch: canvas.clientHeight} : null;
        }''')
        print("Canvas size:", size)

        await browser.close()

asyncio.run(run())
