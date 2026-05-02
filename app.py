import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Unit Information Portal", layout="wide")

# The Live Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- DATA LOADING ---
@st.cache_data(ttl=300) 
def get_live_data():
    return pd.read_csv(SHEET_URL, dtype=str)

try:
    df = get_live_data()
    # Clean column names just in case there are hidden spaces
    df.columns = df.columns.str.strip()

    st.title("🏙️ Property Unit Viewer")
    st.write("Please select a unit to view current status and payment details.")

    unit_list = df['Plot No.'].dropna().unique()
    selected_unit = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list))

    if selected_unit != "-- Select --":
        row_data = df[df['Plot No.'] == selected_unit]
        unit_row = row_data.iloc[0]

        st.divider()
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"📋 Detailed Info: {selected_unit}")
            display_df = unit_row.to_frame()
            display_df.columns = ["Value"]
            st.table(display_df)

        with col2:
            st.subheader("🏥 Payment Health")
            
            # --- FIXING THE METRICS ---
            # Using .get() with the exact names shown in your screenshot table
            amt_collect = unit_row.get('Amount to Collect for This Month', '0')
            bill_month = unit_row.get('Current Billing Month', 'N/A')
            
            # --- CALCULATING OUTSTANDING BALANCE ---
            # Total Amount - Total Paid (Ensure they are treated as numbers)
            try:
                total_amt = float(str(unit_row.get('Total Amount (Incl. Booking Fee)', '0')).replace(',', ''))
                total_paid = float(str(unit_row.get('Total Paid', '0')).replace(',', ''))
                outstanding = total_amt - total_paid
            except:
                outstanding = 0

            # Display Metrics
            st.metric(label="Amount to Collect", value=f"{amt_collect}")
            st.metric(label="Current Billing Month", value=f"{bill_month}")
            st.metric(label="Total Outstanding Balance", value=f"{outstanding:,.0f}")

            # Visual Status
            status = str(unit_row.get('Status', 'Pending')).strip()
            if status.lower() == "pending":
                st.error(f"🔴 Status: {status}")
                st.warning("Action: Follow up for immediate collection.")
            else:
                st.success(f"🟢 Status: {status}")

            st.write("---")
            st.caption("Last interaction recorded on:")
            st.write(unit_row.get('Last Payment Date', 'N/A'))

except Exception as e:
    st.error(f"Error: {e}")
