import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime

# --- USER LOGIN SETUP ---
USERS = {"pauline": "gritblueprint", "ben": "gritblueprint"}

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

def login():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state.authenticated = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid credentials.")

if not st.session_state.authenticated:
    login()
    st.stop()

# --- MAIN APP ---
st.set_page_config(page_title="Product Price Updater", layout="wide")
st.title("📦 Product Price Updater")
st.write(f"👤 Logged in as: {st.session_state.username}")

main_file = st.file_uploader("📁 Upload Main Spreadsheet", type="xlsx")
vendor_file = st.file_uploader("📁 Upload Vendor Spreadsheet", type="xlsx")

if main_file and vendor_file:
    main_df = pd.read_excel(main_file)
    vendor_df = pd.read_excel(vendor_file)

    # Normalize columns
    main_df.columns = main_df.columns.str.strip().str.lower()
    vendor_df.columns = vendor_df.columns.str.strip().str.lower()

    vendor_df.rename(columns={'item number': 'product code', 'new price': 'updated price'}, inplace=True)

    # Merge and detect changes
    merged_df = main_df.merge(
        vendor_df[['product code', 'updated price']],
        on='product code', how='left'
    )

    merged_df['original price'] = merged_df['drop ship price']
    merged_df['was updated'] = (
        merged_df['updated price'].notnull() &
        ~np.isclose(merged_df['original price'], merged_df['updated price'], rtol=1e-5, atol=1e-8)
    )

    # Apply only actual changes
    merged_df.loc[merged_df['was updated'], 'drop ship price'] = merged_df['updated price']
    changes_df = merged_df[merged_df['was updated']]

    if not changes_df.empty:
        st.subheader("🔄 Products That Will Be Updated")
        st.dataframe(changes_df[['product code', 'original price', 'drop ship price']])

        if st.button("✅ Confirm Price Update"):
            st.session_state.confirmed = True
            st.success("Price update confirmed!")

        if st.session_state.get("confirmed"):
            # Create downloadable updated Excel
            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.drop(columns=['updated price', 'original price', 'was updated'], errors='ignore').to_excel(writer, index=False)
                return output.getvalue()

            updated_file = to_excel(merged_df)

            st.download_button(
                "📥 Download Updated main.xlsx",
                updated_file,
                file_name="main.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Prepare changelog
            changelog_df = changes_df[['product code', 'original price', 'drop ship price']].copy()
            changelog_df['original price'] = changelog_df['original price'].round(5)
            changelog_df['drop ship price'] = changelog_df['drop ship price'].round(5)
            changelog_df['updated by'] = st.session_state.username
            changelog_df['timestamp'] = datetime.now().strftime("%m/%d/%Y %H:%M")

            changelog_csv = changelog_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "🗒️ Download Change Log (CSV)",
                changelog_csv,
                file_name=f"price_update_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv'
            )
    else:
        st.info("✅ No price changes detected. All prices in the vendor file already match the main file.")
