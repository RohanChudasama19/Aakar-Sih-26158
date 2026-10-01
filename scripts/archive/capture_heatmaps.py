import asyncio
from playwright.async_api import async_playwright
import os

async def run():
    os.makedirs("demo/mars_heatmaps", exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        print("Navigating to MARS mission...")
        await page.goto("http://127.0.0.1:8000/workspace/mars_hkairport01_quality")
        await page.wait_for_timeout(8000) # Wait for initial load
        
        print("Capturing Original Texture...")
        await page.screenshot(path="demo/mars_heatmaps/screenshot_original_texture.png")
        
        # Click Point Density
        print("Clicking Point Density...")
        try:
            await page.get_by_text("Point Density").first.click(timeout=5000)
            await page.wait_for_timeout(8000) # Wait for binary load
            await page.screenshot(path="demo/mars_heatmaps/screenshot_point_density.png")
        except Exception as e:
            print("Failed to click Point Density", e)
            
        # Click Surface Support
        print("Clicking Surface Support...")
        try:
            await page.get_by_text("Surface Support").first.click(timeout=5000)
            await page.wait_for_timeout(8000)
            await page.screenshot(path="demo/mars_heatmaps/screenshot_surface_support.png")
        except Exception as e:
            print("Failed to click Surface Support", e)

        # Click Potential Camera Visibility
        print("Clicking Potential Camera Visibility...")
        try:
            await page.get_by_text("Potential Camera Visibility").first.click(timeout=5000)
            await page.wait_for_timeout(8000)
            await page.screenshot(path="demo/mars_heatmaps/screenshot_potential_camera_visibility.png")
        except Exception as e:
            print("Failed to click Potential Camera Visibility", e)

        # Opacity test
        print("Testing opacity...")
        try:
            await page.evaluate("document.querySelector('input[type=range]').value = 0.5")
            await page.evaluate("document.querySelector('input[type=range]').dispatchEvent(new Event('change'))")
            await page.wait_for_timeout(2000)
            await page.screenshot(path="demo/mars_heatmaps/screenshot_opacity_50.png")
            
            await page.evaluate("document.querySelector('input[type=range]').value = 0.0")
            await page.evaluate("document.querySelector('input[type=range]').dispatchEvent(new Event('change'))")
            await page.wait_for_timeout(2000)
            await page.screenshot(path="demo/mars_heatmaps/screenshot_opacity_0.png")
            
            await page.evaluate("document.querySelector('input[type=range]').value = 1.0")
            await page.evaluate("document.querySelector('input[type=range]').dispatchEvent(new Event('change'))")
            await page.wait_for_timeout(2000)
            await page.screenshot(path="demo/mars_heatmaps/screenshot_opacity_100.png")
        except Exception as e:
            print("Failed opacity test", e)

        # Collapse Panel
        print("Collapsing panel...")
        try:
            await page.get_by_text("<").first.click(timeout=2000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path="demo/mars_heatmaps/screenshot_panel_collapsed.png")
            
            await page.get_by_text(">").first.click(timeout=2000)
            await page.wait_for_timeout(2000)
            await page.screenshot(path="demo/mars_heatmaps/screenshot_panel_expanded.png")
        except Exception as e:
            print("Failed collapse test", e)
            
        await browser.close()

asyncio.run(run())
