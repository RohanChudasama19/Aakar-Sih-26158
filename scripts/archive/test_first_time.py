import asyncio
from playwright.async_api import async_playwright
import sqlite3
import os

async def test_first_time():
    # backup and clear db
    if os.path.exists('app/aerorecon.db'):
        os.rename('app/aerorecon.db', 'app/aerorecon.db.tmp')
    
    # restart server here or just rely on API? The server creates tables on startup
    import subprocess
    proc = subprocess.Popen([".\\.venv\\Scripts\\python.exe", "-m", "uvicorn", "app.main:app", "--port", "8003"])
    import time
    time.sleep(4)

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # First time user journey
            await page.goto("http://127.0.0.1:8003", wait_until='networkidle')
            await page.wait_for_timeout(1000)
            
            # Go to projects
            await page.goto("http://127.0.0.1:8003/projects", wait_until='networkidle')
            await page.wait_for_timeout(1000)
            
            # Click New Project
            await page.click("text=New Project")
            await page.wait_for_timeout(500)
            await page.fill("input[name=name]", "First Project")
            await page.fill("textarea[name=description]", "A brand new disposable project")
            await page.click("button:has-text('Create Project')")
            await page.wait_for_timeout(1000)

            # Go to New Mission
            await page.goto("http://127.0.0.1:8003/new", wait_until='networkidle')
            await page.wait_for_timeout(1000)
            # Select project (the first one)
            await page.click("text=First Project")
            await page.click("button:has-text('Next: Mission Name')")
            
            await page.fill("input[placeholder='Enter mission name...']", "First Mission")
            await page.click("button:has-text('Next: Data Upload')")
            
            # (Data Upload) Since we can't upload easily, we just click next if allowed or skip
            
            print("First time journey partial test passed!")
            await browser.close()
    finally:
        proc.terminate()
        # restore db
        if os.path.exists('app/aerorecon.db'):
            os.remove('app/aerorecon.db')
        if os.path.exists('app/aerorecon.db.tmp'):
            os.rename('app/aerorecon.db.tmp', 'app/aerorecon.db')

if __name__ == '__main__':
    asyncio.run(test_first_time())
