from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to URL...")
        # Use wait_until='load' to avoid networkidle timeout
        page.goto('https://www.nse-esgrating.com/esg-ratings', wait_until='domcontentloaded', timeout=60000)
        
        print("Waiting for API to populate data...")
        time.sleep(10) # Hard wait for React to finish fetching and rendering
        
        data = page.evaluate('''() => {
            let rows = document.querySelectorAll('tr');
            let result = [];
            rows.forEach(row => {
                let cols = row.querySelectorAll('th, td');
                let rowData = [];
                cols.forEach(col => rowData.push(col.innerText.trim()));
                result.push(rowData);
            });
            return result;
        }''')
        
        if not data:
            print("No tr tags found. Dumping all div texts with some length:")
            texts = page.evaluate('''() => Array.from(document.querySelectorAll('div')).map(d => d.innerText).filter(t => t.length > 20 && t.includes('\\n'))''')
            print(texts[:5])
        else:
            print(f"Found {len(data)} rows.")
            for row in data[:5]:
                print(row)
            
        browser.close()

if __name__ == '__main__':
    run()
