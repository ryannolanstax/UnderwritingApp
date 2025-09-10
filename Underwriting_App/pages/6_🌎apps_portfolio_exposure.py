#python3 -m streamlit run apps_exposure/test3.py 

#new version with genrated code

import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import altair as alt
import seaborn as sns


# Streamlit App Title
st.title("APPS Exposure & Risk Analysis")

st.write("MCC and Business Models can be found here: https://docs.google.com/spreadsheets/d/1CypTwnuAxxQlFPfLNweo9TYuU9Fv-6WN01kYOYChWEY/edit?gid=0#gid=0")
st.write("Please cleanup Synovous Processing Sheet before uploading, no blank space at the top")

# File Uploads for APPS and MCC Sheets
apps_file = st.file_uploader("Upload APPS Sheet", type=['csv', 'xlsx'])
mcc_file = st.file_uploader("Upload MCC Sheet", type=['csv', 'xlsx'])

# Default month selection to current month
current_month = datetime.now().strftime('%B')
month_options = ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December']
month_selection = st.selectbox("Select Month", month_options, index=month_options.index(current_month))

# Submit Button
submitted = st.button("Submit")

# Only run processing if submit button is clicked
if submitted and apps_file and mcc_file:
    # Convert selected month to days equivalent for calculation
    month_days_mapping = {
        'January': 31, 'February': 59, 'March': 90, 'April': 120, 'May': 151,
        'June': 181, 'July': 212, 'August': 243, 'September': 273,
        'October': 304, 'November': 334, 'December': 365
    }
    days_in_selected_month = month_days_mapping[month_selection]

    # Constants
    refund_days = 30
    chargeback_days = 180

    # Days Processing Calculation Function
    def calculate_days_processing(date_opened):
        current_year = datetime.now().year
        if date_opened.year < current_year:
            return days_in_selected_month
        else:
            days_in_year = (date_opened - datetime(date_opened.year, 1, 1)).days
            return days_in_selected_month - days_in_year

    # Load DataFrames
    apps_df = pd.read_excel(apps_file) if apps_file.name.endswith('.xlsx') else pd.read_csv(apps_file)
    mcc_df = pd.read_excel(mcc_file, sheet_name='MCC Ratings') if mcc_file.name.endswith('.xlsx') else pd.read_csv(mcc_file)

    # Data Filtering and Processing
    apps_df = apps_df[apps_df['Date Closed'].isna()]
    apps_df = apps_df[apps_df['Association'] != 192024]
    apps_df = apps_df[apps_df['YTD Gross Sales Volume'] > 1]
    apps_df['Date Opened'] = pd.to_datetime(apps_df['Date Opened'])
    apps_df['days_processing'] = apps_df['Date Opened'].apply(calculate_days_processing)

    # Calculating Refund and Chargeback Rates
    apps_df['refund_rate'] = apps_df['YTD Credit Volume'] / apps_df['YTD Gross Sales Volume']
    apps_df['chargeback_rate'] = apps_df['YTD Chargeback Volume'] / apps_df['YTD Gross Sales Volume']

    # Merge
    apps_df['MCC'] = apps_df['MCC'].astype(str)
    mcc_df['MCC'] = mcc_df['MCC'].astype(str)
    apps_df['MID'] = apps_df['MID'].astype(str)

    df_merged = apps_df.merge(mcc_df, on='MCC', how='left')
    df_merged['MCC_Risk_Tier'] = df_merged[['AML_Risk_Rating', 'Loss_Risk_Rating']].max(axis=1)

    # Risk Calculations
    df_merged['refund_risk'] = (df_merged['YTD Volume Card-NOT-Present'] / df_merged['days_processing']) * df_merged['refund_rate'] * refund_days
    df_merged['chargeback_risk'] = (df_merged['YTD Volume Card-NOT-Present'] / df_merged['days_processing']) * df_merged['chargeback_rate'] * chargeback_days
    df_merged['cnp_dd_risk'] = (df_merged['YTD Volume Card-NOT-Present'] / df_merged['days_processing']) * df_merged['CNP_DD']
    df_merged['cp_dd_risk'] = (df_merged['YTD Volume Card-Present'] / df_merged['days_processing']) * df_merged['CP_DD']
    df_merged['exposure'] = df_merged['refund_risk'] + df_merged['chargeback_risk'] + df_merged['cnp_dd_risk'] + df_merged['cp_dd_risk']

    total_exposure = df_merged['exposure'].sum()
    max_exposure = df_merged['exposure'].max()

    st.write("Total Exposure: $", f"{total_exposure:,.2f}")
    st.write("Max Exposure: $", f"{max_exposure:,.2f}")

    def categorize_exposure(value):
        if value < 100000:
            return 'under_100k'
        elif 100000 <= value < 500000:
            return 'Range_100k_500k'
        else:
            return 'Range_Over_500k'

    df_merged['exposure_category'] = df_merged['exposure'].apply(categorize_exposure)
    exposure_counts = df_merged.groupby('exposure_category').size().reset_index(name='number_of_merchants')

    # Altair Bar Chart
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=exposure_counts, x='exposure_category', y='number_of_merchants', ax=ax, palette='Blues_d')
    ax.set_title('Exposure Count by Threshold Level', fontsize=16)
    ax.set_xlabel('Exposure Threshold', fontsize=12)
    ax.set_ylabel('Total Merchants', fontsize=12)

    for i, row in exposure_counts.iterrows():
        ax.text(i, row['number_of_merchants'] + 1, f"{int(row['number_of_merchants'])}", ha='center', fontsize=10)

    st.pyplot(fig)

    # Top 10 MCCs
    df_mcc_exposure = df_merged.groupby('MCC')['exposure'].sum().sort_values(ascending=False).head(10).reset_index()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df_mcc_exposure, x='MCC', y='exposure', ax=ax, palette='Blues_d')
    ax.set_title("APPS Top 10 MCCs by Exposure", fontsize=16)
    ax.set_xlabel("MCC", fontsize=12)
    ax.set_ylabel("Total Exposure", fontsize=12)
    ax.tick_params(axis='x', rotation=45)

    for i, v in enumerate(df_mcc_exposure['exposure']):
        ax.text(i, v + df_mcc_exposure['exposure'].max() * 0.02, f"{v:,.0f}", ha='center', fontsize=10)

    st.pyplot(fig)

    # Top 10 Merchants
    top_merchants = df_merged.sort_values(by='exposure', ascending=False).head(10)
    top_merchants_display = top_merchants[['MID', 'Merchant Legal Name', 'MCC', 'MCC_Risk_Tier', 'exposure']]
    top_merchants_display['exposure'] = top_merchants_display['exposure'].map('{:,.0f}'.format)
    st.subheader("Top 10 Merchants by Exposure")
    st.dataframe(top_merchants_display.reset_index(drop=True))

    # Count by Risk Tier
    tier_counts = df_merged['MCC_Risk_Tier'].value_counts().sort_index().reset_index()
    tier_counts.columns = ['MCC_Risk_Tier', 'count']

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=tier_counts, x='MCC_Risk_Tier', y='count', ax=ax, palette='Oranges_d')
    ax.set_title("APPS Merchant Count by MCC Risk Tier", fontsize=16)
    ax.set_xlabel("MCC Risk Tier", fontsize=12)
    ax.set_ylabel("Number of Merchants", fontsize=12)

    for i, v in enumerate(tier_counts['count']):
        ax.text(i, v + 1, str(v), ha='center', fontsize=10)

    st.pyplot(fig)

    # File Download
    st.write("Download the processed data:")
    df_merged.to_excel("APPS_Exposure.xlsx", index=False)
    st.download_button(
        label="Download APPS Exposure Data",
        data=open("APPS_Exposure.xlsx", "rb").read(),
        file_name="APPS_Exposure.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
