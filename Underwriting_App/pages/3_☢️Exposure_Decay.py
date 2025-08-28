import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import io
import sys
import os
from auth_utils import require_role, get_user_info
#from auth_utils import require_role, get_user_info


st.set_page_config(page_title="Exposure Decay Portfolio", page_icon="☢️", layout="wide")

# Add the parent directory to Python path to import auth_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# This will check authentication and redirect if not logged in
#if require_auth("Exposure Decay Portfolio"):
if require_role(["Risk"], "Exposure Decay Portfolio"):

    # Your protected page content goes here
    user_info = get_user_info()

    
    # ------------------ CONFIG ------------------
    risk_cols = [
        "refund_risk",
        "chargeback_risk",
        "cnp_dd_risk",
        "cp_dd_risk",
        "ach_new_reject_exposure",
        "ach_dd_risk"
    ]
    
    # Half-life rules
    def calculate_chargeback_risk_value(cb):
        if cb <= 0.1:
            return 30
        elif cb <= 0.5:
            return 40
        elif cb <= 1:
            return 50
        else:
            return 60
    
    def calculate_refund_risk_value(refund):
        if refund <= 0.5:
            return 5
        elif refund <= 2.5:
            return 10
        elif refund <= 5:
            return 15
        else:
            return 20
    
    st.title("Portfolio-Level & Merchant-Level Exposure Decay")
    st.markdown("Automatically calculates decay for 6 components and totals them per merchant.")
    
    
    
    # ------------------ FILE UPLOAD ------------------
    merchants = st.file_uploader("Upload Merchant Spreadsheet", type=['csv', 'xlsx'])
    
    if merchants is not None:
        merchants_df = pd.read_csv(merchants)
    
        # Auto half-life per merchant
        merchants_df["hl_chargeback"] = merchants_df["chargeback_risk"].apply(calculate_chargeback_risk_value)
        merchants_df["hl_refund"] = merchants_df["refund_risk"].apply(calculate_refund_risk_value)
        merchants_df["hl_ach_reject"] = 5
        merchants_df["hl_cnp_dd"] = merchants_df["dd_cnp"]
        merchants_df["hl_cp_dd"] = merchants_df["dd_cp"]
        merchants_df["hl_ach_dd"] = merchants_df["dd_ach"]
    
        # Map half-lives
        hl_map = {
            "refund_risk": "hl_refund",
            "chargeback_risk": "hl_chargeback",
            "ach_new_reject_exposure": "hl_ach_reject",
            "cnp_dd_risk": "hl_cnp_dd",
            "cp_dd_risk": "hl_cp_dd",
            "ach_dd_risk": "hl_ach_dd"
        }
    
        # Calculate decay results per merchant
        decay_days = np.arange(0, 181, 30)
        all_results = []
        for idx, row in merchants_df.iterrows():
            merchant_result = {"stax_merchant_id": row["stax_merchant_id"]}
            for col in risk_cols:
                merchant_result[f"{col}_start"] = row[col]
            for day in decay_days:
                total_exposure_day = 0
                for col in risk_cols:
                    base_val = row[col]
                    hl = row[hl_map[col]]
                    decayed_val = base_val * (0.5 ** (day / hl)) if hl > 0 else 0
                    total_exposure_day += decayed_val
                merchant_result[f"exposure_day_{day}"] = total_exposure_day
            all_results.append(merchant_result)
    
        results_df = pd.DataFrame(all_results)
        exposure_cols = [col for col in results_df.columns if col.startswith("exposure_day_")]
        results_df[exposure_cols] = results_df[exposure_cols].applymap(lambda x: f"${x:,.2f}")
    
        # ===== Portfolio-Level Curves =====
        days = np.arange(0, 181)
        portfolio_curves = {col: np.zeros_like(days, dtype=float) for col in risk_cols + ["Total Exposure"]}
        for _, row in merchants_df.iterrows():
            for col in risk_cols:
                hl = row[hl_map[col]]
                base_val = row[col]
                decay_curve = base_val * (0.5 ** (days / hl)) if hl > 0 else np.zeros_like(days)
                portfolio_curves[col] += decay_curve
        portfolio_curves["Total Exposure"] = np.sum([portfolio_curves[col] for col in risk_cols], axis=0)
    
        # ===== Two-column layout =====
        col_left, col_spacer, col_right = st.columns([1, 0.2, 1])
    
        # ----- Left: Portfolio Graph -----
        with col_left:
            st.subheader("Portfolio Decay Graph")
            st.write("")  # 1 line
            st.write("")  # 2 lines if needed for alignment
            st.write("")  # 2 lines if needed for alignment
            st.write("")  # 2 lines if needed for alignment
            st.write("")  # 2 lines if needed for alignment
            all_components = list(portfolio_curves.keys())
            selected_components_portfolio = []
            cols_cb = st.columns(3)
            for i, comp in enumerate(all_components):
                with cols_cb[i % 3]:
                    default_state = True if comp == "Total Exposure" else False
                    if st.checkbox(f"Portfolio - {comp}", value=default_state):
                        selected_components_portfolio.append(comp)
    
            fig, ax = plt.subplots(figsize=(8, 5))
            for comp in selected_components_portfolio:
                ax.plot(days, portfolio_curves[comp], label=comp, linewidth=2)
            ax.set_xlabel("Days")
            ax.set_ylabel("Exposure ($)")
            ax.set_title("Portfolio-Level Exposure Decay")
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)
    
        # ----- Right: Merchant Graph -----
        with col_right:
            st.subheader("Merchant Decay Graph")
            # Merchant ID input for right-hand graph
            merchant_id_input = st.text_input("Enter stax_merchant_id for Merchant-Level Graph:")
            if merchant_id_input and merchant_id_input in merchants_df["stax_merchant_id"].values:
                merchant_row = merchants_df[merchants_df["stax_merchant_id"] == merchant_id_input].iloc[0]
                merchant_curves = {}
                for col in risk_cols:
                    hl = merchant_row[hl_map[col]]
                    base_val = merchant_row[col]
                    decay_curve = base_val * (0.5 ** (days / hl)) if hl > 0 else np.zeros_like(days)
                    merchant_curves[col] = decay_curve
                merchant_curves["Total Exposure"] = np.sum([merchant_curves[col] for col in risk_cols], axis=0)
    
                selected_components_merchant = []
                cols_cb_m = st.columns(3)
                for i, comp in enumerate(merchant_curves.keys()):
                    with cols_cb_m[i % 3]:
                        default_state = True if comp == "Total Exposure" else False
                        if st.checkbox(f"Merchant - {comp}", value=default_state):
                            selected_components_merchant.append(comp)
    
                fig2, ax2 = plt.subplots(figsize=(8, 5))
                for comp in selected_components_merchant:
                    ax2.plot(days, merchant_curves[comp], label=comp, linewidth=2)
                ax2.set_xlabel("Days")
                ax2.set_ylabel("Exposure ($)")
                ax2.set_title(f"Exposure Decay for {merchant_id_input}")
                ax2.grid(True)
                ax2.legend()
                st.pyplot(fig2)
            else:
                st.info("Enter a valid stax_merchant_id to see merchant-level decay.")
    
        # ===== Tables =====
        interval_days = np.arange(0, 181, 30)
        agg_table = pd.DataFrame({"Days Since Start": interval_days})
        for comp in all_components:
            agg_table[comp] = [portfolio_curves[comp][day] for day in interval_days]
        for comp in all_components:
            agg_table[comp] = agg_table[comp].apply(lambda x: f"${x:,.2f}")
    
        st.subheader("Portfolio Aggregate Exposure at 30-Day Intervals")
        st.dataframe(agg_table, use_container_width=True)
    
        st.subheader("Portfolio-Level Exposure Decay by Merchant")
        st.dataframe(results_df, use_container_width=True)
    
        csv = results_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Decay Table as CSV",
            data=csv,
            file_name="portfolio_exposure_decay.csv",
            mime="text/csv"
        )
