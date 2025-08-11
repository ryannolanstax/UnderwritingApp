import pandas as pd
import numpy as np
import datetime
import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import io

st.set_page_config(page_title="Individual Merchant Decay", page_icon="☣️", layout="wide")

st.header('Individual Exposure Decay')

st.write("Merchants Query can be found here: https://app.mode.com/editor/fattmerchant/reports/49e3c5343375/queries/3c59a638ce08")

with st.expander("Half Life Rules 8/11"):
    st.write("CNP/CP/ACH DD Half Life = Default or Merchant DD Value in Database")
    st.write("ACH Half Life = 5 Days")

    cb_half_life = {
        "≤ 5%": 30,
        "6–11%": 40,
        "12–19%": 50,
        "≥ 20%": 60
    }

    refund_half_life = {
        "≤ 3%": 30,
        "4–6%": 40,
        "7–10%": 50,
        "≥ 11%": 60
    }

    # Convert to DataFrame
    cb_df = pd.DataFrame({
        "Rate Type": ["Chargeback Rate"] * 4,
        "Rate Range": list(cb_half_life.keys()),
        "Half Life (days)": list(cb_half_life.values())
    })

    refund_df = pd.DataFrame({
        "Rate Type": ["Refund Rate"] * 4,
        "Rate Range": list(refund_half_life.keys()),
        "Half Life (days)": list(refund_half_life.values())
    })

    # Combine into one table
    combined_df = pd.concat([cb_df, refund_df], ignore_index=True)

    # Display in Streamlit
    st.header("Half-Life Table Based on Refund or Chargeback Rate")
    st.table(combined_df)






# Risk columns graph
risk_cols = [
    "refund_risk",
    "chargeback_risk",
    "cnp_dd_risk",
    "cp_dd_risk",
    "ach_new_reject_exposure",
    "ach_dd_risk"
]

def calculate_chargeback_risk_value(cb):
    if cb <= 0.05:
        return 30
    elif cb <= 0.11:
        return 40
    elif cb <= 0.19:
        return 50
    else:
        return 60

def calculate_refund_risk_value(refund):
    if refund <= 3:
        return 30
    elif refund <= 6:
        return 40
    elif refund <= 10:
        return 50
    else:
        return 60

transactions_merchant = st.file_uploader("Upload Merchant Spreadsheet", type=['csv', 'xlsx'])

if transactions_merchant is not None:
    transaction_df = pd.read_csv(transactions_merchant)

    transaction_df['chargeback_risk_value'] = transaction_df['chargeback_risk'].apply(calculate_chargeback_risk_value)
    transaction_df['refund_risk_value'] = transaction_df['refund_risk'].apply(calculate_refund_risk_value)
    transaction_df['ach_risk_value'] = 5  # Static or placeholder value

    col1, spacer, col2 = st.columns([3, 1, 5])  # spacer column smaller width

    with col1:
        st.subheader("Half-Life Settings (Days)")
        half_life_days = {}

        half_life_days["refund_risk"] = st.slider(
            "refund_risk",
            min_value=0,
            max_value=180,
            value=int(transaction_df['refund_risk_value'].iloc[0])
        )
        half_life_days["chargeback_risk"] = st.slider(
            "chargeback_risk",
            min_value=0,
            max_value=180,
            value=int(transaction_df['chargeback_risk_value'].iloc[0])
        )
        half_life_days["cnp_dd_risk"] = st.slider(
            "cnp_dd_risk",
            min_value=0,
            max_value=365,
            value=int(transaction_df['dd_cnp'].iloc[0])
        )
        half_life_days["cp_dd_risk"] = st.slider(
            "cp_dd_risk",
            min_value=0,
            max_value=365,
            value=int(transaction_df['dd_cp'].iloc[0])
        )
        half_life_days["ach_new_reject_exposure"] = st.slider(
            "ach_new_reject_exposure",
            min_value=0,
            max_value=180,
            value=int(transaction_df['ach_risk_value'].iloc[0])
        )
        half_life_days["ach_dd_risk"] = st.slider(
            "ach_dd_risk",
            min_value=0,
            max_value=365,
            value=int(transaction_df['dd_ach'].iloc[0])
        )

    with col2:
        st.subheader("Select Components to Plot")

        show_cols = {}
        # Arrange options: Total Exposure first, then the rest
        options = risk_cols + ["Total Exposure"]

        # Create 3 columns for checkboxes
        num_cols = 3
        cols_grid = st.columns(num_cols)

        # Calculate chunk size to distribute evenly
        chunk_size = (len(options) + num_cols - 1) // num_cols

        for i, col_box in enumerate(cols_grid):
            with col_box:
                for opt in options[i * chunk_size : (i + 1) * chunk_size]:
                    default_val = True if opt == "Total Exposure" else False
                    show_cols[opt] = st.checkbox(opt, value=default_val)

        # Compute decay curves
        days = np.arange(0, 181)  # 0 to 180 days
        decay_curves = {}

        for col in risk_cols:
            base_value = transaction_df[col].iloc[0]
            hl = half_life_days[col]
            if hl > 0:
                decay_curves[col] = base_value * (0.5 ** (days / hl))
            else:
                decay_curves[col] = np.zeros_like(days)

        # Total exposure
        decay_curves["Total Exposure"] = np.sum(list(decay_curves.values()), axis=0)

        # Create a dictionary for easy day-to-exposure lookup
        total_exposure_over_time = {int(day): exposure for day, exposure in zip(days, decay_curves["Total Exposure"])}

        # Plot selected curves
        fig, ax = plt.subplots()
        for col_name, show in show_cols.items():
            if show:
                ax.plot(days, decay_curves[col_name], label=col_name, linewidth=2)

        ax.set_xlabel("Days")
        ax.set_ylabel("Exposure")
        ax.set_title("Exposure Decay")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

    # ---- Exposure table every 30 days ----
    interval_days = np.arange(0, 181, 30)
    last_txn_date = pd.to_datetime(transaction_df["last_transaction_day"].iloc[0])

    exposure_table = pd.DataFrame({
        "Date": [last_txn_date + timedelta(days=int(d)) for d in interval_days],
        "Days Since Last Transaction": interval_days,
        "Total Exposure": [total_exposure_over_time[d] for d in interval_days]
    })

    exposure_table['Total Exposure $'] = exposure_table['Total Exposure'].apply(lambda x: f"${x:,.2f}")


    st.subheader("Exposure at 30-Day Intervals")
    st.write('Starting Date of Exposure is Day of Last Transaction')
    st.dataframe(exposure_table.drop(columns=['Total Exposure']), use_container_width=True)
