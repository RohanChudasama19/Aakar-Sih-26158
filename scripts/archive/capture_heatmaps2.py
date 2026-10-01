
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        page.on("console", lambda msg: print(f"Browser: {msg.type}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PageError: {err.message}"))
        
        print("Navigating to MARS mission...")
        await page.goto("http://127.0.0.1:8000/#/mission/mars_hkairport01_quality")
        await page.wait_for_timeout(5000)
        
        print(await page.content())
        
        await browser.close()

asyncio.run(run())

