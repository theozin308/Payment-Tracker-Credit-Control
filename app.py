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
# Defaulting the filter to "Overdue" so it loads first
if "selected_unit" not in st.session_state:
    st.session_state.selected_unit = "-- Select --"
if "due_filter" not in st.session_state:
    st.session_state.due_filter = "Overdue" 

@st.cache_data(ttl=60) 
def get_live_data():
    df = pd.read_csv(SHEET_URL, dtype=str)
    df.columns = df.columns.str.strip() 
    
    # Cleaning: Remove empty/None rows
    df = df[df['Plot No.'].notna()]
    df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', '', 'null'])]
    
    # Convert 'Months Overdue' to numeric for sorting
    df['overdue_val'] = pd.to_numeric(df['Months Overdue'].str.extract('(\d+)')[0], errors='coerce').fillna(0)
    
    # Global Sort: Highest Overdue at the top
    df = df.sort_values(by='overdue_val', ascending=False)
    return df

try:
    df = get_live_data()
    st.title("🏙️ Fortune Commercial City Payment Tracker")
    st.divider()

    # --- ROW 1: PRIMARY FILTERS ---
    col_a, col_b = st.columns(2)

    with col_a:
        sales_people = sorted(df['Sales Person'].dropna().unique())
        selected_sales = st.selectbox("👤 Filter by Sales Person", options=["-- All Sales --"] + list(sales_people))

    filtered_df = df.copy()
    if selected_sales != "-- All Sales --":
        filtered_df = df[df['Sales Person'] == selected_sales]

    with col_b:
        unit_list = filtered_df['Plot No.'].unique()
        curr_idx = 0
        if st.session_state.selected_unit in unit_list:
            curr_idx = list(unit_list).index(st.session_state.selected_unit) + 1
            
        selected_unit_box = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list), index=curr_idx)
        if selected_unit_box != st.session_state.selected_unit:
            st.session_state.selected_unit = selected_unit_box
            st.rerun()

    # --- ROW 2: BUTTON LAYOUT (REORDERED) ---
    st.markdown("### 🔍 Quick Filters")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
    
    with c1:
        if st.button("📑 All Units", type="primary" if st.session_state.due_filter == "All" else "secondary"):
            st.session_state.due_filter = "All"
            st.rerun()
    
    with c2:
        if st.button("🚨 1+ Month Overdue", type="primary" if st.session_state.due_filter == "Overdue" else "secondary"):
            st.session_state.due_filter = "Overdue"
            st.rerun()
        
    with c3:
        if st.button("🗓️ Current Month Due", type="primary" if st.session_state.due_filter == "Current" else "secondary"):
            st.session_state.due_filter = "Current"
            st.rerun()

    # --- FILTER LOGIC ---
    base_cols = ['Plot No.', 'Sales Person', 'Customer Name', 'Total Amount to Collect', 'Status', 'Months Overdue']
    
    if st.session_state.due_filter == "Current":
        filtered_df = filtered_df[filtered_df['overdue_val'] == 0]
        display_cols = base_cols
    elif st.session_state.due_filter == "Overdue":
        filtered_df = filtered_df[filtered_df['overdue_val'] >= 1]
        # Include Past Due Amount for the overdue view
        display_cols = ['Plot No.', 'Sales Person', 'Customer Name', 'Past Due Amount', 'Total Amount to Collect', 'Status', 'Months Overdue']
    else:
        display_cols = base_cols

    # --- DASHBOARD VIEW ---
    if st.session_state.selected_unit == "-- Select --":
        st.subheader(f"Dashboard: {st.session_state.due_filter} ({len(filtered_df)} Units)")
        
        summary_cols = [c for c in display_cols if c in filtered_df.columns]
        
        event = st.dataframe(
            filtered_df[summary_cols], 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",  
            selection_mode="single-row"
        )

        if len(event.selection.rows) > 0:
            row_idx = event.selection.rows[0]
            st.session_state.selected_unit = filtered_df.iloc[row_idx]['Plot No.']
            st.rerun()

    else:
        # DETAIL VIEW
        unit_data = df[df['Plot No.'] == st.session_state.selected_unit].iloc[0]
        st.divider()
        if st.button("⬅️ Back to Table List"):
            st.session_state.selected_unit = "-- Select --"
            st.rerun()
            
        st.header(f"Details: {st.session_state.selected_unit}")
        st.table(unit_data.to_frame(name="Information"))

except Exception as e:
    st.error(f"Application Error: {e}")
