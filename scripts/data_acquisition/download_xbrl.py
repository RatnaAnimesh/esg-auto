import os
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import re

def sanitize_filename(name):
    # Remove invalid characters for filenames
    name = str(name).strip()
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def download_file(url, output_path, retries=3):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True, url
            else:
                if attempt == retries - 1:
                    return False, f"{url} (HTTP {response.status_code})"
        except Exception as e:
            if attempt == retries - 1:
                return False, f"{url} ({str(e)})"
        
        # Exponential backoff
        time.sleep(2 ** attempt)
        
    return False, url

def main():
    csv_path = '/Users/ashishmishra/Downloads/CF-BRSR-equities-09-Jul-2026.csv'
    output_dir = 'data/raw/xbrl'
    error_log = 'data/raw/failed_downloads.txt'
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading CSV...")
    df = pd.read_csv(csv_path)
    
    # Identify the correct columns despite weird whitespace
    company_col = [c for c in df.columns if 'COMPANY' in c.upper()][0]
    xbrl_col = [c for c in df.columns if 'XBRL' in c.upper()][0]
    
    # Filter valid URLs
    tasks = []
    for idx, row in df.iterrows():
        url = str(row[xbrl_col]).strip()
        company = str(row[company_col]).strip()
        
        if url.startswith('http') and url.endswith('.xml'):
            safe_name = sanitize_filename(company)
            # Add index or symbol if company names are duplicated? 
            # We'll just use company name. If duplicated, it overwrites with the latest.
            output_path = os.path.join(output_dir, f"{safe_name}.xml")
            
            # Skip if already downloaded (allows restarting script)
            if not os.path.exists(output_path):
                tasks.append((url, output_path))
    
    total_files = len(tasks)
    print(f"Found {total_files} new XBRL files to download.")
    
    if total_files == 0:
        return
        
    success_count = 0
    failed_urls = []
    
    # Sequential download with explicit delays to prevent IP ban
    for i, task in enumerate(tasks):
        url, output_path = task
        success, result = download_file(url, output_path)
        
        if success:
            success_count += 1
        else:
            failed_urls.append(result)
            
        if (i + 1) % 10 == 0 or (i + 1) == total_files:
            print(f"Progress: {i + 1}/{total_files} processed... (Success: {success_count}, Failed: {len(failed_urls)})")
            
        # Hard sleep removed to speed up processing
        # time.sleep(1.5)
                
    if failed_urls:
        with open(error_log, 'w') as f:
            for fail in failed_urls:
                f.write(f"{fail}\n")
        print(f"\nWARNING: {len(failed_urls)} downloads failed. Check {error_log}")
        
    print(f"\nDownload process complete. {success_count} files successfully downloaded to {output_dir}")

if __name__ == '__main__':
    main()
