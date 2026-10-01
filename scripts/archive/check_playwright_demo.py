import asyncio, json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--disable-web-security'])
        ctx = await browser.new_context(viewport={'width':1920,'height':1080})

        # Capture console errors
        console_errors = []
        page = await ctx.new_page()
        page.on('console', lambda m: console_errors.append((m.type, m.text)) if m.type == 'error' else None)
        page.on('pageerror', lambda e: console_errors.append(('page_error', str(e))))

        # 1. Dashboard
        print("=== DASHBOARD ===")
        await page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
        await page.wait_for_timeout(2000)
        content = await page.content()
        await page.screenshot(path='demo/mars_hkairport01_quality/demo_dashboard.png')

        mars_visible = 'MARS HKairport01' in content or 'mars_hkairport01' in content
        colorado_visible = '95f51b12' in content or 'Colorado' in content or 'degraded' in content.lower()
        aerorecon_visible = 'AERORECON' in content
        print(f'  AERORECON branding: {aerorecon_visible}')
        print(f'  MARS mission visible: {mars_visible}')
        print(f'  Colorado job visible: {colorado_visible}')

        # Check for completed count
        import re
        completed = re.findall(r'completed', content, re.I)
        print(f'  "completed" mentions: {len(completed)}')

        # 2. Navigate to MARS workspace
        print()
        print("=== MARS WORKSPACE ===")
        await page.goto('http://127.0.0.1:8000/workspace/mars_hkairport01_quality', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        content2 = await page.content()
        await page.screenshot(path='demo/mars_hkairport01_quality/demo_workspace.png')

        dense_ok = 'dense' in content2.lower() or 'cloud' in content2.lower()
        mesh_ok = 'mesh' in content2.lower() or '355' in content2
        texture_ok = 'texture' in content2.lower() or 'glb' in content2.lower() or 'textured' in content2.lower()
        measure_ok = 'measure' in content2.lower()
        report_ok = 'report' in content2.lower() or '99.3' in content2 or 'RELATIVE' in content2
        download_ok = 'download' in content2.lower() or 'PLY' in content2 or 'GLB' in content2
        print(f'  Dense cloud section: {dense_ok}')
        print(f'  Mesh section: {mesh_ok}')
        print(f'  Texture section: {texture_ok}')
        print(f'  Measurements: {measure_ok}')
        print(f'  Reports: {report_ok}')
        print(f'  Downloads: {download_ok}')

        # 3. Colorado workspace
        print()
        print("=== COLORADO WORKSPACE ===")
        await page.goto('http://127.0.0.1:8000/workspace/95f51b12-b771-47bf-9201-c3700f9475a7', wait_until='networkidle')
        await page.wait_for_timeout(3000)
        content3 = await page.content()
        await page.screenshot(path='demo/mars_hkairport01_quality/demo_colorado.png')

        co_viewer = 'viewer' in content3.lower() or 'mesh' in content3.lower() or 'point' in content3.lower()
        co_degraded = 'degraded' in content3.lower() or 'FAIL' in content3 or '76' in content3
        print(f'  Viewer present: {co_viewer}')
        print(f'  Degraded status shown: {co_degraded}')

        # 4. Console errors
        print()
        print("=== CONSOLE ERRORS ===")
        if console_errors:
            for t,m in console_errors[:10]:
                print(f'  [{t}] {m[:120]}')
        else:
            print('  NONE')

        await browser.close()
        return console_errors

asyncio.run(run())
