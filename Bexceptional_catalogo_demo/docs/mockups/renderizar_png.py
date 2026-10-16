import asyncio, pathlib
from playwright.async_api import async_playwright
base = pathlib.Path('.').resolve(); out = base / 'png'; out.mkdir(exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 900, 'height': 1200})
        for svg in sorted((base / 'svg').glob('*.svg')):
            await pg.set_content(f'<html><body style="margin:0">{svg.read_text()}</body></html>')
            await pg.screenshot(path=str(out / (svg.stem + '.png')))
        await b.close()
asyncio.run(main())
