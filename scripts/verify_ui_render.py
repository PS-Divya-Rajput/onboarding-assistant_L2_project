"""Verify Streamlit UI mount, computed fonts, and capture clean screenshots."""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SCREENSHOTS_DIR = Path(__file__).resolve().parent.parent / "docs" / "screenshots"


def main():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=EDGE_PATH,
            headless=True,
            args=["--disable-gpu", "--no-sandbox"],
        )

        # 1. Desktop Viewport (1440px)
        context_desktop = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context_desktop.new_page()

        print("Navigating to http://localhost:8501...")
        page.goto("http://localhost:8501")

        # Wait for Streamlit to connect and mount the UI components
        print("Waiting for .wordmark element...")
        page.wait_for_selector(".wordmark", timeout=20000)
        print("UI mounted successfully!")

        # Check fonts
        wordmark_font = page.locator(".wordmark").first.evaluate("el => window.getComputedStyle(el).fontFamily")
        body_font = page.locator("body").evaluate("el => window.getComputedStyle(el).fontFamily")
        chip_font = page.locator(".repo-chip").first.evaluate("el => window.getComputedStyle(el).fontFamily")

        print(f"Wordmark Font:  {wordmark_font}")
        print(f"Body Font:      {body_font}")
        print(f"Repo Chip Font: {chip_font}")

        # Capture desktop screenshot
        desktop_file = SCREENSHOTS_DIR / "desktop_1440.png"
        page.screenshot(path=str(desktop_file))
        print(f"Desktop screenshot saved to {desktop_file}")

        # 2. Mobile Viewport (390px)
        context_mobile = browser.new_context(viewport={"width": 390, "height": 844})
        page_mobile = context_mobile.new_page()
        page_mobile.goto("http://localhost:8501")
        page_mobile.wait_for_selector(".wordmark", timeout=20000)

        mobile_file = SCREENSHOTS_DIR / "mobile_390.png"
        page_mobile.screenshot(path=str(mobile_file))
        print(f"Mobile screenshot saved to {mobile_file}")

        browser.close()

    print("SUCCESS: UI rendering verified and screenshots captured.")


if __name__ == "__main__":
    main()

