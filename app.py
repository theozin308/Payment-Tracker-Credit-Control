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
    
    # Safe handling/standardization for the new Plan column
    if 'Plan' in df.columns:
        df['Plan'] = df['Plan'].fillna('-').str.strip()
    else:
        df['Plan'] = '-'
    
    # Numeric Conversion for Health Metrics & Table Columns
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
            # Parse out raw text/commas from sheet
            shorthand_num = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
            # Conversion: Shorthand lakhs to full numerical value
            df[col] = shorthand_num * 100000

    # --- OVERDUE EXTRACTION ---
    raw_digits = pd.to_numeric(df['Months Overdue'].str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
    is_advance = df['Months Overdue'].str.lower().str.contains('advance|paid', na=False)
    df['overdue_val'] = raw_digits.mask(is_advance, -1 * raw_digits)
    
    return df

try:
    df = get_live_data()
    
    # --- GET URL PARAMS FOR ROUTING ---
    url
