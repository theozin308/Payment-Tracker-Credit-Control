import streamlit as st
import pandas as pd
import streamlit.components.v1 as components  # Required for injecting JS

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
        move-height: 3.5em;
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

@st.cache_data(ttl=60) 
def get_live_data():
    df = pd.read_csv(SHEET_URL, dtype=str)
    df.columns = df.columns.str.strip() 
    
    # Cleaning: Remove empty/None rows
    df = df[df['Plot No.'].notna()]
    df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', '', 'null'])]
    
    # Global Sort by Plot No.
    df = df.sort_values(by='Plot No.')
    
    # Numeric Conversion for Health Metrics
    cols_to_fix = ['Amount to Collect for This Month', 'Past Due Amount', 'Total Amount to Collect']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)

    # Convert 'Months Overdue' to numeric
    df['overdue_val'] = pd.to_numeric(df['Months Overdue'].str.extract('(\d+)')[0], errors='coerce').fillna(0)
    
    return df

try:
    df = get_live_data()
    st.title("Fortune Commercial City Payment Tracker")
    st.divider()

    # --- ADD TO HOME SCREEN BUTTON COMPONENTS ---
    # This injects a hidden handler that pops up an install button only if the browser supports it.
    components.html("""
    <div id="install-container" style="display:none; padding: 10px 0px;">
        <button id="btnInstall" style="
            width: 100%; 
            background-color: #FF4B4B; 
            color: white; 
            border: none; 
            padding: 12px; 
            font-size: 16px; 
            font-weight: bold; 
            border-radius: 8px; 
            cursor: pointer;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
            📲 Install FCC Tracker on Home Screen
        </button>
    </div>

    <script>
        let deferredPrompt;
        const btnInstall = document.getElementById('btnInstall');
        const container = document.getElementById('install-container');

        // Listen for the browser's install prompt offer
        window.addEventListener('beforeinstallprompt', (e) => {
            // Prevent Chrome 67 and earlier from automatically showing the prompt
            e.preventDefault();
            // Stash the event so it can be triggered later.
            deferredPrompt = e;
            // Update UI notify the user they can install the PWA
            container.style.display = 'block';
        });

        btnInstall.addEventListener('click', async () => {
            if (!deferredPrompt) return;
            // Show the install prompt
            deferredPrompt.prompt();
            // Wait for the user to respond to the prompt
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`User response to the install prompt: ${outcome}`);
            // We've used the prompt, and can't use it again
            deferredPrompt = null;
            // Hide our custom button
            container.style.display = 'none';
        });

        window.addEventListener('appinstalled', () => {
            // Clear the deferredPrompt so it can be garbage collected
            deferredPrompt = null;
            container.style.display = 'none';
            console.log('PWA was installed');
        });
    </script>
    """, height=70)

    # --- ROW 1: PRIMARY FILTERS ---
    col_a, col_b = st.columns(2)

    with col_a:
        sales_people = sorted(df['Sales Person'].dropna().unique())
        selected_sales = st.selectbox("👤 Filter by Sales Person", options=["-- All Sales --"] + list(sales_people))

    filtered_df = df.copy()
    if selected_sales != "-- All Sales --":
        filtered_df = df[df['Sales Person'] == selected_sales]

    with col_b:
        unit_list = filtered_df['Plot No.'].unique()
        curr_idx = 0
        if st.session_state.selected_unit in unit_list:
            curr_idx = list(unit_list).index(st.session_state.selected_unit) + 1
            
        selected_unit_box = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list), index=curr_idx)
        if selected_unit_box != st.session_state.selected_unit:
            st.session_state.selected_unit = selected_unit_box
            st.rerun()

    # --- DASHBOARD VIEW ---
    if st.session_state.selected_unit == "-- Select --":
        # QUICK FILTERS
        st.markdown("### Quick Filters")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🚨 1+ Month Overdue", type="primary" if st.session_state.due_filter == "Overdue" else "secondary"):
                st.session_state.due_filter = "Overdue"
                st.rerun()
        with c2:
            if st.button("🗓️ Current Month Due", type="primary" if st.session_state.due_filter == "Current" else "secondary"):
                st.session_state.due_filter = "Current"
                st.rerun()
        with c3:
            if st.button("📑 All Units", type="primary" if st.session_state.due_filter == "All" else "secondary"):
                st.session_state.due_filter = "All"
                st.rerun()

        # Filter Logic
        base_cols = ['Plot No.', 'Sales Person', 'Customer Name', 'Total Amount to Collect', 'Status', 'Months Overdue']
        if st.session_state.due_filter == "Current":
            display_df = filtered_df[filtered_df['overdue_val'] == 0]
        elif st.session_state.due_filter == "Overdue":
            display_df = filtered_df[filtered_df['overdue_val'] >= 1]
        else:
            display_df = filtered_df

        st.subheader(f"Table View: {st.session_state.due_filter} ({len(display_df)} Units)")
        
        event = st.dataframe(
            display_df[base_cols], 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",  
            selection_mode="single-row"
        )

        if len(event.selection.rows) > 0:
            row_idx = event.selection.rows[0]
            st.session_state.selected_unit = display_df.iloc[row_idx]['Plot No.']
            st.rerun()

    # --- DETAIL PANE (With Payment Health & Last Payment) ---
    else:
        unit_data = df[df['Plot No.'] == st.session_state.selected_unit].iloc[0]
        
        if st.button("⬅️ Back to Table List"):
            st.session_state.selected_unit = "-- Select --"
            st.rerun()

        st.header(f"Details: {st.session_state.selected_unit}")
        
        # --- PAYMENT HEALTH (Unit Specific) ---
        st.markdown("### 📊 Payment Health")
        h1, h2, h3, h4 = st.columns(4)
        
        past_due = unit_data['Past Due Amount']
        this_month = unit_data['Amount to Collect for This Month']
        total_due = unit_data['Total Amount to Collect']
        last_payment = unit_data.get('Last Payment Date', 'No Record')

        h1.metric("Past Due", f"{past_due:,.0f} MMK", delta=f"{unit_data['Months Overdue']}", delta_color="inverse")
        h2.metric("Due This Month", f"{this_month:,.0f} MMK")
        h3.metric("Total to Collect", f"{total_due:,.0f} MMK")
        h4.metric("Last Payment Date", str(last_payment)) 
        
        st.divider()
        
        # Full Info Table
        clean_display = unit_data.drop(['overdue_val'])
        st.table(clean_display.to_frame(name="Information"))

except Exception as e:
    st.error(f"Application Error: {e}")
