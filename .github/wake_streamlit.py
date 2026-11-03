# Opens the live dashboard in a headless browser so Streamlit Community Cloud sees a visit.
# If the app is already asleep, it clicks the wake-up button.
# Avoid relying on one exact text in the first iframe: Streamlit's page structure
# and text rendering can vary between deployments.
from __future__ import annotations

import re

from playwright.sync_api import TimeoutError, sync_playwright

URL = "https://maharashtra-elnino-vulnerability.streamlit.app/"
APP_TEXT = "Maharashtra vulnerability map"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1200})
    page.goto(URL, wait_until="domcontentloaded", timeout=120_000)

    try:
        page.get_by_role(
            "button", name=re.compile(r"yes, get this app back up!", re.IGNORECASE)
        ).click(timeout=15_000)
        print("app was asleep, wake-up requested")
    except TimeoutError:
        print("app was awake or no wake-up button was present")

    # Give the app time to wake and render. Do not fail the keep-awake job just
    # because a heading changed or is rendered outside the first iframe.
    try:
        page.wait_for_load_state("networkidle", timeout=60_000)
    except TimeoutError:
        print("network remained active; continuing to check the rendered page")

    try:
        page.get_by_text(APP_TEXT, exact=False).first.wait_for(timeout=60_000)
        print("app loaded (text found in the page)")
    except TimeoutError:
        text_found = False
        for frame in page.frames:
            try:
                frame.get_by_text(APP_TEXT, exact=False).first.wait_for(timeout=10_000)
                text_found = True
                break
            except TimeoutError:
                continue

        if text_found:
            print("app loaded (text found in a frame)")
        else:
            # Visiting the app is the purpose of this workflow. The app might
            # render differently or be temporarily unavailable; log diagnostics
            # without turning a successful request into a failed keep-awake run.
            print("Page visited; expected heading was not found. This is non-fatal.")
            print(f"final URL: {page.url}")
            print(f"page title: {page.title()}")

    browser.close()
