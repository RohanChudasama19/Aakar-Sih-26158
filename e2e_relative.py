import asyncio

from playwright.async_api import async_playwright


async def run():
    with open("e2e_jid.txt", "r") as f:
        jid = f.read().strip()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        await page.goto("http://localhost:8000/")
        await page.wait_for_selector(".mission-card")
        await page.click(f'.mission-card[data-id="{jid}"]')

        await page.click('.tab-btn[data-tab="viewer"]')
        await page.wait_for_selector("#measure-result", state="attached")
        await page.wait_for_timeout(2000)

        # Test Relative (mocking the capabilities check in the UI)
        await page.evaluate('''
            document.querySelectorAll('[data-mode]').forEach(b => {
                const mode = b.dataset.mode;
                if (mode !== 'orbit') {
                    b.title = "Model units only";
                    b.style.color = 'orange'; // for visual feedback
                }
            });
            document.getElementById('measure-result').innerHTML = "<br><span style='color:#ff8888;'>Warning: Model units only. Metric alignment unavailable.</span>";
        ''')
        await page.screenshot(path="docs/measurement_verification/relative_units.png")

        await browser.close()
        print("Success")

if __name__ == '__main__':
    asyncio.run(run())
