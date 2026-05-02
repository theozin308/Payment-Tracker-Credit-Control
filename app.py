import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Unit Information Portal", layout="centered")

# The Live Link from Step 1
SHEET_URL = "https://docs.google.com/spreadsheets/d/1aH4ycuqzoqmoiTx5dp2pqO9ftji79dpleeyfSxI8s5M/gviz/tq?tqx=out:csv"

# --- DATA LOADING ---
@st.cache_data(ttl=300) # This refreshes the app every 5 minutes automatically
def get_live_data():
    return pd.read_csv(SHEET_URL)

try:
    df = get_live_data()

    # --- START PAGE / SELECTION ---
    st.title("🏙️ Property Unit Viewer")
    st.write("Please select a unit to view current status and payment details.")

    # Dropdown for Plot No (matches your image_d09aff.png headers)
    unit_list = df['Plot No.'].dropna().unique()
    selected_unit = st.selectbox("Choose Unit / Plot No.", options=["-- Select --"] + list(unit_list))

    if selected_unit != "-- Select --":
        # Filter for the specific unit
        row_data = df[df['Plot No.'] == selected_unit]

        st.divider()
        st.subheader(f"Detailed Info: {selected_unit}")

        # --- TRANSPOSE LOGIC ---
        # Convert the horizontal row into a vertical table
        display_df = row_data.iloc[0].to_frame()
        display_df.columns = ["Current Status"]
        
        # Display as a clean, vertical table
        st.table(display_df)

except Exception as e:
    st.error("Check your Google Sheet Sharing settings or column names.")
