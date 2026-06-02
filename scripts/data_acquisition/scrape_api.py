import requests
import json
import pandas as pd
import time

headers = {
    'Accept': '*/*',
    'Sec-Fetch-Site': 'same-origin',
    'Cookie': 'bm_sv=AEE4043001B018632F25B5E9B5D64BF1~YAAQLhzFF2snWT+eAQAASNO9aB8MGd99qORr2x4h2oGMblvGK5xX6aJRw5cy0OdJ2Lq/3CCZ9WE2f4o8EHUy5JP8Kk3B5gjgHznIGtmStmxvCUt1lMuqirChXvaOua0OcU8s9omEEQvXYqkTOgOd1ZZ4Y4qHD78j2gKHgSekd0cfJ1mk/BjNj35VFRvaG/JOkwvqBulhRTsqkbDLdtagdlnHFQhLs3G/3CLKOtbETKaqAT6C7qN6iPx69fN72grxUncXMPwGmw==~1; ak_bmsc=875DC11509740735EB61B93C4676F7F1~000000000000000000000000000000~YAAQLRzFF0u2vT6eAQAAYu+1aB8MwSk7/IZn/bLHnbq1JlambQyzi1Yqz99HZJABTiHGLa68vRpObexi9m6wVhDucq9EngnUxtx7ZPn40/OPokGSiC/D3EocOJWsKIJJVru19Ov/9nU5YILPOylduqK0rLQlxQrRFwkHVzZj9V3Oqgyd08H9nntLPrxa3zXY8+KyezJfLsboQr4f47q8oZ0mZpVZevXMccP/DFngzXJ6BXfXNDFJurumrkU5rz+zhqo1qvKDnU4OKaMwtUww43atR2jtfsInLSvTLy/9+dboGvQzzjjoGhiTNRjnfCfRYXQk3k3yt3GSBALAE+5RWXwbWrOVrTUGy04Wwjmt79h1XiX8rG9pqNuLvVhqdTenpwKBaPZu75MTHJXPhIfz2ReB9AD5k4PZe0FNuIls52cRUqrmkY8Af6mUFVS485SlSG0/ZxXZHyNjejR3rp+2qIwKzZw0FQ/Vc1s=; connect.sid=s%3AIhQ8yMoKEQcAEfeEyT-DgEsb8yUMF8AE.kbFVk8SHMMFUrbUgvJbAQDdpzR%2B3JxyIjCTOGw%2FCvKg',
    'Referer': 'https://www.nse-esgrating.com/esg-ratings',
    'Sec-Fetch-Dest': 'empty',
    'Accept-Language': 'en-IN,en-GB;q=0.9,en;q=0.8',
    'Sec-Fetch-Mode': 'cors',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.5 Safari/605.1.15',
    'Connection': 'keep-alive'
}

all_companies = []
page = 1
total_pages = 1

while page <= total_pages:
    url = f'https://www.nse-esgrating.com/api/companies?pageIndex={page}&pageSize=100'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        companies = data.get('companies', [])
        all_companies.extend(companies)
        if page == 1:
            total_pages = data.get('paginationMeta', {}).get('totalPages', 1)
    page += 1
    time.sleep(0.5)

# Save the raw JSON first to see the exact keys
with open('data/reference/scores/nsral_scores_full.json', 'w') as f:
    json.dump(all_companies, f, indent=2)

df = pd.DataFrame(all_companies)
print("Keys in dataframe:", list(df.columns))

# Just map whatever keys we have to Company Name and ESG Ratings
key_map = {}
for col in df.columns:
    if 'company' in col.lower() or 'name' in col.lower():
        key_map[col] = 'Company Name'
    elif 'score' in col.lower() or 'rating' in col.lower():
        key_map[col] = 'ESG Ratings'

df = df.rename(columns=key_map)
df.to_csv('data/reference/scores/nsral_scores_full.csv', index=False)
print("Successfully extracted and saved", len(df), "companies to CSV!")
