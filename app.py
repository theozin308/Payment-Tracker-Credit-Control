# --- DETAIL PANE (With Payment Health & Last Payment) ---
    else:
        unit_data = df[df['Plot No.'] == st.session_state.selected_unit].iloc[0]
        
        if st.button("⬅️ Back to Table List"):
            st.session_state.selected_unit = "-- Select --"
            st.rerun()

        st.header(f"Details: {st.session_state.selected_unit}")
        
        # --- PAYMENT HEALTH (Unit Specific) ---
        st.markdown("### 📊 Payment Health")
        # Added a 4th column for the Last Payment Date
        h1, h2, h3, h4 = st.columns(4)
        
        past_due = unit_data['Past Due Amount']
        this_month = unit_data['Amount to Collect for This Month']
        total_due = unit_data['Total Amount to Collect']
        last_payment = unit_data.get('Last Payment Date', 'No Record')

        h1.metric("Past Due", f"{past_due:,.0f} MMK", delta=f"{unit_data['Months Overdue']}", delta_color="inverse")
        h2.metric("Due This Month", f"{this_month:,.0f} MMK")
        h3.metric("Total to Collect", f"{total_due:,.0f} MMK")
        h4.metric("Last Payment Date", str(last_payment)) # Highlighting the date here
        
        st.divider()
        
        # Full Info Table
        clean_display = unit_data.drop(['overdue_val'])
        st.table(clean_display.to_frame(name="Information"))
