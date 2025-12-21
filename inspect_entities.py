import pandas as pd
from pathlib import Path

files = ["MEPL.xlsx", "MLPL.xlsx"]

for file in files:
    print(f"--- Inspecting {file} ---")
    try:
        df = pd.read_excel(file, skiprows=1)
        
        # Check for entity columns
        entity_cols = [c for c in df.columns if 'entity' in str(c).lower()]
        print(f"Entity columns found: {entity_cols}")
        
        for col in entity_cols:
            print(f"Unique values in '{col}':")
            print(df[col].unique())
            print("-" * 20)
            
    except Exception as e:
        print(f"Error reading {file}: {e}")
