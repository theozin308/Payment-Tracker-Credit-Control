import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="FCC Mandalay Payment Tracker", layout="wide")

# --- CUSTOM NATIVE AUTHENTICATION ---
# Initialize authentication status if it doesn't exist
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

def check_credentials(username, password):
    """Helper function to validate credentials against Streamlit secrets."""
    try:
        # Pull the user dictionary from Secrets Management
        user_db = st.secrets["users"]
        if username in user_db and user_db[username] == password:
            return True
    except Exception:
        st.error("Credentials database configuration missing in Secrets panel.")
    return False

# --- LOGIN SCREEN VIEW ---
if not st.session_state.authenticated:
    # Center the login box layout nicely on screen
    _, col_login, _ = st.columns([1, 2, 1])
    
    with col_login:
        st.markdown("<h2 style='text-align: center;'>🔐 FCC Tracker Login</h2>", unsafe_allow_html=True)
        
        # Using a standard st.form prevents the page from refreshing on every keystroke
        with st.form("login_form"):
            user_input = st.selectbox("Select User Role", options=["-- Select Role --", "Sales Person", "Sales Admin", "Sales Management"])
            pass_input = st.text_input("Enter Password", type="password")
            submit_button = st.form_submit_button("Log In", use_container_width=True)
            
            if submit_button:
                if user_input != "-- Select Role --" and check_credentials(user_input, pass_input):
                    st.session_state.authenticated = True
                    st.session_state.user_name = user_input
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("❌ Invalid Role or Password. Please try again.")

# --- DASHBOARD VIEW (UNLOCKED AFTER SUCCESSFUL LOGIN) ---
else:
    # Sidebar navigation with a native logout button
    st.sidebar.markdown(f"### Welcome, **{st.session_state.user_name}** 👋")
    if st.sidebar.button("🔓 Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_name = ""
        st.rerun()

    # --- Original CSS Styling ---
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
        df = df[df['Plot No.'].notna()]
        df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', '', 'null'])]
        df = df.sort_values(by='Plot No.')
        
        cols_to_fix = ['Amount to Collect for This Month', 'Past Due Amount', 'Total Amount to Collect']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)

        df['overdue_val'] = pd.to_numeric(df['Months Overdue'].str.extract(r'(\d+)')[0], errors='coerce').fillna(0)
        return df

    try:
        df = get_live_data()
        st.title("Fortune Commercial City Payment Tracker")
        st.divider()

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

        # --- DETAIL PANE ---
        else:
            unit_data = df[df['Plot No.'] == st.session_state.selected_unit].iloc[0]
            
            if st.button("⬅️ Back to Table List"):
                st.session_state.selected_unit = "-- Select --"
                st.rerun()

            st.header(f"Details: {st.session_state.selected_unit}")
            
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
            
            clean_display = unit_data.drop(['overdue_val'])
            st.table(clean_display.to_frame(name="Information"))

    except Exception as e:
        st.error(f"Application Error: {e}")
