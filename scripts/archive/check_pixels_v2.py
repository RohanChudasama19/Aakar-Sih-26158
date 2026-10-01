
import asyncio
from playwright.async_api import async_playwright
import numpy as np
from PIL import Image

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        await page.goto("http://127.0.0.1:8000/workspace/mars_hkairport01_quality")
        await page.wait_for_timeout(8000)
        
        # Take base screenshot
        await page.screenshot(path="demo/mars_heatmaps/base.png")
        
        # Click Point Density
        await page.locator("button", has_text="Point Density").click(timeout=5000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path="demo/mars_heatmaps/point_density.png")
            
        await browser.close()
        
        # Compare
        img1 = np.array(Image.open("demo/mars_heatmaps/base.png"))
        img2 = np.array(Image.open("demo/mars_heatmaps/point_density.png"))
        
        diff = np.sum(img1 != img2)
        total = img1.size
        print(f"Diff: {diff} / {total} pixels ({diff/total*100:.2f}%)")

asyncio.run(run())

