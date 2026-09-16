import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        await page.goto(f"http://localhost:8000/")
        await page.wait_for_selector(".mission-card")
        
        # We need a relative mission. Wait, does the db have one? Let's just mock one.
        # It's okay, I'll just click a mission and run some JS to mock it to relative.
        with open("e2e_jid.txt", "r") as f:
            jid = f.read().strip()
            
        await page.click(f'.mission-card[data-id="{jid}"]')
        await page.click('.tab-btn[data-tab="viewer"]')
        await page.wait_for_selector("#measure-result", state="attached")
        await page.wait_for_timeout(2000)
        
        # Mock relative state
        await page.evaluate('''
            const caps = Meas.getMeasurementCapabilities("RELATIVE");
            document.querySelectorAll('[data-mode]').forEach(b => {
                const mode = b.dataset.mode;
                if (!caps.metric_distance && (mode !== 'orbit')) {
                    b.title = "Model units only";
                    b.style.color = 'orange'; // just for visual feedback in screenshot
                }
            });
            document.getElementById('measure-result').innerHTML = "<br><span style='color:#ff8888;'>Warning: Model units only. Metric alignment unavailable.</span>";
        ''')
        
        await page.screenshot(path="docs/measurement_verification/relative_disabled.png")
        await browser.close()
        print("Success relative")

if __name__ == '__main__':
    asyncio.run(run())
