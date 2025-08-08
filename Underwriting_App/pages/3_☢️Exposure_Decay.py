import pandas as pd
import numpy as np
import datetime
import streamlit as st
import matplotlib.pyplot as plt


st.set_page_config(page_title="Exposure Decay", page_icon="☢️", layout="wide")

# Function to calculate row-wise half-life based on cb_rate and refund_rate
def calculate_half_life(row):
    cb = row['cb_rate']
    refund = row['refund_rate']

    # CB half-life
    if cb <= 0.05:
        cb_life = 30
    elif cb <= 0.11:
        cb_life = 40
    elif cb <= 0.19:
        cb_life = 50
    else:
        cb_life = 60

    # Refund half-life
    if refund <= 3:
        refund_life = 30
    elif refund <= 6:
        refund_life = 40
    elif refund <= 10:
        refund_life = 50
    else:
        refund_life = 60

    # Choose stricter (larger) half-life
    return max(cb_life, refund_life)




st.title("Exposure Decay Calc Last Updated 8/6/25")
st.markdown("This New Calculator Looks at Decaying Exposure for Merchants in a Partner")
st.markdown("Having Issues or Ideas to improve the APP? Reach out to Ryan Nolan")


col1, col2 = st.columns(2)

with col1:

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



with col2:

    st.header("Exposure Decay for Different Half-Lives")

    # Initial exposure
    initial_exposure = 10000
    time_range = np.arange(0, 181, 5)  # 0 to 180 days, step of 5
    half_lives = [30, 40, 50, 60]

    # Create decay curves
    fig, ax = plt.subplots(figsize=(5, 3))  # Width=5 inches, Height=3 inches

    for hl in half_lives:
        lambda_ = np.log(2) / hl
        decay = initial_exposure * np.exp(-lambda_ * time_range)
        ax.plot(time_range, decay, label=f'Half-Life {hl} days')

    # Formatting
    ax.set_title("Exponential Decay of $10,000 Exposure")
    ax.set_xlabel("Days")
    ax.set_ylabel("Exposure ($)")
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)


st.header('File Upload Section')


st.write("Merchants Query can be found here: https://app.mode.com/editor/fattmerchant/reports/51bead101fb5/queries/1e8a80ded27a")

merchants = st.file_uploader("Upload Merchant Spreadsheet", type=['csv', 'xlsx'])



if merchants is not None:
    merchants_df = pd.read_csv(merchants)

    # List of decay days
    decay_days = [30, 60, 90, 120, 150, 180]

    # Define a half-life (or pick lambda directly)
    #half_life = 30  # This is just an example, change it if needed
    merchants_df['half_life'] = merchants_df.apply(calculate_half_life, axis=1)
    merchants_df['lambda'] = np.log(2) / merchants_df['half_life']

    for t in decay_days:
        merchants_df[f'decay_exposure_{t}d'] = merchants_df['exposure_180'] * np.exp(-merchants_df['lambda'] * t)


    #merchants_df = merchants_df.drop(columns=['refund_rate', 'cb_rate'])

    currency_cols = ['exposure_180'] + ['last_180_vol] + [f'decay_exposure_{t}d' for t in decay_days]
    merchants_df[currency_cols] = merchants_df[currency_cols].applymap(lambda x: f"${x:,.2f}")

    # Show the result
    st.dataframe(merchants_df, use_container_width=True)

    csv = merchants_df.to_csv(index=False)
    
    # Create download button
    st.download_button(
        label="📥 Download as CSV",
        data=csv,
        file_name="merchants.csv",
        mime="text/csv",
    )

