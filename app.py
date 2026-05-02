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
        # Dropdown remains for manual selection
        selected_unit = st.selectbox("🎯 Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list))

    # --- SALES PERSON TABLE VIEW (INTERACTIVE) ---
    if selected_sales != "-- All Sales --":
        st.subheader(f"📊 Unit Summary for {selected_sales}")
        
        summary_table = filtered_df[['Plot No.', 'Customer Name', 'Total Amount to Collect', 'Status', 'Months Overdue']]
        
        # Enable row selection in the dataframe
        event = st.dataframe(
            summary_table, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",  # This triggers the app to update when a row is clicked
            selection_mode="single-row"
        )

        # Logic to update selected_unit based on table click
        if len(event.selection.rows) > 0:
            selected_row_index = event.selection.rows[0]
            selected_unit = summary_table.iloc[selected_row_index]['Plot No.']

    # --- DETAIL INFO PANE (Appears under the table when a row or dropdown is selected) ---
    if selected_unit != "-- Select --":
        unit_row = df[df['Plot No.'] == selected_unit].iloc[0]

        st.divider()
        st.header(f"🔍 Viewing Unit: {selected_unit}")
        
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📋 Detailed Info")
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
    st.info(f"Details: {e}")
