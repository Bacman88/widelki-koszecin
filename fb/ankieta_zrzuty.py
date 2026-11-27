import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox','--lang=pl-PL'], env={'LANG':'pl_PL.UTF-8','LANGUAGE':'pl','LC_ALL':'pl_PL.UTF-8','HOME':'/root'})
        pg = await b.new_page(viewport={'width': 390, 'height': 844}, device_scale_factor=3, locale='pl-PL')
        await pg.route('**/*', lambda r: r.abort() if 'google' in r.request.url else r.continue_())
        await pg.goto('http://localhost:8765/ankieta/', wait_until='networkidle')
        await pg.evaluate("localStorage.clear()"); await pg.add_style_tag(content='.bar{display:none!important}')
        async def opt(name, txt):
            await pg.locator(f'.opt[data-name="{name}"] label', has_text=txt).first.click()
        await opt('rola', 'pracuję'); await opt('wiek', '26')
        await pg.select_option('#miejsc', label='Strzebiń')
        await pg.locator('#k1').screenshot(path='/tmp/ank/k1.png')
        await pg.select_option('#z', label='Strzebiń Centrum')
        await pg.select_option('#do', label='Lubliniec PKP')
        await opt('dzien', 'robocze')
        await pg.fill('#na', '07:30'); await pg.fill('#po', '15:30'); await pg.evaluate('document.activeElement.blur()')
        await pg.locator('#k2').screenshot(path='/tmp/ank/k2.png')
        await pg.click('#pokaz'); await pg.wait_for_timeout(800)
        await pg.locator('#k3').screenshot(path='/tmp/ank/k3.png')
        await opt('ocena', 'Tak, pojechałbym')
        await pg.wait_for_timeout(300)
        await opt('dzis', 'autem')
        await pg.locator('#k4').screenshot(path='/tmp/ank/k4.png')
        await b.close()
asyncio.run(main())
