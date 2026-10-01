
import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        page.on("console", lambda msg: print(f"Browser: {msg.text}"))
        
        await page.goto("http://127.0.0.1:8000/workspace/mars_hkairport01_quality")
        await page.wait_for_timeout(8000)
        
        # Click Point Density
        try:
            await page.get_by_text("Point Density").first.click(timeout=5000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print("Failed to click Point Density", e)

        script = """
        () => {
            if (!window.__viewer_debug_obj) return "No debug obj";
            let o = window.__viewer_debug_obj;
            return {
                name: o.name,
                isIndexed: o.geometry.index !== null,
                indexCount: o.geometry.index ? o.geometry.index.count : 0,
                vertexCount: o.geometry.attributes.position.count
            };
        }
        """
        res = await page.evaluate(script)
        print("Geometry info:", res)
            
        await browser.close()

asyncio.run(run())

