import pandas as pd
import os
import glob
import re

def parse_vendor_files(vendor_files):
    all_vendors = []
    
    for file_path in vendor_files:
        print(f"Processing vendor file: {file_path}")
        try:
            # Read the entire file without header
            df = pd.read_excel(file_path, header=None)
            
            # Pre-calculate company name
            company_name = None
            for i in range(min(10, len(df))):
                val = df.iloc[i, 0]
                if isinstance(val, str) and "PRIVATE LIMITED" in val:
                    company_name = val
                    break
            
            # State tracking
            current_vendor = {}
            
            # Iterate through all rows
            for idx, row in df.iterrows():
                # Convert first column to string and strip
                col0 = str(row[0]).strip() if pd.notna(row[0]) else ""
                
                if col0 == 'Vendor account':
                    # If we have a current vendor, save it
                    if current_vendor:
                        current_vendor['Source Company'] = company_name
                        current_vendor['Source File'] = os.path.basename(file_path)
                        all_vendors.append(current_vendor)
                    
                    # Start new vendor
                    current_vendor = {}
                    # Value is at index 2 based on debug
                    if len(row) > 2:
                        current_vendor['Vendor Account'] = row[2]
                        
                elif current_vendor:
                    # We are inside a vendor block
                    if col0 == 'Address':
                        if len(row) > 2:
                            current_vendor['Address'] = row[2]
                        
                        # Vendor Name is on the same row, label at index 6, value at index 9
                        if len(row) > 9:
                             # Check if col 6 says 'Vendor name'
                             col6 = str(row[6]).strip() if pd.notna(row[6]) else ""
                             if col6 == 'Vendor name':
                                 current_vendor['Vendor Name'] = row[9]
                                
                    elif col0 == 'Telephone':
                        if len(row) > 2:
                            current_vendor['Telephone'] = row[2]
                            
                    elif col0 == 'Email':
                        if len(row) > 2:
                            current_vendor['Email'] = row[2]
                            
                    elif col0 == 'Buyer group':
                        if len(row) > 2:
                            current_vendor['Buyer Group'] = row[2]

            # Save the last vendor
            if current_vendor:
                current_vendor['Source Company'] = company_name
                current_vendor['Source File'] = os.path.basename(file_path)
                all_vendors.append(current_vendor)
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()
            
    return pd.DataFrame(all_vendors)

def parse_report_files(report_files):
    all_reports = []
    
    for file_path in report_files:
        print(f"Processing report file: {file_path}")
        try:
            # Read with header=1 as discovered
            df = pd.read_excel(file_path, header=1)
            df['Source File'] = os.path.basename(file_path)
            all_reports.append(df)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    if all_reports:
        return pd.concat(all_reports, ignore_index=True)
    else:
        return pd.DataFrame()

def main():
    base_path = "/tmp/file_attachments"
    archive_6_path = os.path.join(base_path, "Archive 6")
    archive_7_path = os.path.join(base_path, "Archive 7")
    
    report_files = glob.glob(os.path.join(archive_6_path, "*.xlsx"))
    vendor_files = glob.glob(os.path.join(archive_7_path, "*.xlsx"))
    
    # Process Vendors
    print("Processing vendors...")
    vendors_df = parse_vendor_files(vendor_files)
    print(f"Extracted {len(vendors_df)} vendors.")
    vendors_df.to_csv("vendors.csv", index=False)
    print("Saved to vendors.csv")
    
    # Process Reports
    print("Processing reports...")
    reports_df = parse_report_files(report_files)
    print(f"Extracted {len(reports_df)} report rows.")
    reports_df.to_csv("reports.csv", index=False)
    print("Saved to reports.csv")

if __name__ == "__main__":
    main()
