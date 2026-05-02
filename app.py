import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
# Replace SPREADSHEET_ID with the actual ID from your URL
SHEET_ID = "your_actual_id_here"
SHEET_NAME = "Sheet1"  # Or your specific sheet name
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

# --- APP LAYOUT ---
st.set_page_config(page_title="Property Portfolio", layout="centered")
st.title("🏗️ Property Unit Portal")

# Function to load live data
@st.cache_data(ttl=600) # Clears cache every 10 minutes to fetch new data
def load_data():
    return pd.read_csv(URL)

try:
    df = load_data()

    # 1. Start Page / Dropdown
    plot_list = df['Plot No.'].dropna().unique()
    selected_plot = st.selectbox("Select Unit or Plot No.", options=["-- Choose --"] + list(plot_list))

    if selected_plot != "-- Choose --":
        # 2. Filter for the selected row
        unit_data = df[df['Plot No.'] == selected_plot]

        st.divider()
        st.subheader(f"Unit Details: {selected_plot}")

        # 3. Transpose Data for Vertical View
        # We select the first matching row and transpose it
        details = unit_data.iloc[0].to_frame()
        details.columns = ["Value"]
        
        # Display as a clean table
        st.table(details)

except Exception as e:
    st.error("Could not connect to Google Sheets. Check your link sharing permissions.")