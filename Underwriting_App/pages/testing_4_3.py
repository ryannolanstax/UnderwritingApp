# python3 -m streamlit run Underwriting_App/pages/calc_3_25_2024_updates.py 

import altair as alt
import pandas as pd
import seaborn as sns
import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import numpy as np
import datetime
from datetime import date, timedelta
import io
import matplotlib.pyplot as plt  


#set default max dd
#5% default refund rate
#0.5% default chargeback rate

st.set_page_config(page_title="Underwriting Calculator", page_icon="💾", layout="wide")

st.title("Underwriting and Risk Calculator")
st.markdown("This New Calculator Combines the older Tiering + Exposure Calculators")
st.markdown("Having Issues or Ideas to improve the APP? Reach out to Ryan Nolan")

st.header('Exposure Fields')

delayed = pd.read_csv('Underwriting_App/MCC & Business Models - MCC Ratings_Sales.csv')

MCC = st.number_input("MCC", key='MCC', value=1711)

CNP_DD = delayed.loc[delayed['MCC'] == MCC, ['CNP Delayed Delivery']].iloc[0, 0]
CP_DD = delayed.loc[delayed['MCC'] == MCC, ['CP/ACH Delayed Delivery']].iloc[0, 0]
ACH_DD = delayed.loc[delayed['MCC'] == MCC, ['CP/ACH Delayed Delivery']].iloc[0, 0]



#max_cnp_cp_dd = max(CNP_DD, CP_ACH_DD) TEMP PAUSE

AML_Risk_Rating = delayed.loc[delayed['MCC'] == MCC, ['AML Risk Rating']].iloc[0, 0]
Loss_Risk_Rating = delayed.loc[delayed['MCC'] == MCC, ['Loss Risk Rating']].iloc[0, 0]

mcc_risk = max(AML_Risk_Rating, Loss_Risk_Rating)

Annual_CNP_Volume = st.number_input("Annual CNP Volume ($)", key="Annual_CNP_Volume")
#Annual_CP_ACH_Volume = st.number_input("Annual CP/ACH Volume ($)", key="Annual_CP_ACH_Volume") OLD
Annual_CP_Volume = st.number_input("Annual CP Volume ($)", key="Annual_CP_Volume")
Annual_ACH_Volume = st.number_input("Annual ACH Volume ($)", key="Annual_ACH_Volume")


#old refund rate field
#Refund_Rate = st.number_input("Refund Rate (%)", value=3.0, key="Refund_Rate", step=0.1, format="%0.1f")
Refund_Rate = 0.05
Refund_Days = st.number_input("Refund Days (#) #Default 30 ie. If official 90 day return policy for online sales, Use 90", value=30, key="Refund_Days")

#old chargeback rate field
#Chargeback_Rate = st.number_input("'Chargeback Rate (%)", value=0.5, key="Chargeback_Rate", step=0.1, format="%0.1f")
Chargeback_Rate = 0.005
Chargeback_Days = 180

#ACH_Reject_Rate = st.number_input('ACH Reject (%)',min_value=0.0, max_value=100.0, key='ACH_Reject_Rate')
ACH_Reject_Rate = 0.005
#ACH_Reject_Days = st.number_input("ACH Reject Days (#)", key='ACH_Reject_Days', value=5)

my_expander = st.expander(label='Delayed Delivery Calcs')

st.write('Delayed Delivery Calcs')

data = {
        'Terms': ['Annual', 'Monthly', 'One-time', 'Arrears payment', 'Other', 'Other'],
        'DD': [15, 1, 0, 0, 0, 0],
        'Vol': [20, 80, 0, 0, 0, 0],
}

df_original = pd.DataFrame(data)
edited_df = st.data_editor(df_original)

#CP_ACH_DD

#TEMP REMOVE CALCULATOR
#max_dd = max_cnp_cp_dd  # Default value for max_dd

#def calculate_results(df):
#    weighted_avg_DD = (df['DD'] * df['Vol']).sum() / df['Vol'].sum()
#    volume = df['Vol'].sum()
    
#    if weighted_avg_DD:
#        weighted_avg_DD = float(weighted_avg_DD)
    
#    max_dd = max(weighted_avg_DD, max_cnp_cp_dd)
    
#    return weighted_avg_DD, volume, max_dd

#if st.button("Calculate"):
#    weighted_avg_DD, volume, max_dd = calculate_results(edited_df)
    
#    st.write('Calculated Results:')
#    st.write(f'Weighted Average DD: {weighted_avg_DD}')
#    st.write(f'Total Volume: {volume}')
#    st.write(f'Max DD: {max_dd}')

# Now max_dd is defined outside the "Calculate" block and can be used as a default value in st.number_input
#Delayed_Delivery = st.number_input("Delayed Delivery (DD)", key='Delayed_Delivery', value=max_dd)

#temp fix
CNP_Delayed_Delivey = st.number_input("CNP Delayed Delivery (DD)", key='CNP_Delayed_Delivery', value=CNP_DD)
CP_Delayed_delivery = st.number_input("CP Delayed Delivery (DD)", key='CP_Delayed_Delivery', value=CP_DD)
ACH_Delayed_Delivery = st.number_input("ACH Delayed Delivery (DD)", key='ACH_Delayed_Delivery', value=ACH_DD)


#Calculations Section Exposure
Refund_Risk = (Annual_CNP_Volume/365) * Refund_Rate * Refund_Days 
Chargeback_Risk = (Annual_CNP_Volume/365) * Chargeback_Rate * Chargeback_Days 
CNP_DD_Risk = (Annual_CNP_Volume/365) * CNP_Delayed_Delivey 

CP_Reject_Exposure = (Annual_CP_Volume/365)*CP_Delayed_delivery
#ACH_New_Reject_Exposure = (Annual_ACH_Volume/365)*ACH_Reject_Rate*ACH_Reject_Days
ACH_New_Reject_Exposure = (Annual_ACH_Volume/365)*ACH_Reject_Rate*ACH_Delayed_Delivery



#ACH_Reject_Exposure = ((Annual_CP_ACH_Volume/365)*Delayed_Delivery) + ((Annual_CP_ACH_Volume/365)*ACH_Reject_Rate*ACH_Reject_Days)


Total_Volume = Annual_CNP_Volume + Annual_ACH_Volume + Annual_CP_Volume
Total_Exposure = Refund_Risk + Chargeback_Risk + CNP_DD_Risk + CP_Reject_Exposure + ACH_New_Reject_Exposure

formatted_exposure = "${:,.0f}".format(Total_Exposure)
st.write('The Final Exposure of the Customer is:', formatted_exposure)

formatted_exposure50 = "${:,.0f}".format(Total_Exposure * 0.5)
formatted_exposure60 = "${:,.0f}".format(Total_Exposure *  0.6)

st.write('60% of The Final Exposure of the Customer is:', formatted_exposure60)
st.write('50% of The Final Exposure of the Customer is:', formatted_exposure50)

st.header('Tiering Fields')

Fulfillment = max(CNP_Delayed_Delivey, CP_Delayed_delivery, ACH_Delayed_Delivery)


exposure_mapping = {
    'Merchant refuses to provide current bank statements OR merchant’s current bank statements show negative balances and recent NSFs': 5,
    'Merchant provided current bank statements that show no negative balances or NSFs; however, the average balances would not cover the high ticket and/or volumes would not support 50% or more of the exposure amount': 4,
    'Waiver OR Merchant provided current bank statements that cover approved high ticket and at least 50% of exposure amount': 3,
    'Merchant provided current bank statements that cover 2x approved high ticket and at least 60% of exposure amount': 2,
    'Low Risk Not Required OR Merchant provided current bank statements that cover at least 3x approved high ticket and entirety of exposure amount': 1
}

ExposureCoverage = st.radio('Can the Business Cover Exposure?', options=list(exposure_mapping.keys()), horizontal=True)

ExposureCoverage_integer = exposure_mapping[ExposureCoverage]


SignerCreditScore_mapping = {
            '<550': 5,
            '551-579 or Unknown': 4,
            '580-650': 3,
            '651-750': 2,
            '751-850': 1,
}

SignerCreditScore = st.radio('What is the signers credit score?', options=list(SignerCreditScore_mapping.keys()), horizontal=True)

SignerCreditScore_integer = SignerCreditScore_mapping[SignerCreditScore]


age_mapping = {
    'Less than 6 months': 5,
    '6 months to 1 year': 4,
    '1 year to 3 years': 3,
    '3 years to 5 years': 2,
    '>5 years': 1
}

# Display radio button and get user input
business_age = st.radio('How old is the business?', options=list(age_mapping.keys()), horizontal=True)

# Convert selected value to integer using the mapping
business_age_integer = age_mapping[business_age]



st.write('**CB Rate:** Merchants chargeback rate over the last 180 days')
st.write('**Refund Rate:** Merchants chargeback rate over the last 90 days')
st.write('**ACH Reversal Rate:** ACH reversal rate in the last 30 days')
st.write('**Unauth Return Codes:** R05, R07, R08, R10, R29, R51')

link = "https://www.vericheck.com/ach-return-codes/#:~:text=R08,be%20a%20revocation%20of%20authorization"
text = "All Return Codes with Detail Info"
st.markdown(f"[{text}]({link})")

###Simplified
chargeback_refund_mapping = {
    'CB Rate **>= 2%** OR Refund Rate **>= 10%** OR ACH Reversal Rate **>= 0.5%** for Unauth Return Codes OR **>=10% and <15%** for All Return Codes.': 5,
    'CB Rate **>= 1%** AND < 2%** OR Refund Rate **>= 7.5% AND < 10%** OR ACH Reversal Rate **>= 0.4%** for Unauth Return Codes OR **>= 10% AND < 15%** for All Return Codes.': 4,
    'CB Rate **>= 0.75% AND < 1%** OR Refund Rate **>= 5% AND < 7.5%** OR ACH Reversal Rate **>= 0.3%** for Unauth Return Codes OR  **>= 7.5% AND < 10%** for All Return Codes.': 3,
    'CB Rate **>= 0.05% AND < 0.75%** OR Refund Rate **>= 3% AND < 5%** OR ACH Reversal Rate **>= 0.2%** for Unauth Return Codes OR  **>= 5% AND < 7.5%** for All Return Codes.': 2,
    'Not Needed OR CB Rate **< 0.05%** OR Refund Rate **< 3%** OR ACH Reversal Rate **< 0.2%** for Unauth Return Codes OR **< 5%** for All Return Codes.': 1,
}

chargeback_refund = st.radio('What is the customers business processing and banking history?', options=list(chargeback_refund_mapping.keys()), horizontal=True)

chargeback_refund_integer = chargeback_refund_mapping[chargeback_refund]





AvgReview_mapping = {
            '>3.8': 4,
            '3.8 - 4.2 or Under 10 Reviews': 3,
            '4.2 - 4.5': 2,
            '4.5<': 1,
}

AvgReview = st.radio('What is the business average review score across all review platforms?', options=list(AvgReview_mapping.keys()), horizontal=True)

AvgReview_integer = AvgReview_mapping[AvgReview]


#####



if  Fulfillment >= 24:
    fullfillment_int = 5

elif Fulfillment >= 31:
    fullfillment_int = 4

elif Fulfillment >= 16:
    fullfillment_int = 3

elif Fulfillment >= 6:
    fullfillment_int = 2

else: fullfillment_int = 1

#Calculations Section Tier
total_score = business_age_integer + ExposureCoverage_integer + chargeback_refund_integer + AvgReview_integer + SignerCreditScore_integer + fullfillment_int


if  total_score > 24 \
    or chargeback_refund_integer == 5 \
    or SignerCreditScore_integer == 5:
    final_score = 5

elif total_score > 20 \
    or chargeback_refund_integer == 4 \
    or SignerCreditScore_integer == 4:
    final_score = 4

elif total_score > 15:
    final_score = 3

elif total_score > 10:
    final_score = 2

else:
    final_score = 1

st.header('Final Results')





st.write('The Final Exposure of the Customer is:', formatted_exposure)

st.write('The Final Tier of the Customer is: ', final_score)

st.subheader("Exposure Calculations")

st.write('Refund_Risk:', Refund_Risk)
st.write('Chargeback_Risk:', Chargeback_Risk)
st.write('CNP_DD_Risk:', CNP_DD_Risk)
st.write('ACH_Reject_Exposure:', ACH_New_Reject_Exposure)
st.write('CP_Reject_Exposure:', CP_Reject_Exposure)

st.subheader("Risk Tier Calculations")


st.write("Based on the form fields above and MCC DD the total amount of points the merchant had was: ", total_score)

data = {
    'Risk_Tier': [5,4,3,2,1],
    'Reason for Tier': ['total_score> 24 OR Chargeback Refund Risk = 5 OR Credit Score Risk = 5', 'total_score > 20 OR Chargeback Refund Risk = 4 OR Credit Score Risk = 4', 'total_score > 15', 'total_score > 10', 'total_score > 0'],
}

# Create DataFrame
df = pd.DataFrame(data)

# Ensure index is dropped
df = df.reset_index(drop=True)

# Display table using Streamlit
st.write(df)

st.write('The Total Score of the Customer is: ', total_score)

st.write('Business Age:', business_age_integer, 'Exposure:', ExposureCoverage_integer, 'Chargeback Refund:', chargeback_refund_integer, 'Avg Review:', AvgReview_integer, 'Credit Score:', SignerCreditScore_integer, 'Fullfillment:', fullfillment_int)

