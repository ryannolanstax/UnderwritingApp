# python3 -m streamlit run Underwriting_App/pages/vamp.py

import streamlit as st
import pandas as pd
from io import BytesIO
import requests
import json
import io
import sys
import os
from auth_utils import require_role, get_user_info

st.set_page_config(page_title="Firecrawl + Claude Analysis", page_icon="🔎")

# Add the parent directory to Python path to import auth_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# This will check authentication and redirect if not logged in
if require_role(["Risk"], "Exposure Decay Portfolio"):

    # Your protected page content goes here
    user_info = get_user_info()

    st.title("Visa VAMP Groupby Exporter")
    
    # File upload
    dispute_file = st.file_uploader("Upload Dispute Details xlsx", type=["xlsx"])
    fraud_analysis_file = st.file_uploader("Upload Fraud Analysis xlsx", type=["xlsx"])
    fraud_details_file = st.file_uploader("Upload Fraud Details xlsx", type=["xlsx"])
    
    if dispute_file and fraud_analysis_file and fraud_details_file:
        # Read Excel files
        df_vamp = pd.read_excel(dispute_file)
        df_fraud_analysis = pd.read_excel(fraud_analysis_file, header=2)
        df_fraud_details = pd.read_excel(fraud_details_file, header=2)
    
        # Fix merged BIN/MCC cells
        for df in [df_vamp, df_fraud_analysis, df_fraud_details]:
            if "Acquirer BIN" in df.columns:
                df["Acquirer BIN"] = df["Acquirer BIN"].ffill()
            if "Merchant Category Code" in df.columns:
                df["Merchant Category Code"] = df["Merchant Category Code"].ffill()
    
        # Collect all groupbys
        results = {}
    
        # --- Dispute groupbys ---
        results["Dispute_by_BIN"] = (
            df_vamp.groupby("Acquirer BIN")[["Dispute Amount", "Dispute Count"]]
            .sum()
            .reset_index()[["Acquirer BIN", "Dispute Amount", "Dispute Count"]]
            .sort_values("Dispute Count", ascending=False)
        )
    
        results["Dispute_by_BIN_MCC"] = (
            df_vamp.groupby(["Acquirer BIN", "Merchant Category Code"])[["Dispute Amount", "Dispute Count"]]
            .sum()
            .reset_index()[["Acquirer BIN", "Merchant Category Code", "Dispute Amount", "Dispute Count"]]
            .sort_values("Dispute Count", ascending=False)
        )
    
        # --- Fraud Analysis groupbys ---
        results["FraudAnalysis_by_BIN"] = (
            df_fraud_analysis.groupby("Acquirer BIN")[["Fraud Transaction Amount", "Fraud Transaction Count"]]
            .sum()
            .reset_index()[["Acquirer BIN", "Fraud Transaction Amount", "Fraud Transaction Count"]]
            .sort_values("Fraud Transaction Count", ascending=False)
        )
    
        results["FraudAnalysis_by_BIN_MCC"] = (
            df_fraud_analysis.groupby(["Acquirer BIN", "Merchant Category Code"])[["Fraud Transaction Amount", "Fraud Transaction Count"]]
            .sum()
            .reset_index()[["Acquirer BIN", "Merchant Category Code", "Fraud Transaction Amount", "Fraud Transaction Count"]]
            .sort_values("Fraud Transaction Count", ascending=False)
        )
    
        # --- Fraud Details groupbys ---
        results["FraudDetails_by_BIN"] = (
            df_fraud_details.groupby("Acquirer BIN")[["Fraud Amount", "Fraud Count"]]
            .sum()
            .reset_index()[["Acquirer BIN", "Fraud Amount", "Fraud Count"]]
            .sort_values("Fraud Count", ascending=False)
        )
    
        results["FraudDetails_by_BIN_MCC"] = (
            df_fraud_details.groupby(["Acquirer BIN", "Merchant Category Code"])[["Fraud Amount", "Fraud Count"]]
            .sum()
            .reset_index()[["Acquirer BIN", "Merchant Category Code", "Fraud Amount", "Fraud Count"]]
            .sort_values("Fraud Count", ascending=False)
        )
    
        # Save to Excel with multiple tabs
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for sheet_name, df in results.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        output.seek(0)
    
        # Download button
        st.download_button(
            label="Download Excel with Groupbys",
            data=output,
            file_name="visa_vamp_groupbys.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
