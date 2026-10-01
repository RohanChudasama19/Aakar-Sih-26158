import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto('http://127.0.0.1:8000/workspace/mars_hkairport01_quality', wait_until='networkidle')
        await page.wait_for_timeout(2000)

        sizes = await page.evaluate('''() => {
            const getBox = (el) => el ? {w: el.clientWidth, h: el.clientHeight} : null;
            const container = document.querySelector('[class*="workspaceArea"]');
            const viewport = document.querySelector('[class*="viewport"]');
            const sidepanels = document.querySelectorAll('[class*="sidePanel"]');
            const arv = document.querySelector('[class*="viewport"] > div');
            return {
                window: {w: window.innerWidth, h: window.innerHeight},
                container: getBox(container),
                viewport: getBox(viewport),
                arv: getBox(arv),
                sidepanels: Array.from(sidepanels).map(getBox)
            };
        }''')
        print(sizes)
        await browser.close()

asyncio.run(run())

import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        
        page.on("console", lambda msg: print(f"Browser: {msg.type}: {msg.text}"))
        
        print("Navigating...")
        await page.goto("http://127.0.0.1:8000/#/workspace/mars_hkairport01_quality")
        await page.wait_for_timeout(5000)
        
        # Check if Scientific Intelligence panel is present
        content = await page.content()
        if "Scientific Intelligence" in content:
            print("Panel is present.")
        else:
            print("Panel is missing!")
            print(content[:1000]) # Print snippet
            
        await browser.close()

asyncio.run(run())

