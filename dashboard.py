import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Vendor Spend Dashboard", layout="wide")

@st.cache_data
def load_data():
    try:
        vendors = pd.read_csv("vendors.csv")
        reports = pd.read_csv("reports.csv")
        
        # Clean numeric columns in reports
        reports['Net Amount'] = pd.to_numeric(reports['Net Amount'], errors='coerce').fillna(0)
        reports['PO Quantity'] = pd.to_numeric(reports['PO Quantity'], errors='coerce').fillna(0)
        
        # Clean mixed type columns to avoid PyArrow errors
        for col in reports.columns:
            if reports[col].dtype == 'object':
                 reports[col] = reports[col].astype(str)

        # Parse Dates (after converting to string, need to handle 'nan')
        reports['PO create Date'] = pd.to_datetime(reports['Po create Date'], errors='coerce')
        reports['PR Date Submitted'] = pd.to_datetime(reports['PR Date Submitted'], errors='coerce')
        
        return vendors, reports
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()

vendors, reports = load_data()

st.title("Vendor Spend Dashboard")

if reports.empty:
    st.error("No data found. Please ensure 'reports.csv' and 'vendors.csv' exist.")
else:
    # --- Sidebar Filters ---
    st.sidebar.header("Filters")
    
    # Date Range
    min_date = reports['PO create Date'].min()
    max_date = reports['PO create Date'].max()
    
    if pd.notnull(min_date) and pd.notnull(max_date):
        date_range = st.sidebar.date_input(
            "Select PO Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
    else:
        date_range = []

    # Filter Data based on Date
    filtered_reports = reports.copy()
    if len(date_range) == 2:
        start_date, end_date = date_range
        mask = (filtered_reports['PO create Date'].dt.date >= start_date) & (filtered_reports['PO create Date'].dt.date <= end_date)
        filtered_reports = filtered_reports.loc[mask]

    # --- KPI Row ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_spend = filtered_reports['Net Amount'].sum()
    total_pos = filtered_reports['Purchase Doc'].nunique()
    total_vendors = filtered_reports['PO Vendor'].nunique()
    avg_po_value = total_spend / total_pos if total_pos > 0 else 0

    col1.metric("Total Spend", f"₹{total_spend:,.2f}")
    col2.metric("Total POs", f"{total_pos}")
    col3.metric("Active Vendors", f"{total_vendors}")
    col4.metric("Avg PO Value", f"₹{avg_po_value:,.2f}")

    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs(["Overview", "Vendor Analysis", "Data View"])

    with tab1:
        st.subheader("Spend Over Time")
        # Aggregate by Month
        if not filtered_reports.empty and 'PO create Date' in filtered_reports:
             spend_over_time = filtered_reports.groupby(filtered_reports['PO create Date'].dt.to_period("M"))['Net Amount'].sum().reset_index()
             spend_over_time['PO create Date'] = spend_over_time['PO create Date'].astype(str)
             
             fig_time = px.line(spend_over_time, x='PO create Date', y='Net Amount', markers=True, title="Monthly Spend Trend")
             st.plotly_chart(fig_time, use_container_width=True)
        
        col_cat1, col_cat2 = st.columns(2)
        
        with col_cat1:
            st.subheader("Spend by Procurement Category")
            if 'Procurement Category' in filtered_reports:
                cat_spend = filtered_reports.groupby('Procurement Category')['Net Amount'].sum().reset_index()
                fig_cat = px.pie(cat_spend, values='Net Amount', names='Procurement Category', title="Spend Distribution by Category")
                st.plotly_chart(fig_cat, use_container_width=True)
        
        with col_cat2:
             st.subheader("Spend by Buyer Group")
             if 'Buyer Group' in filtered_reports:
                 buyer_spend = filtered_reports.groupby('Buyer Group')['Net Amount'].sum().reset_index()
                 fig_buyer = px.bar(buyer_spend, x='Buyer Group', y='Net Amount', title="Spend by Buyer Group")
                 st.plotly_chart(fig_buyer, use_container_width=True)

    with tab2:
        st.subheader("Top Vendors by Spend")
        
        top_n = st.slider("Select Top N Vendors", 5, 50, 10)
        
        vendor_spend = filtered_reports.groupby('PO Vendor')['Net Amount'].sum().sort_values(ascending=False).reset_index()
        
        fig_vendor = px.bar(vendor_spend.head(top_n), x='Net Amount', y='PO Vendor', orientation='h', title=f"Top {top_n} Vendors by Spend")
        fig_vendor.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_vendor, use_container_width=True)
        
        st.subheader("Vendor Details Lookup")
        selected_vendor = st.selectbox("Select Vendor to View Details", options=sorted(filtered_reports['PO Vendor'].dropna().unique()))
        
        if selected_vendor:
            # Filter reports for this vendor
            vendor_txns = filtered_reports[filtered_reports['PO Vendor'] == selected_vendor]
            st.write(f"**Total Spend:** ₹{vendor_txns['Net Amount'].sum():,.2f}")
            st.write(f"**Total Transactions:** {len(vendor_txns)}")
            
            # Try to find contact details in vendors df
            if not vendors.empty:
                 # Clean names for matching
                 clean_name = str(selected_vendor).strip().upper()
                 # Ensure vendors columns are string
                 vendors['Vendor Name Clean'] = vendors['Vendor Name'].astype(str).str.strip().str.upper()
                 
                 matched_info = vendors[vendors['Vendor Name Clean'] == clean_name]
                 
                 if not matched_info.empty:
                     st.write("### Contact Information (from Vendor Master)")
                     info = matched_info.iloc[0]
                     st.write(f"**Address:** {info.get('Address', 'N/A')}")
                     st.write(f"**Email:** {info.get('Email', 'N/A')}")
                     st.write(f"**Telephone:** {info.get('Telephone', 'N/A')}")
                 else:
                     st.info("No contact details found in Vendor Master list.")

    with tab3:
        st.subheader("Raw Data")
        st.dataframe(filtered_reports)
