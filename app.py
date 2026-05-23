# Keep the raw data download cached for up to 5-10 minutes to save network overhead
@st.cache_data(ttl=300) 
def download_raw_sheet():
    return pd.read_csv(SHEET_URL, dtype=str)

# Process and clean the data separately
def get_live_data():
    df = download_raw_sheet().copy() # Copy prevents cache mutation errors
    df.columns = df.columns.str.strip() 
    
    # Cleaning: Remove empty/None rows
    df = df[df['Plot No.'].notna()]
    df = df[~df['Plot No.'].str.lower().isin(['none', 'nan', '', 'null'])]
    df = df.sort_values(by='Plot No.')
    
    # Numeric Conversion for Health Metrics
    cols_to_fix = ['Amount to Collect for This Month', 'Past Due Amount', 'Total Amount to Collect']
    for col in cols_to_fix:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0)

    df['overdue_val'] = pd.to_numeric(df['Months Overdue'].str.extract('(\d+)')[0], errors='coerce').fillna(0)
    return df
