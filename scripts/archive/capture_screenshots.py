import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        # 1. Load the Dashboard
        print("Navigating to frontend...")
        await page.goto("http://127.0.0.1:8000/")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="demo/mars_hkairport01_quality/screenshot_dashboard.png")
        print("Captured dashboard screenshot.")
        
        # Check if the text "MARS HKairport01" is present in the DOM
        content = await page.content()
        if "MARS HKairport01" in content:
            print("Found MARS mission on Dashboard.")
        else:
            print("Warning: MARS mission not seen on dashboard immediately. Still proceeding.")
            
        # Instead of clicking UI which might be flaky, we can just navigate directly
        # to the viewer route if we know it. We'll try to find the link first.
        # Usually React routes are like /#/mission/mars_hkairport01_quality or /mission/...
        print("Trying to click MARS mission...")
        try:
            # We look for an element containing the text
            await page.get_by_text("MARS HKairport01").first.click(timeout=5000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print("Click failed, navigating directly to mission hash...")
            await page.goto("http://127.0.0.1:8000/#/mission/mars_hkairport01_quality")
            await page.wait_for_timeout(3000)
            
        await page.screenshot(path="demo/mars_hkairport01_quality/screenshot_viewer.png")
        print("Captured viewer screenshot.")
        
        # Try to click the "Textured" or "GLB" mode if such a button exists
        try:
            # Depending on the friend's design, it might be called "Textured", "GLB", "3D Model", etc.
            await page.get_by_text("Textured", exact=False).first.click(timeout=2000)
            print("Clicked Textured mode.")
            await page.wait_for_timeout(5000)
            await page.screenshot(path="demo/mars_hkairport01_quality/screenshot_textured.png")
        except:
            print("Could not find 'Textured' button, it might already be loaded or called something else.")
            
        await browser.close()

asyncio.run(run())
