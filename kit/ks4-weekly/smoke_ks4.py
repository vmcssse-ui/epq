#!/usr/bin/env python3
# © 2026 Dr Vitor Merissi de Carvalho · Edu.Ai SV Digital — Edu.Ai Ecosystem framework, Weekly Page Kit (KS4 edition). All rights reserved. Harlington School deployment licensed for internal use. Not for reproduction or redistribution without written permission.
"""
smoke_ks4.py <site-folder> <page.html>

Serves <site-folder> with python's http.server, opens <page.html> in headless
Chromium via Playwright and checks the page behaves:

  * no JS exceptions and no console errors (network 404s are listed separately)
  * 33 week cards (or however many the manifest has: passed as --weeks N)
  * the week-nav chips jump to their card and the scrollspy marks the chip .on
  * tick-boxes persist across a reload (localStorage)
  * a #w7 deep link lands on week 7 and flashes it
  * the self-check pill appears

Prints a PASS/FAIL line per check and exits non-zero on any failure.
"""
import os
import subprocess
import sys
import time

from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium" if os.path.isdir("/opt/pw-browsers/chromium") else None


def main(argv):
    weeks = 33
    if "--weeks" in argv:
        i = argv.index("--weeks")
        weeks = int(argv[i + 1])
        del argv[i:i + 2]
    folder, page_name = argv
    port = 8765
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=folder,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    url = "http://127.0.0.1:%d/%s" % (port, page_name)
    results = []

    def check(name, ok, detail=""):
        results.append(ok)
        print("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + detail) if detail else ""))

    try:
        with sync_playwright() as p:
            launch = {"headless": True}
            exe = None
            if CHROME:
                for root, dirs, files in os.walk(CHROME):
                    if "chrome" in files:
                        exe = os.path.join(root, "chrome")
                        break
            if exe:
                launch["executable_path"] = exe
            browser = p.chromium.launch(**launch)
            ctx = browser.new_context(viewport={"width": 1280, "height": 900},
                                      permissions=["clipboard-read", "clipboard-write"])
            pg = ctx.new_page()
            errors, console_errors, failed_requests = [], [], []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
            pg.on("requestfailed", lambda r: failed_requests.append(r.url))
            pg.goto(url, wait_until="load")
            pg.wait_for_timeout(600)
            check("page loads", pg.title() != "", "title=" + pg.title())
            check("no JS exceptions", not errors, "; ".join(errors)[:300])
            noise = [c for c in console_errors if "Failed to load resource" not in c]
            check("no console errors", not noise, "; ".join(noise)[:300])
            if console_errors and not noise:
                print("      (resource-load messages only: %d, e.g. %s)" % (len(console_errors), console_errors[0][:120]))
            n = pg.locator("article.wk").count()
            check("%d week cards" % weeks, n == weeks, "found %d" % n)
            check("%d nav chips" % weeks, pg.locator("a.nch").count() == weeks)
            # nav chip -> card
            pg.click('a.nch[data-w="20"]')
            pg.wait_for_timeout(900)
            # scroll-padding-top (88px, on html) and scroll-margin-top (92px, on the card) are
            # additive, so a targeted card lands ~180px down: below the sticky nav, in view.
            nav_b = pg.evaluate("document.getElementById('wknav').getBoundingClientRect().bottom")
            top = pg.evaluate("document.getElementById('w20').getBoundingClientRect().top")
            check("week nav chip scrolls to #w20", nav_b <= top <= 260, "top=%.0f, nav bottom=%.0f" % (top, nav_b))
            on = pg.evaluate("(document.querySelector('.nch.on')||{}).dataset ? document.querySelector('.nch.on').dataset.w : ''")
            check("scrollspy marks chip 20 .on", on == "20", "on=" + str(on))
            # ticks persist
            pg.check('input[data-t="w20_read"]')
            pg.wait_for_timeout(200)
            txt = pg.text_content("#ptxt")
            check("progress text updates", txt.startswith("1 of "), txt)
            pg.reload(wait_until="load")
            pg.wait_for_timeout(400)
            check("tick persists after reload", pg.is_checked('input[data-t="w20_read"]'))
            stored = pg.evaluate("Object.keys(localStorage).join(',')")
            check("localStorage key present", "_ticks" in stored, stored)
            pg.uncheck('input[data-t="w20_read"]')
            # deep link
            pg2 = ctx.new_page()
            pg2.goto(url + "#w7", wait_until="load")
            pg2.wait_for_timeout(900)
            top7 = pg2.evaluate("document.getElementById('w7').getBoundingClientRect().top")
            flashed = pg2.evaluate("document.getElementById('w7').classList.contains('target')")
            nav_b7 = pg2.evaluate("document.getElementById('wknav').getBoundingClientRect().bottom")
            check("#w7 deep link lands on week 7", nav_b7 <= top7 <= 260, "top=%.0f, nav bottom=%.0f" % (top7, nav_b7))
            check("#w7 gets the flash class", flashed)
            # copy-link button changes state
            pg2.click('#w7 .wlink')
            pg2.wait_for_timeout(300)
            check("copy-link button reacts", "copied" in (pg2.text_content("#w7 .wlink") or "").lower() or pg2.locator(".toast.show").count() > 0)
            # self-check pill
            pg2.wait_for_timeout(1500)
            pill = pg2.locator(".check").count()
            cls = pg2.evaluate("(document.querySelector('.check')||{className:''}).className")
            check("self-check pill appears", pill == 1, cls)
            if failed_requests:
                print("      failed requests (%d): %s" % (len(failed_requests), ", ".join(failed_requests[:4])))
            browser.close()
    finally:
        srv.terminate()
    ok = all(results)
    print("%s: %d/%d checks" % ("ALL PASS" if ok else "FAILURES", sum(results), len(results)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
