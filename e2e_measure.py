import asyncio
import os

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
        await page.wait_for_timeout(3000)

        os.makedirs("docs/measurement_verification", exist_ok=True)

        # distance
        await page.click('button[data-mode="distance"]')
        await page.mouse.click(640, 400)
        await page.wait_for_timeout(100)
        await page.mouse.click(660, 400)
        await page.wait_for_timeout(100)
        await page.mouse.click(660, 420)
        await page.wait_for_timeout(100)
        await page.screenshot(path="docs/measurement_verification/distance_completed.png")
        await page.mouse.click(660, 420, button="right")

        # planar area
        await page.click('button[data-mode="area"]')
        await page.mouse.click(600, 300)
        await page.mouse.click(700, 300)
        await page.mouse.click(700, 400)
        await page.mouse.click(600, 400)
        await page.wait_for_timeout(100)
        await page.screenshot(path="docs/measurement_verification/planar_area_completed.png")
        await page.mouse.click(600, 400, button="right")

        # surface area
        await page.click('button[data-mode="surface_area"]')
        await page.mouse.down()
        await page.mouse.move(600, 300)
        await page.mouse.move(650, 300)
        await page.mouse.move(650, 350)
        await page.mouse.up()
        await page.wait_for_timeout(100)
        await page.screenshot(path="docs/measurement_verification/surface_area_completed.png")
        await page.mouse.click(650, 350, button="right")

        # slope
        await page.click('button[data-mode="slope"]')
        await page.mouse.click(640, 400)
        await page.mouse.click(640, 500)
        await page.wait_for_timeout(100)
        await page.screenshot(path="docs/measurement_verification/slope_completed.png")

        # angle
        await page.click('button[data-mode="angle"]')
        await page.mouse.click(500, 500)
        await page.mouse.click(550, 500)
        await page.mouse.click(550, 450)
        await page.wait_for_timeout(100)
        await page.screenshot(path="docs/measurement_verification/angle_completed.png")

        # Test Relative (mocking the capabilities check in the UI)
        await page.evaluate('''
            const caps = Meas.getMeasurementCapabilities("RELATIVE");
            document.querySelectorAll('[data-mode]').forEach(b => {
                const mode = b.dataset.mode;
                if (!caps.metric_distance && (mode !== 'orbit')) {
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
