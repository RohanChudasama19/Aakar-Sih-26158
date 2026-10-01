import asyncio
from playwright.async_api import async_playwright
import base64

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto('http://127.0.0.1:8000/workspace/mars_hkairport01_quality', wait_until='networkidle')
        await page.wait_for_timeout(3000)

        # Get canvas pixel data to see if it's drawing anything other than background
        data = await page.evaluate('''() => {
            const canvas = document.querySelector('canvas');
            if (!canvas) return { error: "No canvas found" };
            
            const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
            if (!gl) return { error: "No WebGL context" };

            const pixels = new Uint8Array(canvas.width * canvas.height * 4);
            gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
            
            let nonBg = 0;
            // bg is '#121b17' -> 18, 27, 23
            for (let i = 0; i < pixels.length; i += 4) {
                if (Math.abs(pixels[i] - 18) > 5 || 
                    Math.abs(pixels[i+1] - 27) > 5 || 
                    Math.abs(pixels[i+2] - 23) > 5) {
                    nonBg++;
                }
            }
            return { w: canvas.width, h: canvas.height, nonBg: nonBg, total: canvas.width * canvas.height };
        }''')
        
        print(f"Canvas stats: {data}")
        await browser.close()

asyncio.run(run())

from PIL import Image
import numpy as np

def diff(f1, f2):
    img1 = np.array(Image.open(f1).convert("RGB"))
    img2 = np.array(Image.open(f2).convert("RGB"))
    diff_pixels = np.sum(img1 != img2)
    total_pixels = img1.size
    print(f"Diff {f1} vs {f2}: {diff_pixels} pixels ({(diff_pixels/total_pixels)*100:.2f}%)")

diff("demo/mars_heatmaps/screenshot_original_texture.png", "demo/mars_heatmaps/screenshot_point_density.png")
diff("demo/mars_heatmaps/screenshot_original_texture.png", "demo/mars_heatmaps/screenshot_surface_support.png")

