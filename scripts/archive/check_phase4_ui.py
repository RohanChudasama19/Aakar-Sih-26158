import asyncio
import subprocess
from playwright.async_api import async_playwright
import time

async def test_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Testing MARS viewer modes...")
        await page.goto("http://127.0.0.1:8002/workspace/mars_hkairport01_quality", wait_until='networkidle')
        await page.wait_for_timeout(4000)
        
        # Check Orbit
        await page.click("button[title='Orbit']")
        await page.wait_for_timeout(500)
        
        # Check Fly
        await page.click("button[title='Fly']")
        await page.wait_for_timeout(500)
        
        # Press forward
        await page.mouse.down()
        await page.mouse.up()
        await page.keyboard.down("w")
        await page.wait_for_timeout(500)
        await page.keyboard.up("w")
        
        # Walk Mode
        await page.click("button[title='Walk']")
        await page.wait_for_timeout(500)
        
        # Focus mode
        await page.click("button[title='Focus']")
        await page.wait_for_timeout(500)
        
        # Reset View
        await page.click("button[title='Reset / Fit Model']")
        await page.wait_for_timeout(500)
        
        print("Done UI tests.")
        await browser.close()

if __name__ == '__main__':
    proc = subprocess.Popen([".\\.venv\\Scripts\\python.exe", "-m", "uvicorn", "app.main:app", "--port", "8002"])
    time.sleep(5)
    try:
        asyncio.run(test_ui())
    finally:
        proc.terminate()
