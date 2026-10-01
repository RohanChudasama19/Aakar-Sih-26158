
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        page.on("pageerror", lambda err: print(f"Page Error: {err}"))
        page.on("console", lambda msg: print(f"Browser: {msg.text}"))
        
        await page.goto("http://127.0.0.1:8000/workspace/mars_hkairport01_quality")
        await page.wait_for_timeout(8000)
        
        await page.screenshot(path="demo/mars_heatmaps/screenshot_debug_ui.png")
            
        await browser.close()

asyncio.run(run())

