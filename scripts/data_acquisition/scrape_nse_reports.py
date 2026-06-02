import os
import time
import random
import pandas as pd
from playwright.sync_api import sync_playwright

def get_symbols(csv_path):
    df = pd.read_csv(csv_path, low_memory=False)
    # Filter out symbols that are missing or 'NOT_FOUND'
    symbols = df['NSESymbol'].dropna().unique()
    valid_symbols = [s for s in symbols if str(s).strip() != 'NOT_FOUND' and str(s).strip() != '']
    return valid_symbols

def random_delay(min_sec=5, max_sec=15):
    delay = random.uniform(min_sec, max_sec)
    print(f"Waiting for {delay:.2f} seconds to simulate human behavior...")
    time.sleep(delay)

def scrape_reports():
    csv_path = "data/processed/consolidated/brsr_consolidated.csv"
    pdf_dir = "data/raw/pdfs"
    os.makedirs(pdf_dir, exist_ok=True)
    
    symbols = get_symbols(csv_path)
    print(f"Loaded {len(symbols)} valid NSE symbols to process.")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        # Randomize user agents or use a realistic one
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        context = browser.new_context(user_agent=user_agent, viewport={"width": 1280, "height": 720})
        page = context.new_page()
        
        url = "https://www.nseindia.com/companies-listing/corporate-filings-annual-reports"
        
        try:
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("Successfully loaded NSE Annual Reports portal.")
            
            for symbol in symbols[:1]:
                print(f"\\nProcessing symbol: {symbol}")
                try:
                    # In a real implementation, we would inspect the NSE DOM to find the exact search input.
                    # Usually it's an input with placeholder "Enter Symbol or Company Name"
                    search_input = page.locator("input[placeholder*='Symbol']")
                    if search_input.count() > 0:
                        search_input.first.fill(symbol)
                        # Press Enter to search
                        search_input.first.press("Enter")
                        
                        # Wait for the table to update
                        page.wait_for_timeout(3000)
                        
                        # Find PDF links
                        pdf_links = page.locator("a[href$='.pdf']")
                        if pdf_links.count() > 0:
                            pdf_url = pdf_links.first.get_attribute('href')
                            print(f"Found PDF link for {symbol}: {pdf_url}")
                            # Download logic would go here.
                            # We would use page.expect_download() or requests.
                        else:
                            print(f"No PDF link found for {symbol}.")
                    else:
                        print("Search input not found. DOM might be different than expected.")
                        
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
                
                # Critical: Human-like delay to prevent Cloudflare ban
                random_delay(5, 15)
                
        except Exception as e:
            print(f"Failed to load the portal: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_reports()
