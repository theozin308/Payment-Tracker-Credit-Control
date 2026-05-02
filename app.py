import streamlit as st
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Unit Information Portal", layout="wide") # Changed to wide for side-by-side view

# The Live Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- DATA LOADING ---
@st.cache_data(ttl=300) 
def get_live_data():
    # Adding dtype=str ensures phone numbers and IDs don't lose leading zeros
    return pd.read_csv(SHEET_URL, dtype=str)

try:
    df = get_live_data()

    # --- START PAGE / SELECTION ---
    st.title("🏙️ Property Unit Viewer")
    st.write("Please select a unit to view current status and payment details.")

    # Dropdown for Plot No
    unit_list = df['Plot No.'].dropna().unique()
    selected_unit = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list))

    if selected_unit != "-- Select --":
        # Filter for the specific unit
        row_data = df[df['Plot No.'] == selected_unit]
        unit_row = row_data.iloc[0]

        st.divider()
        
        # --- LAYOUT: 2 COLUMNS ---
        col1, col2 = st.columns([2, 1]) # Left side wider for data, right side for health

        with col1:
            st.subheader(f"📋 Detailed Info: {selected_unit}")
            # Your original Transpose Logic
            display_df = row_data.iloc[0].to_frame()
            display_df.columns = ["Value"]
            st.table(display_df)

        with col2:
            st.subheader("🏥 Payment Health")
            
            # 1. Actionable Metrics
            amount_to_collect = unit_row.get('Amount to Settle', '0')
            status = str(unit_row.get('Status', 'Pending')).strip()
            billing_month = unit_row.get('Last Payment Month', 'N/A')

            st.metric(label="Amount to Collect", value=f"{amount_to_collect}")
            st.metric(label="Current Billing Month", value=billing_month)

            # 2. Visual Status Indicator
            if status.lower() == "pending":
                st.error(f"🔴 Status: {status}")
                st.warning("Action: Follow up for immediate collection.")
            elif status.lower() == "partial":
                st.warning(f"🟡 Status: {status}")
                st.info("Action: Check remaining balance.")
            else:
                st.success(f"🟢 Status: {status}")
                st.balloons() # Fun celebration for full payment!

            # 3. Simple Overdue Logic
            # Note: This assumes 'Last Payment Date' exists in your sheet
            st.write("---")
            st.caption("Last interaction recorded on:")
            st.write(unit_row.get('Last Payment Date', 'No date recorded'))

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Tip: Ensure your Google Sheet columns exactly match the names in the code.")
