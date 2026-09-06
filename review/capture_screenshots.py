"""Refresh the documented web screenshots from the local demo gallery."""
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get('PORTAL_URL', 'http://127.0.0.1:8765')
CAPTURES = [
    (1440, 1100, ['docs/screenshots/portal.png', 'review/screenshots/portal-desktop.png',
                  'review/screenshots/pages-desktop.png']),
    (900, 900, ['docs/screenshots/portal-tablet.png', 'review/screenshots/portal-tablet.png']),
    (390, 844, ['docs/screenshots/portal-mobile.png', 'review/screenshots/portal-mobile.png',
                'review/screenshots/pages-mobile-390.png']),
    (360, 800, ['review/screenshots/portal-small-mobile.png', 'review/screenshots/pages-mobile-360.png']),
]


def main():
    with sync_playwright() as p:
        chrome = os.environ.get('CHROME_BIN', '/usr/bin/google-chrome')
        browser = p.chromium.launch(headless=True, executable_path=chrome if Path(chrome).exists() else None)
        try:
            for width, height, destinations in CAPTURES:
                context = browser.new_context(viewport={'width': width, 'height': height}, reduced_motion='reduce')
                page = context.new_page()
                page.goto(BASE, wait_until='networkidle')
                page.evaluate('document.fonts.ready')
                page.locator('#artwork').evaluate('(img) => img.decode()')
                page.mouse.move(0, 0)
                capture = page.screenshot(full_page=True)
                for destination in destinations:
                    path = ROOT / destination
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(capture)
                print(f'Captured {width} x {height}: {", ".join(destinations)}', flush=True)
                context.close()
        finally:
            browser.close()


if __name__ == '__main__':
    main()
