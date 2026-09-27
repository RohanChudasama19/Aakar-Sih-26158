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

        # 1. Test Project Creation
        await page.goto("http://127.0.0.1:8001/projects", wait_until='networkidle')
        await page.wait_for_timeout(2000)
        
        # Click new project
        await page.click("text=New Project")
        await page.fill("input[placeholder='e.g. Hong Kong Operations']", "Playwright Test Proj")
        await page.fill("input[placeholder='e.g. HKG']", "Local")
        await page.click("button:has-text('Create')")
        
        await page.wait_for_timeout(3000)
        
        # Check text exists
        content = await page.content()
        if "Playwright Test Proj" in content:
            print("Project Create Success")
        else:
            print("Project Create Failed")
        
        # 2. Test MARS Visuals
        await page.goto("http://127.0.0.1:8001/workspace/mars_hkairport01_quality", wait_until='networkidle')
        await page.wait_for_timeout(4000)
        
        data = await page.evaluate('''() => {
            const canvas = document.querySelector('canvas');
            if (!canvas) return { error: "No canvas found" };
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
            if (!gl) return { error: "No WebGL context" };
            const pixels = new Uint8Array(canvas.width * canvas.height * 4);
            gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
            let nonBg = 0;
            for (let i = 0; i < pixels.length; i += 4) {
                if (Math.abs(pixels[i] - 18) > 5 || Math.abs(pixels[i+1] - 27) > 5 || Math.abs(pixels[i+2] - 23) > 5) {
                    nonBg++;
                }
            }
            return { w: canvas.width, h: canvas.height, nonBg: nonBg };
        }''')
        print(f"MARS Canvas stats: {data}")
        
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
