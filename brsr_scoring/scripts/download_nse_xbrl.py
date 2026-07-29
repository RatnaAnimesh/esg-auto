import os
import sqlite3
import time
import random
import csv
import difflib
from pathlib import Path
from curl_cffi import requests

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
XBRL_DIR = DATA_DIR / "xbrl_annual_reports"
DB_PATH = DATA_DIR / "brsr.db"

def ensure_directories():
    XBRL_DIR.mkdir(parents=True, exist_ok=True)

def fetch_nse_symbols():
    csv_path = DATA_DIR / "EQUITY_L.csv"
    if not csv_path.exists():
        print("Downloading EQUITY_L.csv from NSE...")
        res = requests.get("https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv", impersonate="chrome")
        if res.status_code == 200:
            with open(csv_path, "w", encoding="utf-8") as f:
                f.write(res.text)
        else:
            raise Exception("Failed to download EQUITY_L.csv")

    name_to_symbol = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) >= 2:
                symbol = row[0].strip()
                name = row[1].strip().upper()
                name_to_symbol[name] = symbol
    return name_to_symbol

def get_companies_from_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT cin, name, financial_year_start, financial_year_end FROM Company_Master")
    companies = cursor.fetchall()
    conn.close()
    return companies

def get_session():
    session = requests.Session(impersonate="chrome")
    session.headers.update({
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-annual-reports"
    })
    # Hit homepage to grab initial cookies (nsit, etc)
    print("Initializing NSE Session...")
    res = session.get("https://www.nseindia.com")
    if res.status_code != 200:
        print(f"Warning: Homepage returned {res.status_code}")
    return session

def download_xbrl_for_symbol(session, cin, symbol, target_from_yr, target_to_yr):
    api_url = f"https://www.nseindia.com/api/annual-reports-xbrl?index=equities&symbol={symbol}"
    print(f"[{symbol}] Querying API for FY {target_from_yr}-{target_to_yr}...")
    try:
        res = session.get(api_url, timeout=30)
        if res.status_code != 200:
            print(f"[{symbol}] Error {res.status_code} fetching API")
            return False
    except Exception as e:
        print(f"[{symbol}] API request failed: {e}")
        return False

    try:
        data = res.json().get('data', [])
    except Exception as e:
        print(f"[{symbol}] JSON parsing failed: {e}")
        return False

    if not data:
        print(f"[{symbol}] No annual reports found.")
        return False

    # Find the first valid download URL matching the target year (Prefer Consolidated)
    download_url = None
    fallback_url = None
    
    for entry in data:
        if str(entry.get('fromYr')) != str(target_from_yr) or str(entry.get('toYr')) != str(target_to_yr):
            continue
            
        fname = entry.get('fileName', '')
        if fname.endswith('.zip') or fname.endswith('.xml'):
            if str(entry.get('submission_type', '')).lower() == 'consolidated':
                download_url = fname
                break
            elif not fallback_url:
                fallback_url = fname
                
    download_url = download_url or fallback_url
            
    if not download_url:
        print(f"[{symbol}] No valid zip/xml attachment found for FY {target_from_yr}-{target_to_yr}. Skipping.")
        return False

    file_ext = ".zip" if download_url.endswith(".zip") else ".xml"
    save_path = XBRL_DIR / f"{cin}{file_ext}"
    
    if save_path.exists():
        print(f"[{symbol}] File already exists ({save_path.name}). Skipping.")
        return True

    print(f"[{symbol}] Downloading {download_url}...")
    try:
        dl_res = session.get(download_url, timeout=120)
        if dl_res.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(dl_res.content)
            print(f"[{symbol}] Saved {save_path.name} ({len(dl_res.content)} bytes)")
            return True
        else:
            print(f"[{symbol}] Failed to download file. HTTP {dl_res.status_code}")
            return False
    except Exception as e:
        print(f"[{symbol}] Download failed: {e}")
        return False

def main():
    ensure_directories()
    name_to_symbol = fetch_nse_symbols()
    official_names = list(name_to_symbol.keys())
    
    companies = get_companies_from_db()
    print(f"Found {len(companies)} NSE companies in DB.")

    session = get_session()
    
    success_count = 0
    # Process all companies
    for cin, name, fy_start, fy_end in companies:
        query_name = name.upper()
        symbol = None
        
        # parse fy_start, fy_end
        try:
            p_start = fy_start.split("/")[-1]
            p_end = fy_end.split("/")[-1]
            target_from_yr = "20" + p_start if len(p_start) == 2 else p_start
            target_to_yr = "20" + p_end if len(p_end) == 2 else p_end
        except Exception as e:
            print(f"Could not parse years for {name}: {fy_start} - {fy_end}")
            continue
        
        # 1. Exact match
        if query_name in name_to_symbol:
            symbol = name_to_symbol[query_name]
        else:
            # 2. Fuzzy match
            matches = difflib.get_close_matches(query_name, official_names, n=1, cutoff=0.85)
            if matches:
                symbol = name_to_symbol[matches[0]]
                print(f"Fuzzy matched: {name} -> {matches[0]} ({symbol})")
        
        if not symbol:
            print(f"Could not map symbol for company: {name}")
            continue
            
        success = download_xbrl_for_symbol(session, cin, symbol, target_from_yr, target_to_yr)
        if success:
            success_count += 1
            
        # Rate limit
        time.sleep(random.uniform(2.0, 4.0))

    print(f"\nDone! Successfully processed {success_count} files in this batch.")

if __name__ == "__main__":
    main()
