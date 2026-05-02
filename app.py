import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="EFD Sales Tracker", layout="wide")

# The Live Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- DATA LOADING ---
@st.cache_data(ttl=60) 
def get_live_data():
    # Loading everything as strings to prevent scientific notation and preserve text
    df = pd.read_csv(SHEET_URL, dtype=str)
    df.columns = df.columns.str.strip() # Remove any hidden spaces from headers
    return df

try:
    df = get_live_data()

    st.title("Payment Tracker")
    
    # Unit Selection Dropdown
    unit_list = df['Plot No.'].dropna().unique()
    selected_unit = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list))

    if selected_unit != "-- Select --":
        # Get data for the selected unit
        unit_row = df[df['Plot No.'] == selected_unit].iloc[0]

        st.divider()
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"📋 Detailed Info: {selected_unit}")
            # Show the original table view on the left
            display_df = unit_row.to_frame()
            display_df.columns = ["Value"]
            st.table(display_df)

        with col2:
            st.subheader("Payment Status")
            
            # --- EXTRACT DATA FROM NEW COLUMN NAMES ---
            # Using .get() ensures the app doesn't crash if a column is temporarily renamed
            amt_this_month = unit_row.get('Amount to Collect for This Month', '0')
            past_due = unit_row.get('Past Due Amount', '0')
            total_collect = unit_row.get('Total Amount to Collect', '0')
            bill_month = unit_row.get('Current Billing Month', 'N/A')
            overdue_status = unit_row.get('Months Overdue', '0 month due')
            current_status = str(unit_row.get('Status', 'Pending')).strip()

            # --- DISPLAY METRICS ---
            st.metric(label="Amount to Collect for This Month", value=amt_this_month)
            
            st.metric(label="Current Billing Month", value=bill_month)
            
            # Showing Total Amount to Collect with (Current + Past Due) note as requested
            st.metric(
                label="Total Amount to Collect", 
                value=total_collect, 
                help="Includes Current Month + Past Due Amount"
            )
            st.caption(f"({amt_this_month} Current + {past_due} Past Due)")

            # --- STATUS BOXES ---
            st.write("---")
            if "pending" in current_status.lower():
                st.error(f"🔴 Status: {current_status}")
                st.warning(f"⚠️ {overdue_status}")
            else:
                st.success(f"🟢 Status: {current_status}")

            st.write("---")
            st.caption("Last payment recorded on:")
            st.write(unit_row.get('Last Payment Date', 'N/A'))

except Exception as e:
    st.error("Data Sync Error")
    st.info(f"Check your Google Sheet column names. Error details: {e}")
