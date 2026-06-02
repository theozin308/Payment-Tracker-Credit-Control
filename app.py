import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="FCC Mandalay Payment Tracker", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
    [data-testid="stMain"] [data-testid="stDataFrameDataLayer"] > div:first-child {
        display: none !important;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- SESSION STATE ---
if "selected_unit" not in st.session_state:
    st.session_state.selected_unit = "-- Select --"

if "due_filter" not in st.session_state:
    st.session_state.due_filter = "All" 

# --- OPTIMIZED CACHING LAYER ---
@st.cache_data(ttl=300) 
def download_raw_sheet():
    return pd.read_csv(SHEET_URL, dtype=str)

def get_live_data():
    df = download_raw_sheet().copy()  
    df.columns = df.columns.str.strip() 
    
    # Cleaning: Remove empty/None rows
    df = df[df['Plot No.'].notna()]
    df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', '', 'null'])]
    
    # Global Sort by Plot No.
    df = df.sort_values(by='Plot No.')
    
    # Numeric Conversion for Health Metrics & Remaining Table Columns
    cols_to_fix = [
        'Amount to Collect for This Month', 
        'Past Due Amount', 
        'Total Amount to Collect',
        'Total Paid',
        'Plot Price',
        'Remaining Balance'
    ]
    for col in cols_to_fix:
        if col in df.columns:
            # Parse out raw text/commas from sheet
            shorthand_num = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
            # Conversion: Shorthand lakhs to full numerical value
            df[col] = shorthand_num * 100000

    # --- FIXED OVERDUE EXTRACTION ---
    # First, parse out the raw number digits
    raw_digits = pd.to_numeric(df['Months Overdue'].str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
    
    # If the text explicitly contains "advance", treat it as a negative value so it fails the '>= 1' overdue filter
    is_advance = df['Months Overdue'].str.lower().str.contains('advance|paid', na=False)
    df['overdue_val'] = raw_digits.mask(is_advance, -1 * raw_digits)
    
    return df

try:
    df = get_live_data()
    st.title("Fortune Commercial City Payment Tracker")
    st.divider()

    # --- ROW 1: PRIMARY FILTERS ---
    col_a, col_b = st.columns(2)

    with col_a:
        sales_people = sorted(df['Sales Person'].dropna().unique())
        selected_sales = st.selectbox("👤 Filter by Sales Person", options=["-- All Sales --"] + list(sales_people))

    # Apply Sales Person Filter to a Master Base DataFrame
    base_filtered_df = df.copy()
    if selected_sales != "-- All Sales --":
        base_filtered_df = df[df['Sales Person'] == selected_sales]

    with col_b:
        unit_list = base_filtered_df['Plot No.'].unique()
        curr_idx = 0
        if st.session_state.selected_unit in unit_list:
            curr_idx = list(unit_list).index(st.session_state.selected_unit) + 1
            
        selected_unit_box = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list), index=curr_idx)
        if selected_unit_box != st.session_state.selected_unit:
            st.session_state.selected_unit = selected_unit_box
            st.rerun()

    # --- DASHBOARD VIEW ---
    if st.session_state.selected_unit == "-- Select --":
        # QUICK FILTERS
        st.markdown("### Quick Filters")
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            if st.button("📑 All Units", type="primary" if st.session_state.due_filter == "All" else "secondary"):
                st.session_state.due_filter = "All"
                st.rerun()
        with c2:
            if st.button("🗓️ Current Month Due", type="primary" if st.session_state.due_filter == "Current" else "secondary"):
                st.session_state.due_filter = "Current"
                st.rerun()
        with c3:
            if st.button("🚨 1+ Month Overdue", type="primary" if st.session_state.due_filter == "Overdue" else "secondary"):
                st.session_state.due_filter = "Overdue"
                st.rerun()
        with c4:
            if st.button("✅ Completed / Advance", type="primary" if st.session_state.due_filter == "Completed" else "secondary"):
                st.session_state.due_filter = "Completed"
                st.rerun()

        # --- FILTER LOGIC ---
        is_completed_or_advance = (
            base_filtered_df['Status'].str.lower().str.contains('complete|advance|done', na=False) |
            base_filtered_df['Months Overdue'].str.lower().str.contains('advance', na=False)
        )

        if st.session_state.due_filter == "Current":
            display_df = base_filtered_df[(base_filtered_df['overdue_val'] == 0) & (~is_completed_or_advance)]
        elif st.session_state.due_filter == "Overdue":
            display_df = base_filtered_df[(base_filtered_df['overdue_val'] >= 1) & (~is_completed_or_advance)]
        elif st.session_state.due_filter == "Completed":
            display_df = base_filtered_df[is_completed_or_advance]
        else:
            display_df = base_filtered_df

        st.subheader(f"Table View: {st.session_state.due_filter} ({len(display_df)} Units)")
        
        base_cols = ['Plot No.', 'Sales Person', 'Customer Name', 'Total Amount to Collect', 'Status', 'Months Overdue']
        
        # Table view execution with thousands separators configurator active
        event = st.dataframe(
            display_df[base_cols], 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",  
            selection_mode="single-row",
            column_config={
                "Total Amount to Collect": st.column_config.NumberColumn("Total Amount to Collect (MMK)", format="%,d")
            }
        )
