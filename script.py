import pandas as pd

# Load Excel files
main_df = pd.read_excel("main.xlsx")
vendor_df = pd.read_excel("vendor.xlsx")

# Normalize column names to lowercase and strip whitespace
main_df.columns = main_df.columns.str.strip().str.lower()
vendor_df.columns = vendor_df.columns.str.strip().str.lower()

# Rename for easier merging
vendor_df.rename(columns={
    'item number': 'product code',
    'new price': 'updated price'
}, inplace=True)

# Merge and update prices
merged_df = main_df.merge(
    vendor_df[['product code', 'updated price']],
    on='product code',
    how='left'
)

# Replace unit price if updated price is available
merged_df['unit price'] = merged_df['updated price'].combine_first(merged_df['unit price'])

# Drop temporary column
merged_df.drop(columns='updated price', inplace=True)

# Save over the original file
merged_df.to_excel("main.xlsx", index=False)

print("✅ main.xlsx has been updated with new prices.")