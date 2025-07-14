# python3 -m streamlit run Underwriting_App/pages/calc_2025.py 
#last Updated Beginning of July

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

st.title("Underwriting and Risk Calculator 7/11/25 Updates")
st.markdown("This New Calculator Combines the older Tiering + Exposure Calculators")
st.markdown("Having Issues or Ideas to improve the APP? Reach out to Ryan Nolan")

st.header('Exposure Fields')

delayed = pd.read_csv('Underwriting_App/MCC & Business Models - MCC Ratings_Sales.csv')


#Prohibited Business Models
prohibited_business_models = [
    *range(3351, 3441), 4411, 4511, 4814, 4829, 4899, 5051, 5099, 5499, 5692,
    5698, 5941, 5947, 5963, 5964, 5966, 5967, 5968, 5993, 5995, 5999, 6012,
    6051, 6211, 6300, 6538, 6540, 7012, 7277, 7299, 7311, 7322, 7379, 7399,
    7800, 7801, 7802, 7994, 7995, 8099, 8211, 8398, 8651, 8999, 9399, 9754
]



#Restricted Business Models
restricted_business_models = [
1799, 4111, 4121, 4214, 4722, 4900, 5051, 5122, 5262, 5499, 5816, 5912, 5921,
5933, 5935, 5937, 5968, 5972, 5993, 5999, 6010, 6012, 6051, 6211, 6300, 7273,
7321, 7394, 7399, 7922, 7999, 8011, 8071, 8099, 8398, 8641, 9111
]



amex_banned = [
    *range(3000, 3303),  # 3000–3302
    9223,
    5094,
    *range(3351, 3442),  # 3351–3441
    6051,
    7322,
    6010, 6011, 6012, 6051,
    7322,
    5963,
    6051,
    7800, 7802, 7995, 9406,
    6211,
    *range(3501, 4000),  # 3501–3999
    5966, 5967,
    6538,
    9402,
    6012, 6051,
    4411,
    5962,
    7012,
    6051,
    4829
]



no_amex_threshold  = [
    # Charity
    8398,
    8661,

    # Education
    7032,
    7911,
    8211,
    8220,
    8241,
    8244,
    8249,
    8299,
    8351,

    # Government
    9211,
    9222,
    9311,
    9399,

    # Healthcare
    742,
    4119,
    8011,
    8021,
    8031,
    8041,
    8042,
    8043,
    8049,
    8050,
    8062,
    8071,
    8099,

    # Insurance
    6300,

    # Online Gambling
    7801,

    # Residential Rent
    6513,

    # Utilities
    4900
]


MCC = st.number_input("MCC", key='MCC', value=1711)

if MCC == 8099:
    st.error("Prohibited: If 8099,  Home-based massage business without valid license OR Human Growth Hormone OR Male / female sexual enhancements not FDA approved OR Synthetic drugs / substances designed to mimic illegal drugs" \
    "\n RESTRICTED Cannabis-related or adjacent merchant (cannabis related business/marijuana related business crb/mrb) such as Doctors approving prescriptions OR Ketamine including retreats, therapy, treatment etc. OR Hormone Replacement Therapy OR IV Therapy OR Medical Weight Loss / Semaglutides"
     )

if MCC == 8011:
    st.error("RESTRICTED:  Telehealth / Telemedicine ( if the user can receive a prescription)")


if MCC in prohibited_business_models:
    st.error("MCC is in Prohibited Business Models Talk to Manager if this is incorrect")

if MCC  in restricted_business_models:
    st.error("MCC is in Restricted Business Models Talk to Manager if this is incorrect")

if MCC  in amex_banned:
    st.error("MCC code not allowed by AMEX")

if MCC  in no_amex_threshold:
    st.error("No Amex Threshold")


CNP_DD = delayed.loc[delayed['MCC'] == MCC, ['CNP Delayed Delivery']].iloc[0, 0]
CP_DD = delayed.loc[delayed['MCC'] == MCC, ['CP/ACH Delayed Delivery']].iloc[0, 0]
ACH_DD = delayed.loc[delayed['MCC'] == MCC, ['CP/ACH Delayed Delivery']].iloc[0, 0]
ACH_DD = min(ACH_DD, 60)



#max_cnp_cp_dd = max(CNP_DD, CP_ACH_DD) TEMP PAUSE

AML_Risk_Rating = delayed.loc[delayed['MCC'] == MCC, ['AML Risk Rating']].iloc[0, 0]
Loss_Risk_Rating = delayed.loc[delayed['MCC'] == MCC, ['Loss Risk Rating']].iloc[0, 0]

mcc_risk = max(AML_Risk_Rating, Loss_Risk_Rating)

st.write('**Underwriters** Stax Connect has possible data issues with CNP and CP not being accurate from partners. Use data for on the partner sheet for the processing percentage')
Annual_CNP_Volume = st.number_input("Annual CNP Volume ($)", key="Annual_CNP_Volume", step=1)
#Annual_CP_ACH_Volume = st.number_input("Annual CP/ACH Volume ($)", key="Annual_CP_ACH_Volume") OLD
Annual_CP_Volume = st.number_input("Annual CP Volume ($)", key="Annual_CP_Volume", step=1)

if (Annual_CNP_Volume + Annual_CP_Volume > 20000000):
    st.warning('SYNOVUS Underwriting Needed based on Volume!!! Use the Synovus Exposure Calculator Also!!!', icon="⚠️")


Annual_ACH_Volume = st.number_input("Annual ACH Volume ($)", key="Annual_ACH_Volume", step=1)






#old refund rate field
#Refund_Rate = st.number_input("Refund Rate (%)", value=3.0, key="Refund_Rate", step=0.1, format="%0.1f")
#Refund_Rate = 0.05
Refund_Rate = st.number_input("Refund Rate", key="Refund_Rate", value=0.05)


Refund_Days = st.number_input("Refund Days (#) #Default 30 ie. If official 90 day return policy for online sales, Use 90", value=30, key="Refund_Days")

#old chargeback rate field
#Chargeback_Rate = st.number_input("'Chargeback Rate (%)", value=0.5, key="Chargeback_Rate", step=0.1, format="%0.1f")
#Chargeback_Rate = 0.005
step_size = 0.001

Chargeback_Rate = st.number_input("Chargeback Rate", key="Chargeback_Rate", value=0.005, step=step_size, format="%f")


Chargeback_Days = 180

#ACH_Reject_Rate = st.number_input('ACH Reject (%)',min_value=0.0, max_value=100.0, key='ACH_Reject_Rate')
ACH_Reject_Rate = 0.005
ACH_Reject_Days = 5

my_expander = st.expander(label='Delayed Delivery Calcs')

st.write('Delayed Delivery Calcs')

data = {
        'Terms': ['Annual', 'Monthly', 'One-time', 'Arrears payment', 'Other', 'Other'],
        'DD': [15, 1, 0, 0, 0, 0],
        'Vol': [20, 80, 0, 0, 0, 0],
}

df_original = pd.DataFrame(data)
edited_df = st.data_editor(df_original)

def calculate_results(df):
    weighted_avg_DD = (df['DD'] * df['Vol']).sum() / df['Vol'].sum()
    volume = df['Vol'].sum()
    
    if weighted_avg_DD:
        weighted_avg_DD = float(weighted_avg_DD)
    
    return weighted_avg_DD, volume

if st.button("Calculate"):
    weighted_avg_DD, volume = calculate_results(edited_df) 
    st.write('Calculated Results:')
    st.write(f'Weighted Average DD: {weighted_avg_DD}')
    st.write(f'Total Volume: {volume}')


# Now max_dd is defined outside the "Calculate" block and can be used as a default value in st.number_input
#Delayed_Delivery = st.number_input("Delayed Delivery (DD)", key='Delayed_Delivery', value=max_dd)

#temp fix
CNP_Delayed_Delivey = st.number_input("CNP Delayed Delivery (DD)", key='CNP_Delayed_Delivery', value=CNP_DD)
CP_Delayed_delivery = st.number_input("CP Delayed Delivery (DD)", key='CP_Delayed_Delivery', value=CP_DD)
st.write("The MAX ACH DD is 60 Days. This is due to (WRITE MORE INFO HERE)")
ACH_Delayed_Delivery = st.number_input("ACH Delayed Delivery (DD)", key='ACH_Delayed_Delivery', value=ACH_DD, max_value=60)


#Calculations Section Exposure
Refund_Risk = (Annual_CNP_Volume/365) * Refund_Rate * Refund_Days 
Chargeback_Risk = (Annual_CNP_Volume/365) * Chargeback_Rate * Chargeback_Days 
CNP_DD_Risk = (Annual_CNP_Volume/365) * CNP_Delayed_Delivey 
CP_DD_Risk = (Annual_CP_Volume/365)*CP_Delayed_delivery
ACH_New_Reject_Exposure = (Annual_ACH_Volume/365) * ACH_Reject_Rate * ACH_Reject_Days
ACH_DD_Risk = (Annual_ACH_Volume/365)*ACH_Delayed_Delivery


#ACH_Reject_Exposure = ((Annual_CP_ACH_Volume/365)*Delayed_Delivery) + ((Annual_CP_ACH_Volume/365)*ACH_Reject_Rate*ACH_Reject_Days)

Total_Volume = Annual_CNP_Volume + Annual_ACH_Volume + Annual_CP_Volume
Total_Exposure = Refund_Risk + Chargeback_Risk + CNP_DD_Risk + CP_DD_Risk + ACH_New_Reject_Exposure + ACH_DD_Risk

formatted_exposure = "${:,.0f}".format(Total_Exposure)
st.write('The Final Exposure of the Customer is:', formatted_exposure)


if (Refund_Risk + Chargeback_Risk + CNP_DD_Risk + CP_DD_Risk > 2000000):
    st.warning('SYNOVUS Underwriting Potentially Needed Based on Card Exposure!!! Use the Synovus Exposure Calculator Also!!!', icon="⚠️")


formatted_exposure50 = "${:,.0f}".format(Total_Exposure * 0.5)
formatted_exposure60 = "${:,.0f}".format(Total_Exposure *  0.6)

st.write('60% of The Final Exposure of the Customer is:', formatted_exposure60)
st.write('50% of The Final Exposure of the Customer is:', formatted_exposure50)

st.header('Tiering Fields')

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
            'Under 550': 5,
            '551-579': 4,
            '580-650 or Unknown': 3,
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
    '5+ years': 1
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
            'Under 3.8': 4,
            '3.8 - 4.2 or Under 10 Reviews': 3,
            '4.2 - 4.5': 2,
            'Over 4.5': 1,
}

AvgReview = st.radio('What is the business average review score across all review platforms?', options=list(AvgReview_mapping.keys()), horizontal=True)

AvgReview_integer = AvgReview_mapping[AvgReview]


#Calculations Section Tier
total_score = business_age_integer + ExposureCoverage_integer + chargeback_refund_integer + AvgReview_integer + SignerCreditScore_integer 

if  total_score >= 21 \
    or chargeback_refund_integer == 5 \
    or SignerCreditScore_integer == 5 \
    or exposure_mapping == 5:
    final_score = 5

elif total_score >= 16 \
    or chargeback_refund_integer == 4 \
    or SignerCreditScore_integer == 4 \
    or exposure_mapping == 4 \
    or mcc_risk == 5 \
    or business_age_integer > 3:
    final_score = 4

elif total_score >= 8:
    final_score = 3

elif total_score >= 6 \
    or mcc_risk == 4: 
    final_score = 2

else:
    final_score = 1

st.header('Final Results')

#Business age 4/5 and Reviews is 3/4
#4/3 -> Risk Tier 4
#4/4
#5/3
#5/4

#two 2s - >2
#two 3s -> 3
#two 4s -> 4
#twp 5s ->5

#business under a year 

st.write('The Final Exposure of the Customer is:', formatted_exposure)

st.write('The Final Tier of the Customer is: ', final_score)

st.subheader("Exposure Calculations")

st.write('Refund_Risk:', Refund_Risk)
st.write('Chargeback_Risk:', Chargeback_Risk)
st.write('ACH_Reject_Risk:', ACH_New_Reject_Exposure)
st.write('CNP_DD_Risk:', CNP_DD_Risk)
st.write('CP_DD_Risk:', CP_DD_Risk)
st.write('ACH_DD_Risk:', ACH_DD_Risk)

st.subheader("Risk Tier Calculations")

st.write("Based on the form fields above and MCC DD the total amount of points the merchant had was: ", total_score)

st.caption('Tier 5: total_score >= 21 OR Chargeback Refund Risk = 5 OR Credit Score Risk = 5 OR Exposure Risk = 5')
st.caption('Tier 4: total_score >= 16 OR Chargeback Refund Risk = 4 OR Credit Score Risk = 4 OR Exposure Risk = 4 or Business Age = 4/5 or MCC Risk Tier = 5')
st.caption('Tier 3: total_score >= 8')
st.caption('Tier 2: total_score >= 6 OR MCC Risk Tier = 4')
st.caption('Tier 1: total_score >= 0')

st.write('The Total Score of the Customer is: ', total_score)

st.write('Business Age:', business_age_integer, 'Exposure:', ExposureCoverage_integer, 'Chargeback Refund:', chargeback_refund_integer, 'Avg Review:', AvgReview_integer, 'Credit Score:', SignerCreditScore_integer, 'MCC Risk:', mcc_risk)
