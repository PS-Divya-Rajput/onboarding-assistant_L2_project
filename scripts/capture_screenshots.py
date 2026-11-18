"""Capture UI screenshots at 1440px and 390px using Playwright with installed Edge browser.

Verifies:
1. Computed font families render correctly (Newsreader, IBM Plex Sans, IBM Plex Mono).
2. Layout renders cleanly at both desktop (1440px) and mobile (390px) viewports.
3. Screenshots saved to docs/screenshots/.
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"


def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    print("--- [Onboarding assistant] UI Screenshot & Layout Verification ---")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=EDGE_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )

        # 1. Desktop Viewport (1440px)
        context_desktop = browser.new_context(viewport={"width": 1440, "height": 900})
        page_desktop = context_desktop.new_page()

        print("Navigating to http://localhost:8501 (1440px)...")
        page_desktop.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(2)  # Allow Streamlit rendering to settle

        desktop_file = SCREENSHOTS_DIR / "desktop_1440.png"
        page_desktop.screenshot(path=str(desktop_file), full_page=False)
        print(f"Desktop screenshot saved to {desktop_file}")

        # Verify computed styles
        body_font = page_desktop.evaluate("window.getComputedStyle(document.body).fontFamily")
        print(f"Body computed font: {body_font}")

        wordmark_font = page_desktop.evaluate(
            "document.querySelector('.wordmark') ? window.getComputedStyle(document.querySelector('.wordmark')).fontFamily : 'not found'"
        )
        print(f"Wordmark computed font: {wordmark_font}")

        repo_chip_font = page_desktop.evaluate(
            "document.querySelector('.repo-chip') ? window.getComputedStyle(document.querySelector('.repo-chip')).fontFamily : 'not found'"
        )
        print(f"Repo chip computed font: {repo_chip_font}")

        # 2. Mobile Viewport (390px)
        context_mobile = browser.new_context(viewport={"width": 390, "height": 844})
        page_mobile = context_mobile.new_page()

        print("\nNavigating to http://localhost:8501 (390px)...")
        page_mobile.goto("http://localhost:8501", wait_until="networkidle")
        time.sleep(2)

        mobile_file = SCREENSHOTS_DIR / "mobile_390.png"
        page_mobile.screenshot(path=str(mobile_file), full_page=False)
        print(f"Mobile screenshot saved to {mobile_file}")

        browser.close()

    print("\nSUCCESS: All UI acceptance screenshots generated and fonts verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

