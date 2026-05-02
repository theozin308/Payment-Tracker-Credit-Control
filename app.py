import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="EFD Sales Tracker", layout="wide")

# The Live Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- DATA LOADING ---
@st.cache_data(ttl=60) 
def get_live_data():
    df = pd.read_csv(SHEET_URL, dtype=str)
    df.columns = df.columns.str.strip() 
    return df

try:
    df = get_live_data()

    st.title("Payment Tracker")
    
    # --- SELECTION AREA: TWO COLUMNS ---
    select_col1, select_col2 = st.columns(2)

    with select_col1:
        # 1. Sales Person Selection
        sales_list = df['Sales Person'].dropna().unique()
        selected_sales = st.selectbox("Filter by Sales Person", options=["-- All Sales --"] + list(sales_list))

    # Filter data based on Sales Person selection
    filtered_df = df.copy()
    if selected_sales != "-- All Sales --":
        filtered_df = df[df['Sales Person'] == selected_sales]

    with select_col2:
        # 2. Unit Selection (Filtered by the chosen Sales Person)
        unit_list = filtered_df['Plot No.'].dropna().unique()
        selected_unit = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list))

    # --- SALES PERSON TABLE VIEW ---
    # Show this only if a Sales Person is selected but a specific Unit is NOT yet selected
    if selected_sales != "-- All Sales --" and selected_unit == "-- Select --":
        st.divider()
        st.subheader(f"📊 Summary for {selected_sales}")
        
        # Select specific columns to show in the overview table
        summary_columns = ['Plot No.', 'Customer Name', 'Current Billing Month', 'Total Amount to Collect', 'Status']
        st.dataframe(filtered_df[summary_columns], use_container_width=True, hide_index=True)

    # --- INDIVIDUAL UNIT DETAIL VIEW ---
    if selected_unit != "-- Select --":
        unit_row = filtered_df[filtered_df['Plot No.'] == selected_unit].iloc[0]

        st.divider()
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"📋 Detailed Info: {selected_unit}")
            display_df = unit_row.to_frame()
            display_df.columns = ["Value"]
            st.table(display_df)

        with col2:
            st.subheader("Payment Status")
            
            amt_this_month = unit_row.get('Amount to Collect for This Month', '0')
            past_due = unit_row.get('Past Due Amount', '0')
            total_collect = unit_row.get('Total Amount to Collect', '0')
            bill_month = unit_row.get('Current Billing Month', 'N/A')
            overdue_status = unit_row.get('Months Overdue', '0 month due')
            current_status = str(unit_row.get('Status', 'Pending')).strip()

            st.metric(label="Amount to Collect for This Month", value=amt_this_month)
            st.metric(label="Current Billing Month", value=bill_month)
            st.metric(
                label="Total Amount to Collect", 
                value=total_collect, 
                help="Includes Current Month + Past Due Amount"
            )
            st.caption(f"({amt_this_month} Current + {past_due} Past Due)")

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
