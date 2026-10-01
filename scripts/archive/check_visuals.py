import asyncio
from playwright.async_api import async_playwright
import sys

async def run(url, name):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(url, wait_until='networkidle')
        await page.wait_for_timeout(3000)

        data = await page.evaluate('''() => {
            const canvas = document.querySelector('canvas');
            if (!canvas) return { error: "No canvas found" };
            
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
            if (!gl) return { error: "No WebGL context" };

            const pixels = new Uint8Array(canvas.width * canvas.height * 4);
            gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
            
            let nonBg = 0;
            for (let i = 0; i < pixels.length; i += 4) {
                if (Math.abs(pixels[i] - 18) > 5 || 
                    Math.abs(pixels[i+1] - 27) > 5 || 
                    Math.abs(pixels[i+2] - 23) > 5) {
                    nonBg++;
                }
            }
            return { w: canvas.width, h: canvas.height, nonBg: nonBg, total: canvas.width * canvas.height };
        }''')
        
        print(f"{name} Canvas stats: {data}")
        await browser.close()

async def main():
    await run('http://127.0.0.1:8000/workspace/mars_hkairport01_quality', 'MARS')
    await run('http://127.0.0.1:8000/workspace/95f51b12-b771-47bf-9201-c3700f9475a7', 'Colorado')

asyncio.run(main())
