import pandas as pd
df = pd.read_csv('/Users/ashishmishra/animeshratna/nsral/BRSR/data/brsr_consolidated.csv', nrows=0)
print(f"Total columns: {len(df.columns)}")
with open('data/csv_headers_list.txt', 'w') as f:
    f.write('\n'.join(df.columns))
