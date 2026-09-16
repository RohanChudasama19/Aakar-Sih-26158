import asyncio
import os

from playwright.async_api import async_playwright


async def run():
    with open("e2e_jid.txt", "r") as f:
        jid = f.read().strip()

    print(f"Running E2E tests for job: {jid}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

        network_logs = []
        page.on("response", lambda res: network_logs.append((res.status, res.url)))

        print("Navigating to index...")
        await page.goto("http://localhost:8000/")

        try:
            # Wait for mission cards to load
            await page.wait_for_selector(".mission-card")

            # Click the specific job
            print("Clicking job...")
            await page.click(f'.mission-card[data-id="{jid}"]')

            print("Waiting for detail view...")
            await page.wait_for_selector("text=3D Viewer")

            print("Clicking 3D Viewer tab...")
            await page.click("text=3D Viewer")

            print("Waiting for viewer canvas...")
            await page.wait_for_selector("canvas", timeout=15000)
            await page.wait_for_timeout(2000)
        except Exception as e:
            print("Canvas did not appear!", str(e))
            await browser.close()
            return

        os.makedirs("docs/viewer_verification", exist_ok=True)

        modes = [
            ("Textured Mesh", "textured.png"),
            ("Mesh (Geometry)", "mesh.png"),
            ("Dense Point Cloud", "dense.png"),
            ("Sparse Point Cloud", "sparse.png"),
            ("Semantic", "semantic.png"),
            ("Confidence / Coverage", "confidence.png")
        ]

        for mode, filename in modes:
            print(f"Testing mode: {mode}")
            try:
                await page.select_option("select#representation-selector", label=mode)
                await page.wait_for_selector(".viewer-loading", state="hidden", timeout=15000)
                await page.wait_for_timeout(1000)

                obj_type = await page.evaluate("window.getCurrentViewerType ? window.getCurrentViewerType() : 'Unknown'")
                print(f"  Object type: {obj_type}")
                await page.screenshot(path=f"docs/viewer_verification/{filename}")
            except Exception as e:
                print(f"Failed on {mode}: {e}")

        print("Running switching test...")
        for i in range(3):
            for mode, _ in modes:
                try:
                    await page.select_option("select#representation-selector", label=mode)
                    await page.wait_for_selector(".viewer-loading", state="hidden", timeout=5000)
                except:
                    pass
        print("Switching test completed.")

        await browser.close()

        print("\n=== Console Logs ===")
        for log in console_logs:
            print(log)

        print("\n=== Network Status ===")
        for status, url in network_logs:
            if any(x in url for x in [".ply", ".glb", ".json", "representations"]):
                print(f"{status} {url}")

if __name__ == '__main__':
    asyncio.run(run())
