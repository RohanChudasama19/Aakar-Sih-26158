import asyncio
import subprocess
from playwright.async_api import async_playwright
import time

async def test_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Testing settings page...")
        await page.goto("http://127.0.0.1:8002/settings", wait_until='networkidle')
        await page.wait_for_timeout(2000)
        await page.click("text=Reconstruction Engine")
        await page.wait_for_timeout(1000)
        
        print("Testing quality page...")
        await page.goto("http://127.0.0.1:8002/quality/mars_hkairport01_quality", wait_until='networkidle')
        await page.wait_for_timeout(2000)
        content = await page.content()
        if "FRAGMENTED_SURFACE" not in content:
            print("WARNING: Quality report did not load MARS metrics properly.")
        
        print("Testing exports page...")
        await page.goto("http://127.0.0.1:8002/exports/mars_hkairport01_quality", wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        # Download the mesh 
        print("Done UI tests.")
        await browser.close()

if __name__ == '__main__':
    proc = subprocess.Popen([".\\.venv\\Scripts\\python.exe", "-m", "uvicorn", "app.main:app", "--port", "8002"])
    time.sleep(5)
    try:
        asyncio.run(test_ui())
    finally:
        proc.terminate()
