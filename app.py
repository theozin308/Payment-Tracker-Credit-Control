import streamlit as st
import pandas as pd
from datetime import datetime

# --- APP CONFIGURATION ---
st.set_page_config(page_title="EFD Sales Tracker", layout="wide")

# Your Live Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

@st.cache_data(ttl=60) # Faster refresh for active sales tracking
def get_live_data():
    # Load and force all data to be treated as strings first to avoid "missing text"
    df = pd.read_csv(SHEET_URL, dtype=str)
    # Clean up column names (removes hidden spaces)
    df.columns = df.columns.str.strip()
    return df

try:
    df = get_live_data()

    st.title("💰 Sales Collection Dashboard")
    st.info("Check unit status, overdue months, and collection amounts below.")

    # Dropdown for Unit Selection
    unit_list = df['Plot No.'].dropna().unique()
    selected_unit = st.selectbox("🎯 Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list))

    if selected_unit != "-- Select --":
        # Get the specific row for this unit
        unit_row = df[df['Plot No.'] == selected_unit].iloc[0]

        # --- REWORKED COLUMN NAMES FOR SALES PERSONS ---
        # We map your sheet headers to easy-to-read labels
        sales_view = {
            "👤 Customer Name": unit_row.get('Customer Name', 'N/A'),
            "📅 Billing Month": unit_row.get('Last Payment Month', 'N/A'),
            "💵 Amount to Collect": unit_row.get('Amount to Settle', '0'),
            "📑 Payment Plan": unit_row.get('Payment Plan', 'N/A'),
            "🏗️ Current Status": unit_row.get('Status', 'Pending'),
            "📅 Last Payment Date": unit_row.get('Last Payment Date', 'N/A'),
            "💰 Total Paid (Partial)": unit_row.get('Partial Payment', '0')
        }

        # --- OVERDUE CALCULATION (Visual Indicators) ---
        st.divider()
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Collection Details")
            # This shows the vertical table with the new easy names
            st.table(pd.DataFrame.from_dict(sales_view, orient='index', columns=['Value']))

        with col2:
            st.subheader("Payment Health")
            current_status = unit_row.get('Status', '').strip().lower()
            
            if "pending" in current_status or "partial" in current_status:
                st.error(f"⚠️ ATTENTION: {unit_row.get('Amount to Settle')} is due.")
                st.warning(f"Status is currently: {unit_row.get('Status')}")
            else:
                st.success("✅ Payment is Up to Date")

except Exception as e:
    st.error(f"Column Error: Please check if your Google Sheet has the correct headers. Error: {e}")
