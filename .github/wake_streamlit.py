# Opens the live dashboard in a headless browser so Streamlit Community Cloud sees a visit.
# If the app is already asleep, it clicks the wake-up button and waits for the app to load.
from playwright.sync_api import TimeoutError, sync_playwright

URL = "https://maharashtra-elnino-vulnerability.streamlit.app/"

with sync_playwright() as p:
    page = p.chromium.launch().new_page()
    page.goto(URL, timeout=120_000)
    try:
        page.get_by_role("button", name="Yes, get this app back up!").click(timeout=15_000)
        print("app was asleep, wake-up requested")
    except TimeoutError:
        print("app was awake")
    page.frame_locator("iframe").first.get_by_text("Maharashtra vulnerability map").wait_for(timeout=300_000)
    print("app loaded")
