import pandas as pd
import os

# Using the correct path found in the previous listing
correct_path = '/tmp/file_attachments/jules_session_3869290939356711333_update-outliers-savings-logic-3869290939356711333 (7)/p2p_data.parquet'

print(f"--- Checking {correct_path} ---")
if os.path.exists(correct_path):
    try:
        df = pd.read_parquet(correct_path)
        
        # Check entity_source_file
        if 'entity_source_file' in df.columns:
            print(f"Unique entity_source_file: {df['entity_source_file'].unique().tolist()}")
            print(f"Counts:\n{df['entity_source_file'].value_counts()}")
        
        # Check buying_legal_entity
        if 'buying_legal_entity' in df.columns:
            print(f"Unique buying_legal_entity: {df['buying_legal_entity'].unique().tolist()}")
            print(f"Counts:\n{df['buying_legal_entity'].value_counts()}")
            
    except Exception as e:
        print(f"Error reading parquet: {e}")
else:
    print("File does not exist.")
