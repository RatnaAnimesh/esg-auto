import pandas as pd
import requests
import time
import re
import os

def search_ticker_yfinance(company_name):
    """
    Fallback method to search for an NSE ticker using Yahoo Finance API if a direct CIN mapping is unavailable.
    """
    # Clean the company name to improve search results
    clean_name = company_name.replace("LIMITED", "").replace("LTD", "").strip()
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={clean_name}&quotesCount=5&newsCount=0"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'quotes' in data and len(data['quotes']) > 0:
                for quote in data['quotes']:
                    symbol = quote.get('symbol', '')
                    # Look specifically for NSE listings (.NS suffix)
                    if symbol.endswith('.NS'):
                        return symbol.replace('.NS', '')
                    # Fallback to BSE listings (.BO suffix)
                    elif symbol.endswith('.BO'):
                        return symbol.replace('.BO', '')
    except Exception as e:
        print(f"Error searching {company_name}: {e}")
    return ""

def main():
    csv_path = "data/processed/consolidated/brsr_consolidated.csv"
    print(f"Loading {csv_path}...")
    
    try:
        df = pd.read_csv(csv_path, low_memory=False)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_path}")
        return

    if 'NSESymbol' not in df.columns:
        print("NSESymbol column not found. Creating it...")
        df['NSESymbol'] = ""

    updated_count = 0
    total_missing = df['NSESymbol'].isna().sum() + (df['NSESymbol'] == '').sum()
    
    print(f"Found {total_missing} rows with missing NSESymbol. Resolving all missing symbols in the background...")

    for index, row in df.iterrows():
        symbol = str(row.get('NSESymbol', ''))
        if symbol.lower() == 'nan' or symbol.strip() == '':
            cin = row.get('Corporate Identity Number', '')
            company_name = row.get('Name Of The Company', row.get('CompanyName', ''))
            
            if not pd.isna(company_name) and company_name != '':
                print(f"Resolving Symbol for CIN: {cin} | Name: {company_name}...")
                
                resolved_symbol = search_ticker_yfinance(company_name)
                
                if resolved_symbol:
                    df.at[index, 'NSESymbol'] = resolved_symbol
                    updated_count += 1
                    print(f" -> Found Symbol: {resolved_symbol}")
                else:
                    print(f" -> Failed to find Symbol.")
                    
                time.sleep(0.1)

    if updated_count > 0:
        print(f"\\nSuccessfully updated {updated_count} symbols.")
        print(f"Saving updated CSV to {csv_path}...")
        df.to_csv(csv_path, index=False)
        print("Done.")
    else:
        print("\\nNo symbols were updated (either none were missing, or search failed for all).")

if __name__ == "__main__":
    main()
