from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Log all network requests that contain "api/" or "xbrl"
        def log_request(request):
            if "api" in request.url.lower() or "xbrl" in request.url.lower():
                print("REQUEST URL:", request.url)
        
        page.on("request", log_request)
        page.goto("https://www.nseindia.com/companies-listing/corporate-filings-annual-reports-xbrl", wait_until="networkidle")
        time.sleep(3)
        browser.close()
        
if __name__ == "__main__":
    run()
