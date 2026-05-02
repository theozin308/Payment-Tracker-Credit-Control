import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="EFD Sales Tracker", layout="wide")

# The Live Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- DATA LOADING ---
@st.cache_data(ttl=60) 
def get_live_data():
    # Load everything as strings to ensure data like Plot Nos and IDs appear correctly
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

    # Filter data based on sales person selection
    filtered_df = df.copy()
    if selected_sales != "-- All Sales --":
        filtered_df = df[df['Sales Person'] == selected_sales]

    with col_b:
        unit_list = filtered_df['Plot No.'].dropna().unique()
        selected_unit = st.selectbox("🎯 Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list))

    # --- INTERACTIVE TABLE VIEW ---
    if selected_sales != "-- All Sales --":
        st.subheader(f"📊 Unit Summary for {selected_sales}")
        
        # We only show the essential columns in the table
        summary_table = filtered_df[['Plot No.', 'Customer Name', 'Total Amount to Collect', 'Status', 'Months Overdue']]
        
        # This configuration makes the whole row clickable
        event = st.dataframe(
            summary_table, 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",  # Triggers update when clicking anywhere in a row
            selection_mode="single-row"
        )

        # If a row is clicked, update the selected_unit automatically
        if event.selection.rows:
            selected_row_index = event.selection.rows[0]
            selected_unit = summary_table.iloc[selected_row_index]['Plot No.']

    # --- DETAIL INFO PANE (Displays below the table) ---
    if selected_unit != "-- Select --":
        unit_row = df[df['Plot No.'] == selected_unit].iloc[0]

        st.divider()
        st.header(f"🔍 Viewing Unit: {selected_unit}")
        
        # Display side-by-side: Details on left, Health on right
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📋 Detailed Info")
            display_df = unit_row.to_frame()
            display_df.columns = ["Value"]
            st.table(display_df)

        with col2:
            st.subheader("Payment Status")
            
            # Extract variables based on your updated sheet headers
            amt_this_month = unit_row.get('Amount to Collect for This Month', '0')
            past_due = unit_row.get('Past Due Amount', '0')
            total_collect = unit_row.get('Total Amount to Collect', '0')
            bill_month = unit_row.get('Current Billing Month', 'N/A')
            overdue_status = unit_row.get('Months Overdue', '0 month due')
            current_status = str(unit_row.get('Status', 'Pending')).strip()

            # Display metrics for quick reading
            st.metric(label="Amount to Collect for This Month", value=amt_this_month)
            st.metric(label="Current Billing Month", value=bill_month)
            
            st.metric(
                label="Total Amount to Collect", 
                value=total_collect, 
                help="Includes Current Month + Past Due Amount"
            )
            st.caption(f"({amt_this_month} Current + {past_due} Past Due)")

            st.write("---")
            # Visual indicator based on Status
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
