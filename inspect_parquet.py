import pandas as pd

try:
    df = pd.read_parquet("p2p_data.parquet")
    print(f"Columns in p2p_data.parquet: {df.columns.tolist()}")
    
    entity_col = None
    for c in ['entity','company','brand','entity_name', 'entity_source_file']:
        if c in df.columns:
            entity_col = c
            break
            
    if entity_col:
        print(f"Entity column found: {entity_col}")
        print(f"Unique values in {entity_col}: {df[entity_col].unique()}")
    else:
        print("No entity column found.")
        
except Exception as e:
    print(f"Error reading parquet file: {e}")
