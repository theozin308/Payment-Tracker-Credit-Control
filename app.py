import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="FCC Mandalay Payment Tracker", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
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
    div[data-testid="stDataFrame"] iframe {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- SESSION STATE INITIALIZATION ---
if "selected_unit" not in st.session_state:
    st.session_state.selected_unit = "-- Select --"

if "due_filter" not in st.session_state:
    st.session_state.due_filter = "All" 

# --- READ QUERY PARAMETERS FOR NEW TAB LINKS ---
# If a user clicks a Plot No. hyperlink, it opens a new tab with ?unit=XYZ in the URL
query_params = st.query_params
if "unit" in query_params:
    st.session_state.selected_unit = query_params["unit"]

# --- DATA CACHING & FETCHING ---
@st.cache_data(ttl=300) 
def download_raw_sheet():
    return pd.read_csv(SHEET_URL, dtype=str)

def get_live_data():
    df = download_raw_sheet().copy()  
    df.columns = df.columns.str.strip() 
    
    # Clean empty data rows
    df = df[df['Plot No.'].notna()]
    df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', '', 'null'])]
    df = df.sort_values(by='Plot No.')
    
    # Numeric conversions for currency fields
    cols_to_fix = [
        'Amount to Collect for This Month', 
        'Past Due Amount', 
        'Total Amount to Collect This Month',
        'Total Paid',
        'Plot Price',
        'Remaining Balance',
        'Partial (or) Full Payment for Current Month'
    ]
    for col in cols_to_fix:
        if col in df.columns:
            shorthand_num = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
            df[col] = shorthand_num * 100000

    # Overdue extraction logic
    raw_digits = pd.to_numeric(df['Months Overdue'].str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
    is_advance = df['Months Overdue'].str.lower().str.contains('advance|paid', na=False)
    df['overdue_val'] = raw_digits.mask(is_advance, -1 * raw_digits)
    
    return df

# --- MAIN APP ---
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
        
        # Keep dropdown select perfectly synced with current view pane
        curr_idx = 0
        if st.session_state.selected_unit in unit_list:
            curr_idx = list(unit_list).index(st.session_state.selected_unit) + 1
            
        selected_unit_box = st.selectbox("🎯 Choose Unit to View Details Instantly", options=["-- Select --"] + list(unit_list), index=curr_idx)
        if selected_unit_box != st.session_state.selected_unit:
            st.session_state.selected_unit = selected_unit_box
            # If changing via dropdown, clear out any old query string parameter safely
            if "unit" in st.query_params:
                st.query_params.clear()
            st.rerun()

    # --- DASHBOARD VIEW LAYER ---
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

        # --- DATA FILTERING LOGIC ---
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
        
        rendered_df = display_df.copy().reset_index(drop=True)
        
        # 💡 SOLUTION: Convert Plot No. text column into an internal application hyperlink query string string
        # This creates links like: http://localhost:8501/?unit=A-102
        rendered_df['Plot Link'] = "/?unit=" + rendered_df['Plot No.'].astype(str)
        
        base_cols = [
            'Plot Link', # Use the Link column here instead of original static column
            'Sales Person', 
            'Customer Name', 
            'Total Amount to Collect This Month', 
            'Total Paid',
            'Partial (or) Full Payment for Current
