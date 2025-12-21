import pandas as pd
from pathlib import Path
import warnings

# ---------- CONFIG ----------
DATA_DIR = Path(__file__).resolve().parent
RAW_FILES = [("MEPL.xlsx", "MEPL"), ("MLPL.xlsx", "MLPL"), ("mmw.xlsx", "MMW"), ("mmpl.xlsx", "MMPL")]

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Vectorized, robust column normalizer."""
    if df is None or df.empty:
        return df
    cols = list(df.columns)
    new = []
    for c in cols:
        s = str(c).strip()
        s = s.replace(chr(160), " ")
        s = s.replace(chr(92), "_").replace('/', '_')
        s = '_'.join(s.split())
        s = s.lower()
        s = ''.join(ch if (ch.isalnum() or ch == '_') else '_' for ch in s)
        s = '_'.join([p for p in s.split('_') if p != ''])
        new.append(s)
    df.columns = new
    return df

def _resolve_path(fn: str) -> Path:
    """Resolve file path case-insensitively."""
    # Check exact match first
    path = DATA_DIR / fn
    if path.exists():
        return path
    
    # Case-insensitive check
    for p in DATA_DIR.iterdir():
        if p.name.lower() == fn.lower():
            return p
            
    return path

def find_header_row(path: Path) -> int:
    """Detects header row by scanning for known keywords."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Peek first 10 rows
            df_peek = pd.read_excel(path, header=None, nrows=10)
    except Exception:
        return 1 # Fallback default

    # Typical columns we expect (normalized or raw)
    keywords = {"pr number", "pr_number", "po number", "net amount", "vendor", "pr date", "po date", "item code"}
    
    for idx, row in df_peek.iterrows():
        # Join row values to string
        row_str = " ".join([str(x).lower() for x in row if pd.notna(x)])
        
        # Check for at least 2 keywords match to be confident
        matches = 0
        for k in keywords:
            if k in row_str:
                matches += 1
        
        if matches >= 2:
            return idx
            
    return 1  # Default to skipping 1 row (row 1 is header) if detection fails

def _read_excel(path: Path, entity: str) -> pd.DataFrame:
    # Auto-detect header row instead of hardcoding skiprows=1
    header_idx = find_header_row(path)
    
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Try openpyxl first
            df = pd.read_excel(path, header=header_idx, engine='openpyxl')
    except Exception as e:
        print(f"Error reading {path} with openpyxl, trying default: {e}")
        # Fallback to default engine (supports xls via xlrd if installed)
        df = pd.read_excel(path, header=header_idx)

    # Normalize columns immediately to ensure alignment during concat
    df = normalize_columns(df)
    df['entity_source_file'] = entity
    return df

def _finalize_frames(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame()
    # Frames are already normalized individually, so keys should align better
    x = pd.concat(frames, ignore_index=True)
    # parse common date columns once
    for c in ['pr_date_submitted', 'po_create_date', 'po_delivery_date', 'po_approved_date']:
        if c in x.columns:
            x[c] = pd.to_datetime(x[c], errors='coerce')
    return x

def convert_all_to_parquet(file_list=None):
    if file_list is None:
        file_list = RAW_FILES
    frames = []
    for fn, ent in file_list:
        path = _resolve_path(fn)
        if not path.exists():
            print(f"File not found: {path}")
            continue
        try:
            frames.append(_read_excel(path, ent))
        except Exception as exc:
            print(f"Failed to read {path.name}: {exc}")
    
    df = _finalize_frames(frames)
    
    # Ensure all object columns are converted to strings to avoid Parquet errors
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str)

    # Save as a single parquet file
    output_path = DATA_DIR / "p2p_data.parquet"
    df.to_parquet(output_path)
    print(f"Successfully converted all Excel files to {output_path}")

if __name__ == "__main__":
    convert_all_to_parquet()
