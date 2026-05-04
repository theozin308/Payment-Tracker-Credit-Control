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
    </style>
    """, unsafe_allow_html=True)

# The Live Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- SESSION STATE INITIALIZATION ---
# This ensures the app "remembers" what you clicked
if "selected_unit" not in st.session_state:
    st.session_state.selected_unit = "-- Select --"

@st.cache_data(ttl=60) 
def get_live_data():
    df = pd.read_csv(SHEET_URL, dtype=str)
    df.columns = df.columns.str.strip() 
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

    with col_b:
        unit_list = filtered_df['Plot No.'].dropna().unique()
        
        # We sync the selectbox with session_state. If session_state changes via table click,
        # this dropdown updates automatically.
        current_index = 0
        if st.session_state.selected_unit in unit_list:
            current_index = list(unit_list).index(st.session_state.selected_unit) + 1

        selected_unit_box = st.selectbox(
            "Choose Unit / Plot No.", 
            options=["-- Select --"] + list(unit_list),
            index=current_index
        )
        
        # If user manually changes the dropdown, update session state
        if selected_unit_box != st.session_state.selected_unit:
            st.session_state.selected_unit = selected_unit_box
            st.rerun()

    # --- INTERACTIVE TABLE VIEW ---
    # Only show the table if no unit is currently selected
    if selected_sales != "-- All Sales --" and st.session_state.selected_unit == "-- Select --":
        st.subheader(f"Unit Summary for {selected_sales}")
        st.caption("Select a checkbox to view full details.")
        
        summary_table = filtered_df[['Plot No.', 'Customer Name', 'Total Amount to Collect', 'Status', 'Months Overdue']]
        
        # Capture the selection event
        event = st.dataframe(
            summary_table, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",  
            selection_mode="single-row"
        )

        # Logic to handle the checkbox click
        if len(event.selection.rows) > 0:
            row_idx = event.selection.rows[0]
            st.session_state.selected_unit = summary_table.iloc[row_idx]['Plot No.']
            st.rerun()

    # --- DETAIL INFO PANE ---
    if st.session_state.selected_unit != "-- Select --":
        unit_row = df[df['Plot No.'] == st.session_state.selected_unit].iloc[0]

        st.divider()
        if st.button("⬅️ Back to Summary List"):
            st.session_state.selected_unit = "-- Select --"
            st.rerun()

        st.header(f"Viewing Unit: {st.session_state.selected_unit}")
        
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Detailed Info")
            st.table(unit_row.to_frame(name="Value"))

        with col2:
            st.subheader("Payment Health")
            st.metric(label="Total to Collect", value=f"{unit_row.get('Total Amount to Collect', '0')} Lakhs")
            st.metric(label="Status", value=unit_row.get('Status', 'N/A'))
            st.warning(f"🚨 {unit_row.get('Months Overdue', '0')} months overdue")

except Exception as e:
    st.error(f"Error: {e}")
