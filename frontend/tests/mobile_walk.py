import asyncio, sys
from playwright.async_api import async_playwright

BASE = "https://pro-mailer-2.preview.emergentagent.com"
OUT = "/tmp/mob"
STEPS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["edit", "clips", "extract", "paroles", "style", "more", "sheet", "replace"]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
        ctx = await browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
                                        locale="fr-FR", user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
        page = await ctx.new_page()
        await page.goto(BASE + "/login", wait_until="networkidle")
        await page.fill('input[type="email"]', "demo@beatcut.fr")
        await page.fill('input[type="password"]', "Demo1234!")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        await page.goto(BASE + "/studio.html", wait_until="networkidle")
        await page.evaluate("() => localStorage.setItem('bc_lang','fr')")
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUT}_home.png")
        for pg in ["morceaux","serie","compte","hook"]:
            await page.evaluate(f"() => go('{pg}')"); await page.wait_for_timeout(1200)
            await page.screenshot(path=f"{OUT}_pg_{pg}.png")
        await page.evaluate("() => go('morceaux')"); await page.wait_for_timeout(1500)
        await page.evaluate("() => window.scrollTo(0,0)")
        await page.locator(".page.show h3", has_text="Recette 150BPM").first.click(force=True)
        await page.wait_for_timeout(7000)
        for t in ["Continuer quand même", "Skip", "Passer"]:
            try:
                await page.click("text=" + t, timeout=800)
            except Exception:
                pass
        await page.wait_for_timeout(800)
        for st in STEPS:
            try:
                if st == "edit":
                    pass
                elif st in ("clips", "extract", "paroles", "style", "more"):
                    await page.evaluate(f"() => mobSheet('{st}')")
                elif st == "sheet":
                    await page.evaluate("() => mobSheet('more')")
                    await page.wait_for_timeout(400)
                    await page.evaluate("() => openPlanSheet(M.plans[1])")
                elif st == "menu":
                    await page.evaluate("() => toggleMobMenu()")
                elif st == "moreend":
                    await page.evaluate("() => { const m=document.getElementById('mobMore'); m.scrollTop=9999; }")
                elif st == "bpm":
                    await page.click('.transport .bpm-chip')
                elif st == "replace":
                    await page.evaluate("() => psReplace()")
                await page.wait_for_timeout(900)
                await page.screenshot(path=f"{OUT}_{st}.png")
                print("shot", st)
            except Exception as e:
                print("ERR", st, e)
        await browser.close()

asyncio.run(main())
