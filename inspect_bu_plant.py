import pandas as pd

files = ["MEPL.xlsx", "MLPL.xlsx"]

for file in files:
    print(f"--- Inspecting {file} ---")
    try:
        df = pd.read_excel(file, skiprows=1)
        
        cols_to_check = ['PR Bussiness Unit', 'PO Business Unit', 'Plant']
        for col in cols_to_check:
            if col in df.columns:
                print(f"Unique values in '{col}':")
                print(df[col].unique())
            else:
                print(f"Column '{col}' not found.")
            print("-" * 20)
            
    except Exception as e:
        print(f"Error reading {file}: {e}")
