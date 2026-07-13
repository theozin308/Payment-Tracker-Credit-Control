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
    </style>
    """, unsafe_allow_html=True)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- SESSION STATE ---
if "selected_unit" not in st.session_state:
    st.session_state.selected_unit = "-- Select --"

if "due_filter" not in st.session_state:
    st.session_state.due_filter = "All" 

# --- OPTIMIZED CACHING LAYER ---
@st.cache_data(ttl=300) 
def download_raw_sheet():
    return pd.read_csv(SHEET_URL, dtype=str)

def get_live_data():
    df = download_raw_sheet().copy()  
    df.columns = df.columns.str.strip() 
    
    # Cleaning: Remove empty/None rows
    df = df[df['Plot No.'].notna()]
    df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', '', 'null'])]
    
    # Global Sort by Plot No.
    df = df.sort_values(by='Plot No.')
    
    # Safe handling/standardization for the new Plan column
    if 'Plan' in df.columns:
        df['Plan'] = df['Plan'].fillna('-').str.strip()
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
            # Parse out raw text/commas from sheet
            shorthand_num = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)
            
            # Conversion Check: If it looks like raw Lakhs shorthand (e.g. 3.9 instead of 390000), adjust scale
            # If values in your sheets are already stored fully (like 3900), modify multiplier accordingly.
            df[col] = shorthand_num * 100000 if shorthand_num.max() < 1000 else shorthand_num

    # --- OVERDUE EXTRACTION ---
    raw_digits = pd.to_numeric(df['Months Overdue'].str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
    is_advance = df['Months Overdue'].str.lower().str.contains('advance|paid', na=False)
    df['overdue_val'] = raw_digits.mask(is_advance, -1 * raw_digits)
    
    return df

try:
    df = get_live_data()
    
    # --- GET URL PARAMS FOR ROUTING ---
    url_params = st.query_params
    if "view_unit" in url_params:
        st.session_state.selected_unit = url_params["view_unit"]

    st.title("Fortune Commercial City Payment Tracker")
    st.divider()

    # --- ROW 1: PRIMARY FILTERS ---
    col_a, col_b = st.columns(2)

    with col_a:
        sales_people = sorted(df['Sales Person'].dropna().unique())
        selected_sales = st.selectbox("👤 Filter by Sales Person", options=["-- All Sales --"] + list(sales_people))

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
        # QUICK FILTERS
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
        
        rendered_df = display_df.copy()
        rendered_df['Action'] = rendered_df['Plot No.'].apply(lambda x: f"?view_unit={x}")
        
        # Base Columns Layout with Plan Type integrated
        base_cols = [
            'Plot No.', 
            'Plan',
            'Sales Person', 
            'Customer Name', 
            'Total Amount to Collect This Month', 
            'Total Paid',
            'Partial (or) Full Payment for Current Month',
            'Status', 
            'Months Overdue',
            'Action'
        ]
        
        st.dataframe(
            rendered_df[base_cols], 
            width='stretch', 
            hide_index=True,
            column_config={
                "Plan": st.column_config.TextColumn("Plan Type"),
                "Total Amount to Collect This Month": st.column_config.NumberColumn("Total Amount to Collect (MMK)", format="%,d"),
                "Total Paid": st.column_config.NumberColumn("Total Paid (MMK)", format="%,d"),
                "Partial (or) Full Payment for Current Month": st.column_config.NumberColumn("Current Month Payment (MMK)", format="%,d"),
                "Action": st.column_config.LinkColumn("View Details", display_text="Details ➡️")
            }
        )

    # --- DETAIL PANE ---
    else:
        unit_data = df[df['Plot No.'] == st.session_state.selected_unit].iloc[0]
        
        if st.button("⬅️ Back to Table List"):
            st.session_state.selected_unit = "-- Select --"
            st.query_params.clear() 
            st.rerun()

        st.header(f"Details: {st.session_state.selected_unit}")
        
        # --- PAYMENT HEALTH ---
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
        
        # Full Info Table
        clean_display = unit_data.drop(['overdue_val'])
        
        # Format metrics lists safely
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
