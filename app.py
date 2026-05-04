import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="FCC Mandalay Payment Tracker", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
    /* Hide the default selection checkbox column */
    [data-testid="stMain"] [data-testid="stDataFrameDataLayer"] > div:first-child {
        display: none !important;
    }
    /* Make buttons uniform */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# The Live Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- SESSION STATE ---
if "selected_unit" not in st.session_state:
    st.session_state.selected_unit = "-- Select --"
if "due_filter" not in st.session_state:
    st.session_state.due_filter = "All"

# --- DATA LOADING & CLEANING ---
@st.cache_data(ttl=60) 
def get_live_data():
    df = pd.read_csv(SHEET_URL, dtype=str)
    df.columns = df.columns.str.strip() 
    
    # 1. Hide "None" or empty rows by ensuring Plot No exists
    df = df[df['Plot No.'].notna()]
    df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', '', 'null'])]
    
    # 2. Extract numeric overdue value for filtering
    df['overdue_val'] = pd.to_numeric(
        df['Months Overdue'].str.extract('(\d+)')[0], 
        errors='coerce'
    ).fillna(0)
    
    return df

try:
    df = get_live_data()
    st.title("🏙️ Fortune Commercial City Payment Tracker")
    st.divider()

    # --- TOP ROW: FILTERS & SELECTION ---
    col_a, col_b = st.columns(2)

    with col_a:
        sales_people = sorted(df['Sales Person'].dropna().unique())
        selected_sales = st.selectbox("👤 Filter by Sales Person", options=["-- All Sales --"] + list(sales_people))

    # Base filtering by Sales Person
    filtered_df = df.copy()
    if selected_sales != "-- All Sales --":
        filtered_df = df[df['Sales Person'] == selected_sales]

    # --- QUICK FILTER BUTTONS ---
    st.write("###Filter by Due Status")
    c1, c2, c3 = st.columns(3)
    
    if c1.button("📑 All Units", type="primary" if st.session_state.due_filter == "All" else "secondary"):
        st.session_state.due_filter = "All"
        st.rerun()
    
    if c2.button("🗓️ Current Month Due", type="primary" if st.session_state.due_filter == "Current" else "secondary"):
        st.session_state.due_filter = "Current"
        st.rerun()
        
    if c3.button("🚨 1+ Month Overdue", type="primary" if st.session_state.due_filter == "Overdue" else "secondary"):
        st.session_state.due_filter = "Overdue"
        st.rerun()

    # Apply Dashboard Logic & Column Adjustments
    base_cols = ['Plot No.', 'Sales Person', 'Customer Name', 'Total Amount to Collect', 'Status', 'Months Overdue']
    
    if st.session_state.due_filter == "Current":
        # Units that are outstanding but have 0 months overdue
        filtered_df = filtered_df[filtered_df['overdue_val'] == 0]
        display_cols = base_cols
    elif st.session_state.due_filter == "Overdue":
        # Units with 1 or more months overdue
        filtered_df = filtered_df[filtered_df['overdue_val'] >= 1]
        # Include Past Due Amount for this view
        display_cols = ['Plot No.', 'Sales Person', 'Customer Name', 'Past Due Amount', 'Total Amount to Collect', 'Status', 'Months Overdue']
    else:
        display_cols = base_cols

    with col_b:
        unit_list = sorted(filtered_df['Plot No.'].unique())
        # Sync dropdown with session state
        curr_idx = 0
        if st.session_state.selected_unit in unit_list:
            curr_idx = list(unit_list).index(st.session_state.selected_unit) + 1
            
        selected_unit_box = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list), index=curr_idx)
        if selected_unit_box != st.session_state.selected_unit:
            st.session_state.selected_unit = selected_unit_box
            st.rerun()

    # --- VIEW TOGGLE: TABLE OR DETAIL ---
    if st.session_state.selected_unit == "-- Select --":
        st.subheader(f"Dashboard: {st.session_state.due_filter} ({len(filtered_df)} Units)")
        
        # Ensure only columns existing in the data are shown
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
            
        st.header(f"Details for Unit: {st.session_state.selected_unit}")
        
        # Split details into metrics and a full table
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Collect", f"{unit_data.get('Total Amount to Collect', '0')} Lakhs")
        m2.metric("Sales Person", unit_data.get('Sales Person', 'N/A'))
        m3.metric("Status", unit_data.get('Status', 'Pending'))
        
        st.write("### Full Customer Record")
        st.table(unit_data.to_frame(name="Information"))

except Exception as e:
    st.error(f"Application Error: {e}")
