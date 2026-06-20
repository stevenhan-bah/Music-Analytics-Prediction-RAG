import pandas as pd

df = pd.read_parquet("processed/master_dataset.parquet")

print(f"Shape: {df.shape}")
print(f"Columns: {df.columns}")
print(df.dtypes)


pd.set_option('display.max_columns', None)
pd.set_option("display.width", None)

print(df.head(20))


df.head(10000).to_csv("processed/preview_10k.csv", index=False)

df.to_csv('processed/master_dataset.csv', index = False)
