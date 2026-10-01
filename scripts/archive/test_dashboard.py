import asyncio
from playwright.async_api import async_playwright

async def test_dashboard():
    import subprocess
    proc = subprocess.Popen([".\\.venv\\Scripts\\python.exe", "-m", "uvicorn", "app.main:app", "--port", "8005"])
    import time
    time.sleep(4)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto("http://127.0.0.1:8005", wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Assuming dashboard has some text "flight 38" or the count "63" or similar
            content = await page.content()
            if "mars_hkairport01_quality" in content or "MARS" in content:
                print("MARS is found in Dashboard/Viewer")
            else:
                print("Check if MARS loaded correctly.")

            await page.goto("http://127.0.0.1:8005/projects", wait_until='networkidle')
            await page.wait_for_timeout(2000)
            print("Dashboard and Projects checked.")
            
            await browser.close()
    finally:
        proc.terminate()

if __name__ == '__main__':
    asyncio.run(test_dashboard())
