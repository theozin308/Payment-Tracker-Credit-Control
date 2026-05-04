import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="FCC Mandalay Payment Tracker", layout="wide")

# --- CSS TO HIDE THE SELECTION COLUMN & STYLE ---
st.markdown("""
    <style>
    [data-testid="stMain"] [data-testid="stDataFrameDataLayer"] > div:first-child {
        display: none !important;
    }
    .stButton > button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- SESSION STATE INITIALIZATION ---
if "selected_unit" not in st.session_state:
    st.session_state.selected_unit = "-- Select --"
if "due_filter" not in st.session_state:
    st.session_state.due_filter = "All"

@st.cache_data(ttl=60) 
def get_live_data():
    df = pd.read_csv(SHEET_URL, dtype=str)
    df.columns = df.columns.str.strip() 
    
    # --- FIX: HIDE "NONE" ROWS ---
    # Drop rows where 'Plot No.' is NaN or the string "None" or "nan"
    df = df[df['Plot No.'].notna()]
    df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', ''])]
    
    # Helper: Convert 'Months Overdue' to numeric for filtering
    df['overdue_val'] = pd.to_numeric(df['Months Overdue'].str.extract('(\d+)')[0], errors='coerce').fillna(0)
    return df

try:
    df = get_live_data()
    st.title("Fortune Commercial City Payment Tracker")
    st.divider()

    # --- SELECTION AREA ---
    col_a, col_b = st.columns(2)

    with col_a:
        sales_people = df['Sales Person'].dropna().unique()
        selected_sales = st.selectbox("👤 Filter by Sales Person", options=["-- All Sales --"] + list(sales_people))

    filtered_df = df.copy()
    if selected_sales != "-- All Sales --":
        filtered_df = df[df['Sales Person'] == selected_sales]

    # --- QUICK FILTERS ---
    st.write("### Quick Filters")
    c1, c2, c3 = st.columns(3)
    
    if c1.button("📑 Show All Units", type="secondary" if st.session_state.due_filter != "All" else "primary"):
        st.session_state.due_filter = "All"
        st.rerun()
    
    if c2.button("🚨 1+ Month Overdue", type="primary" if st.session_state.due_filter == "Overdue" else "secondary"):
        st.session_state.due_filter = "Overdue"
        st.rerun()

     if c3.button("🗓️ Current Month Due", type="primary" if st.session_state.due_filter == "Current" else "secondary"):
        st.session_state.due_filter = "Current"
        st.rerun()

    # --- DYNAMIC COLUMN LOGIC ---
    base_cols = ['Plot No.', 'Sales Person', 'Customer Name', 'Total Amount to Collect', 'Status', 'Months Overdue']

    if st.session_state.due_filter == "Current":
        filtered_df = filtered_df[filtered_df['overdue_val'] == 0]
        display_cols = base_cols
    elif st.session_state.due_filter == "Overdue":
        filtered_df = filtered_df[filtered_df['overdue_val'] >= 1]
        display_cols = ['Plot No.', 'Sales Person', 'Customer Name', 'Past Due Amount', 'Total Amount to Collect', 'Status', 'Months Overdue']
    else:
        display_cols = base_cols

    with col_b:
        unit_list = filtered_df['Plot No.'].dropna().unique()
        current_index = 0
        if st.session_state.selected_unit in unit_list:
            current_index = list(unit_list).index(st.session_state.selected_unit) + 1
        
        selected_unit_box = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list), index=current_index)
        
        if selected_unit_box != st.session_state.selected_unit:
            st.session_state.selected_unit = selected_unit_box
            st.rerun()

    # --- DASHBOARD TABLE VIEW ---
    if st.session_state.selected_unit == "-- Select --":
        st.subheader(f"Results: {st.session_state.due_filter} ({len(filtered_df)} Units)")
        
        summary_cols = [c for c in display_cols if c in filtered_df.columns]
        summary_table = filtered_df[summary_cols]
        
        event = st.dataframe(
            summary_table, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",  
            selection_mode="single-row"
        )

        if len(event.selection.rows) > 0:
            row_idx = event.selection.rows[0]
            st.session_state.selected_unit = summary_table.iloc[row_idx]['Plot No.']
            st.rerun()

    # --- DETAIL VIEW ---
    else:
        unit_data = df[df['Plot No.'] == st.session_state.selected_unit].iloc[0]
        st.divider()
        if st.button("⬅️ Back to List"):
            st.session_state.selected_unit = "-- Select --"
            st.rerun()
            
        st.header(f"Unit Detail: {st.session_state.selected_unit}")
        st.table(unit_data.to_frame(name="Value"))

except Exception as e:
    st.error(f"Error: {e}")
