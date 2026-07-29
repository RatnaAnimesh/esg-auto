import pandas as pd
import requests

def main():
    # Fetch accurate sectors from TradingView Screener for Sri Lanka
    url = "https://scanner.tradingview.com/srilanka/scan"
    payload = {
        "columns": ["name", "description", "sector"],
        "range": [0, 500],
        "sort": {"sortBy": "name", "sortOrder": "asc"}
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.post(url, json=payload, headers=headers)
    
    if r.status_code != 200:
        print("Failed to fetch from TradingView API")
        return
        
    data = r.json().get("data", [])
    
    # Create mapping
    # Note: TradingView uses symbol without CSE prefix. e.g. ABAN.N0000
    sector_map = {}
    for item in data:
        symbol = item["d"][0]
        sector = item["d"][2]
        # Some sectors might be None, map them to 'Unknown'
        sector_map[symbol] = sector if sector else "Unknown"

    # Load existing CSV
    df = pd.read_csv("cse_companies.csv")
    
    # Extract raw symbol (remove CSE: prefix) to match TradingView
    df['Raw_Symbol'] = df['Symbol'].str.replace('CSE:\s*', '', regex=True).str.strip()
    
    # Apply mapping
    df['Sector'] = df['Raw_Symbol'].map(sector_map)
    
    # Fill any missing sectors with 'Unknown'
    df['Sector'] = df['Sector'].fillna('Unknown')
    
    # Drop intermediate column
    df = df.drop(columns=['Raw_Symbol'])
    
    # Save back to CSV
    df.to_csv("cse_companies.csv", index=False)
    print("Successfully updated cse_companies.csv with exact sector data from TradingView.")
    
    # Show stats
    print(df['Sector'].value_counts())

if __name__ == "__main__":
    main()
