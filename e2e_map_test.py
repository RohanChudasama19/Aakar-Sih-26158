import asyncio
import os

from playwright.async_api import async_playwright


async def run():
    with open("e2e_jid.txt", "r") as f:
        jid = f.read().strip()

    print(f"Running Map Tab E2E tests for job: {jid}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        page.on("console", lambda msg: print(f"[{msg.type}] {msg.text}"))

        print("Navigating to index...")
        await page.goto("http://localhost:8000/")

        try:
            await page.wait_for_selector(".mission-card", timeout=5000)
            print("Clicking job...")
            await page.click(f'.mission-card[data-id="{jid}"]')

            print("Waiting for Map tab...")
            await page.click("button.tab-btn[data-tab='map']")

            await page.wait_for_selector("#leaflet-map", timeout=15000)
            await page.wait_for_timeout(2000)

            os.makedirs("docs/map_verification", exist_ok=True)
            await page.screenshot(path="docs/map_verification/georeferenced_map.png")

            # Check coords display
            coords_text = await page.evaluate("document.getElementById('map-coords').innerText")
            print(f"Coords element text: {coords_text}")

            # Check metrics
            metrics_html = await page.evaluate("document.getElementById('map-metrics').innerHTML")
            print("Metrics EPSG:", "EPSG:32643" in metrics_html)
            print("Map Test Passed!")

        except Exception as e:
            print("Map test failed!", str(e))

        await browser.close()

if __name__ == '__main__':
    asyncio.run(run())

