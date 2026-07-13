import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="FCC Mandalay Payment Tracker", layout="wide")

# --- CSS STYLING ---
st.markdown("""
    <style>
    [data-testid="stMain"] [data-testid="stDataFrameDataLayer"] > div:first-child {
        display: none !important;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        font-weight: bold;
    }
    /* Style for legacy table link visualization */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        font-family: sans-serif;
        min-width: 400px;
    }
    .styled-table th {
        background-color: #f0f2f6;
        color: #31333F;
        text-align: left;
        padding: 12px 15px;
    }
    .styled-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #dddddd;
    }
    </style>
    """, unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- SESSION STATE ---
if "selected_unit" not in st.session_state:
    st.session_state.selected_unit = "-- Select --"

if "due_filter" not in st.session_state:
    st.session_state.due_filter = "All" 

# --- OPTIMIZED CACHING LAYER ---
@st.cache_data(ttl=30)  
def download_raw_sheet():
    try:
        return pd.read_csv(SHEET_URL, dtype=str)
    except Exception as e:
        st.error(f"Failed to download Google Sheet: {e}")
        return pd.DataFrame()

def get_live_data():
    raw_df = download_raw_sheet()
    if raw_df.empty:
        return pd.DataFrame()
        
    df = raw_df.copy()  
    df.columns = df.columns.str.strip() 
    
    # Cleaning: Keep only rows that actually have valid data
    df = df[df['Plot No.'].notna()]
    df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', '', 'null'])]
    
    # Force clean string formatting for structural layout columns
    df['Sales Person'] = df['Sales Person'].fillna('Unknown').astype(str).str.strip()
    df['Status'] = df['Status'].fillna('Outstanding').astype(str).str.strip()
    df['Months Overdue'] = df['Months Overdue'].fillna('0 month due').astype(str).str.strip()
    
    # Global Sort by Plot No.
    df = df.sort_values(by='Plot No.')
    
    if 'Plan' in df.columns:
        df['Plan'] = df['Plan'].fillna('-').astype(str).str.strip()
    else:
        df['Plan'] = '-'
    
    # Numeric Conversion for Health Metrics & Table Columns
    cols_to_fix = [
        'Amount to Collect for This Month', 
        'Past Due Amount', 
        'Total Amount to Collect This Month',
        'Total Paid',
        'Plot Price',
        'Remaining Balance',
        'Partial (or) Full Payment for Current Month'
    ]
    for col in cols_to_fix:
        if col in df.columns:
            cleaned_col = df[col].astype(str).str.replace(',', '').str.strip()
            shorthand_num = pd.to_numeric(cleaned_col, errors='coerce').fillna(0)
            df[col] = shorthand_num.apply(lambda x: x * 100000 if x < 1000 else x)

    # --- OVERDUE EXTRACTION ---
    raw_digits = pd.to_numeric(df['Months Overdue'].str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
    is_advance = df['Months Overdue'].str.lower().str.contains('advance|paid', na=False)
    df['overdue_val'] = raw_digits.mask(is_advance, -1 * raw_digits)
    
    return df

try:
    df = get_live_data()
    
    if df.empty:
        st.warning("No data found or Google Sheet connection failed.")
    else:
        # --- GET URL PARAMS FOR ROUTING ---
        url_params = st.query_params
        if "view_unit" in url_params:
            st.session_state.selected_unit = url_params["view_unit"]

        st.title("Fortune Commercial City Payment Tracker")
        st.divider()

        # --- ROW 1: PRIMARY FILTERS ---
        col_a, col_b = st.columns(2)

        with col_a:
            sales_people = sorted([sp for sp in df['Sales Person'].unique() if sp and sp != 'Unknown'])
            selected_sales = st.selectbox("👤 Filter by Sales Person", options=["-- All Sales --"] + sales_people)

        # Apply Sales Person Filter to a Master Base DataFrame
        base_filtered_df = df.copy()
        if selected_sales != "-- All Sales --":
            base_filtered_df = df[df['Sales Person'] == selected_sales]

        with col_b:
            unit_list = base_filtered_df['Plot No.'].unique()
            curr_idx = 0
            if st.session_state.selected_unit in unit_list:
                curr_idx = list(unit_list).index(st.session_state.selected_unit) + 1
                
            selected_unit_box = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list), index=curr_idx)
            if selected_unit_box != st.session_state.selected_unit:
                st.session_state.selected_unit = selected_unit_box
                if selected_unit_box == "-- Select --":
                    st.query_params.clear()
                else:
                    st.query_params["view_unit"] = selected_unit_box
                st.rerun()

        # --- DASHBOARD VIEW ---
        if st.session_state.selected_unit == "-- Select --":
            st.markdown("### Quick Filters")
            c1, c2, c3, c4 = st.columns(4)
            
            with c1:
                if st.button("📑 All Units", type="primary" if st.session_state.due_filter == "All" else "secondary"):
                    st.session_state.due_filter = "All"
                    st.rerun()
            with c2:
                if st.button("🗓️ Current Month Due", type="primary" if st.session_state.due_filter == "Current" else "secondary"):
                    st.session_state.due_filter = "Current"
                    st.rerun()
            with c3:
                if st.button("🚨 1+ Month Overdue", type="primary" if st.session_state.due_filter == "Overdue" else "secondary"):
                    st.session_state.due_filter = "Overdue"
                    st.rerun()
            with c4:
                if st.button("✅ Completed / Advance", type="primary" if st.session_state.due_filter == "Completed" else "secondary"):
                    st.session_state.due_filter = "Completed"
                    st.rerun()

            # --- FILTER LOGIC ---
            is_completed_or_advance = (
                base_filtered_df['Status'].str.lower().str.contains('complete|advance|done', na=False) |
                base_filtered_df['Months Overdue'].str.lower().str.contains('advance', na=False)
            )

            if st.session_state.due_filter == "Current":
                display_df = base_filtered_df[(base_filtered_df['overdue_val'] == 0) & (~is_completed_or_advance)]
            elif st.session_state.due_filter == "Overdue":
                display_df = base_filtered_df[(base_filtered_df['overdue_val'] >= 1) & (~is_completed_or_advance)]
            elif st.session_state.due_filter == "Completed":
                display_df = base_filtered_df[is_completed_or_advance]
            else:
                display_df = base_filtered_df

            st.subheader(f"Table View: {st.session_state.due_filter} ({len(display_df)} Units)")
            
            # --- SAFE DATAFRAME REPLACEMENT ENGINE ---
            # Instead of st.dataframe (which crashes PyArrow C++), we generate clean, fast HTML tables
            if display_df.empty:
                st.info("No records match this filter selection.")
            else:
                html_rows = ""
                for _, row in display_df.iterrows():
                    # Formatted text string metrics to protect memory allocation layers
                    amt_collect = f"{row['Total Amount to Collect This Month']:,.0f} MMK"
                    total_paid = f"{row['Total Paid']:,.0f} MMK"
                    curr_pay = f"{row['Partial (or) Full Payment for Current Month']:,.0f} MMK"
                    
                    html_rows += f"""
                    <tr>
                        <td><b>{row['Plot No.']}</b></td>
                        <td>{row['Plan']}</td>
                        <td>{row['Sales Person']}</td>
                        <td>{row['Customer Name']}</td>
                        <td>{amt_collect}</td>
                        <td>{total_paid}</td>
                        <td>{curr_pay}</td>
                        <td><span style='color: {"green" if "complete" in str(row["Status"]).lower() else "red"}; font-weight: bold;'>{row['Status']}</span></td>
                        <td>{row['Months Overdue']}</td>
                        <td><a href="?view_unit={row['Plot No.']}" target="_self">Details ➡️</a></td>
                    </tr>
                    """
                
                table_html = f"""
                <table class="styled-table">
                    <thead>
                        <tr>
                            <th>Plot No.</th>
                            <th>Plan Type</th>
                            <th>Sales Person</th>
                            <th>Customer Name</th>
                            <th>Total Amount to Collect</th>
                            <th>Total Paid</th>
                            <th>Current Month Payment</th>
                            <th>Status</th>
                            <th>Months Overdue</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {html_rows}
                    </tbody>
                </table>
                """
                st.markdown(table_html, unsafe_allow_html=True)

        # --- DETAIL PANE ---
        else:
            unit_data = df[df['Plot No.'] == st.session_state.selected_unit].iloc[0]
            
            if st.button("⬅️ Back to Table List"):
                st.session_state.selected_unit = "-- Select --"
                st.query_params.clear() 
                st.rerun()

            st.header(f"Details: {st.session_state.selected_unit}")
            
            st.markdown("### 📊 Payment Health")
            h1, h2, h3, h4 = st.columns(4)
            
            past_due = unit_data['Past Due Amount']
            this_month = unit_data['Amount to Collect for This Month']
            total_due = unit_data.get('Total Amount to Collect This Month', 0)
            last_payment = unit_data.get('Last Payment Date', 'No Record')

            h1.metric("Past Due", f"{past_due:,.0f} MMK", delta=f"{unit_data['Months Overdue']}", delta_color="inverse")
            h2.metric("Due This Month", f"{this_month:,.0f} MMK")
            h3.metric("Total to Collect", f"{total_due:,.0f} MMK")
            h4.metric("Last Payment Date", str(last_payment)) 
            
            st.divider()
            
            clean_display = unit_data.drop(['overdue_val'])
            
            if 'Past Due Amount' in clean_display:
                clean_display['Past Due Amount'] = f"{past_due:,.0f} MMK"
            if 'Amount to Collect for This Month' in clean_display:
                clean_display['Amount to Collect for This Month'] = f"{this_month:,.0f} MMK"
            if 'Total Amount to Collect This Month' in clean_display:
                clean_display['Total Amount to Collect This Month'] = f"{total_due:,.0f} MMK"
            if 'Total Paid' in clean_display:
                clean_display['Total Paid'] = f"{unit_data['Total Paid']:,.0f} MMK"
            if 'Plot Price' in clean_display:
                clean_display['Plot Price'] = f"{unit_data['Plot Price']:,.0f} MMK"
            if 'Remaining Balance' in clean_display:
                clean_display['Remaining Balance'] = f"{unit_data['Remaining Balance']:,.0f} MMK"
            if 'Partial (or) Full Payment for Current Month' in clean_display:
                clean_display['Partial (or) Full Payment for Current Month'] = f"{unit_data['Partial (or) Full Payment for Current Month']:,.0f} MMK"
            
            st.table(clean_display.to_frame(name="Information"))

except Exception as e:
    st.error(f"Application Error: {e}")
