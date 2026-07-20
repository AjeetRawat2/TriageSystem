import pandas as pd

# 1. Stream the raw Parquet file
print("Loading raw dataset from Hugging Face...")
df = pd.read_parquet("hf://datasets/alvanlii/devpost-hackathon-projects/combined_hackathons.parquet")

# 2. Extract exactly 5,000 random rows
# We don't drop nulls or duplicates here—you will handle that in your own EDA!
print("Extracting 5,000 raw rows...")
raw_5k_df = df.sample(n=5000, random_state=42).reset_index(drop=True)

# 3. Export to CSV keeping ALL original columns
export_filename = "devpost_raw_5k.csv"
raw_5k_df.to_csv(export_filename, index=False)

print(f"\nSuccess! {len(raw_5k_df)} raw rows exported to: {export_filename}")
print(f"Columns ready for your analysis: {raw_5k_df.columns.tolist()}")