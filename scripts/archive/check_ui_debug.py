import asyncio
import multiprocessing
import uvicorn
from playwright.async_api import async_playwright
import time
import requests

def run_server():
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="warning")

async def test_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:8001/projects", wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        await page.click("text=New Project")
        await page.fill("input[placeholder='e.g. Hong Kong Operations']", "Playwright Test Proj 2")
        await page.fill("input[placeholder='e.g. HKG']", "Local")
        await page.click("button:has-text('Create')")
        
        await page.wait_for_timeout(3000)
        await page.screenshot(path="debug_projects.png")
        await browser.close()

if __name__ == '__main__':
    server = multiprocessing.Process(target=run_server)
    server.start()
    time.sleep(5) # wait for server
    try:
        asyncio.run(test_ui())
    finally:
        server.terminate()
        server.join()
