import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Procurement & Vendor Spend Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        text-align: center;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_data():
    try:
        # Load Vendors
        if os.path.exists("vendors.csv"):
            vendors = pd.read_csv("vendors.csv")
            # Ensure string columns
            for col in vendors.columns:
                 if vendors[col].dtype == 'object':
                     vendors[col] = vendors[col].astype(str).str.strip()
        else:
            vendors = pd.DataFrame()

        # Load Reports
        if os.path.exists("reports.csv"):
            reports = pd.read_csv("reports.csv")
            
            # Numeric Cleaning
            numeric_cols = ['Net Amount', 'PR Value', 'PO Quantity', 'Unit Rate']
            for col in numeric_cols:
                if col in reports.columns:
                    reports[col] = pd.to_numeric(reports[col], errors='coerce').fillna(0)
            
            # String Cleaning
            string_cols = ['Buying legal entity', 'PO Vendor', 'Procurement Category', 'Buyer Group', 'Version', 'PR Number', 'Purchase Doc']
            for col in string_cols:
                if col in reports.columns:
                    reports[col] = reports[col].astype(str).str.strip()
            
            # Date Parsing
            reports['PO Date'] = pd.to_datetime(reports['Po create Date'], errors='coerce')
            reports['PR Date'] = pd.to_datetime(reports['PR Date Submitted'], errors='coerce')
            
        else:
            reports = pd.DataFrame()
            
        return vendors, reports

    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame()

vendors_df, reports_df = load_data()

# --- Helper Functions ---
def format_currency(val):
    return f"₹{val:,.2f}"

# --- Main App Logic ---
if reports_df.empty:
    st.warning("No report data found. Please run the data processing script first.")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.title("Filters")

# 1. Entity Filter
all_entities = sorted(reports_df['Buying legal entity'].unique())
selected_entities = st.sidebar.multiselect("Select Legal Entity", all_entities, default=all_entities)

# 2. Date Filter
min_date = reports_df['PO Date'].min()
max_date = reports_df['PO Date'].max()

start_date, end_date = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# 3. Category Filter
all_categories = sorted(reports_df['Procurement Category'].unique())
selected_categories = st.sidebar.multiselect("Procurement Category", all_categories, default=all_categories)

# --- Apply Filters ---
mask = (
    reports_df['Buying legal entity'].isin(selected_entities) &
    (reports_df['PO Date'].dt.date >= start_date) &
    (reports_df['PO Date'].dt.date <= end_date) &
    reports_df['Procurement Category'].isin(selected_categories)
)
filtered_df = reports_df.loc[mask]

# --- Dashboard Header ---
st.title("📊 Procurement Overview Dashboard")
st.markdown("---")

# --- KPI Metrics ---
col1, col2, col3, col4 = st.columns(4)

total_spend = filtered_df['Net Amount'].sum()
total_pos = filtered_df['Purchase Doc'].nunique()
unique_vendors = filtered_df['PO Vendor'].nunique()
avg_po_size = total_spend / total_pos if total_pos > 0 else 0

with col1:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Total Spend</div><div class="metric-value">{format_currency(total_spend)}</div></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Total Purchase Orders</div><div class="metric-value">{total_pos}</div></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Active Vendors</div><div class="metric-value">{unique_vendors}</div></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Avg PO Value</div><div class="metric-value">{format_currency(avg_po_size)}</div></div>""", unsafe_allow_html=True)

st.markdown("---")

# --- Charts Section 1: Entity & Time Analysis ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("Spend by Legal Entity")
    entity_spend = filtered_df.groupby('Buying legal entity')['Net Amount'].sum().reset_index()
    fig_entity = px.bar(entity_spend, x='Buying legal entity', y='Net Amount', text_auto='.2s', color='Buying legal entity')
    fig_entity.update_layout(showlegend=False)
    st.plotly_chart(fig_entity, use_container_width=True)

with c2:
    st.subheader("Monthly Spend Trend")
    if 'PO Date' in filtered_df:
        monthly_spend = filtered_df.groupby(pd.Grouper(key='PO Date', freq='M'))['Net Amount'].sum().reset_index()
        fig_trend = px.line(monthly_spend, x='PO Date', y='Net Amount', markers=True)
        st.plotly_chart(fig_trend, use_container_width=True)

# --- Charts Section 2: Category & Vendor Analysis ---
c3, c4 = st.columns(2)

with c3:
    st.subheader("Spend by Procurement Category")
    cat_spend = filtered_df.groupby('Procurement Category')['Net Amount'].sum().reset_index()
    fig_cat = px.treemap(cat_spend, path=['Procurement Category'], values='Net Amount')
    st.plotly_chart(fig_cat, use_container_width=True)

with c4:
    st.subheader("Top 10 Vendors by Spend")
    vendor_spend = filtered_df.groupby('PO Vendor')['Net Amount'].sum().sort_values(ascending=False).head(10).reset_index()
    fig_top_vendors = px.bar(vendor_spend, y='PO Vendor', x='Net Amount', orientation='h', text_auto='.2s', color='Net Amount')
    fig_top_vendors.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top_vendors, use_container_width=True)

# --- Detailed Analysis Tabs ---
st.markdown("---")
st.header("Deep Dive Analysis")

tab_vendor, tab_data = st.tabs(["Vendor Details", "Raw Data Explorer"])

with tab_vendor:
    col_v1, col_v2 = st.columns([1, 2])
    
    with col_v1:
        st.subheader("Select Vendor")
        # Get list of vendors present in the filtered reports
        available_vendors = sorted(filtered_df['PO Vendor'].unique())
        selected_vendor_name = st.selectbox("Choose a Vendor", available_vendors)
        
    if selected_vendor_name:
        with col_v2:
            st.subheader(f"Profile: {selected_vendor_name}")
            
            # --- Vendor Master Info ---
            if not vendors_df.empty:
                # Fuzzy/Normalized Matching
                clean_target = selected_vendor_name.upper()
                # Create temp column for matching
                vendors_df['MatchName'] = vendors_df['Vendor Name'].str.upper()
                
                # Check for direct match
                match = vendors_df[vendors_df['MatchName'] == clean_target]
                
                if not match.empty:
                    info = match.iloc[0]
                    st.info(f"""
                    **Vendor Account:** {info.get('Vendor Account', 'N/A')}  
                    **Phone:** {info.get('Telephone', 'N/A')}  
                    **Email:** {info.get('Email', 'N/A')}  
                    **Address:** {info.get('Address', 'N/A')}
                    """)
                else:
                    st.warning("Vendor contact details not found in Master Record.")
            
        # --- Vendor Stats ---
        v_df = filtered_df[filtered_df['PO Vendor'] == selected_vendor_name]
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Vendor Total Spend", format_currency(v_df['Net Amount'].sum()))
        m2.metric("PO Count", v_df['Purchase Doc'].nunique())
        m3.metric("Avg Ticket Size", format_currency(v_df['Net Amount'].mean()))
        
        st.subheader("Transaction History")
        display_cols = ['PO Date', 'Purchase Doc', 'Item Description', 'PO Quantity', 'Unit Rate', 'Net Amount', 'PO Status', 'Buying legal entity']
        # Filter columns that actually exist
        cols_to_show = [c for c in display_cols if c in v_df.columns]
        st.dataframe(v_df[cols_to_show].sort_values('PO Date', ascending=False), use_container_width=True)

with tab_data:
    st.subheader("Filtered Data Export")
    st.dataframe(filtered_df)
