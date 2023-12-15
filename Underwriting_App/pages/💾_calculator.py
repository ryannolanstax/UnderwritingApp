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

st.title("Underwriting Calculator")
st.markdown("This New Calculator Combines the older Tiering + Exposure Calculators")

#No Downloading for now
#filename = st.text_input("Filename (must include merchant name + deal id)", key="filename")

#buffer = io.BytesIO()

st.header('Exposure Fields')

delayed = pd.read_csv('Underwriting_App/MCC & Business Models - MCC Ratings_Sales.csv')

MCC = st.number_input("MCC", key='MCC', value=1711)

testing = delayed.loc[delayed['MCC'] == MCC, ['CNP Delayed Delivery']].iloc[0, 0]

CNP_DD = delayed.loc[delayed['MCC'] == MCC, ['CNP Delayed Delivery']].iloc[0, 0]
CP_ACH_DD = delayed.loc[delayed['MCC'] == MCC, ['CP/ACH Delayed Delivery']].iloc[0, 0]

AML_Risk_Rating = delayed.loc[delayed['MCC'] == MCC, ['AML Risk Rating']].iloc[0, 0]
Loss_Risk_Rating = delayed.loc[delayed['MCC'] == MCC, ['Loss Risk Rating']].iloc[0, 0]

mcc_risk = max(AML_Risk_Rating, Loss_Risk_Rating)

Annual_CNP_Volume = st.number_input("Annual CNP Volume ($)", key="Annual_CNP_Volume")
Annual_CP_ACH_Volume = st.number_input("Annual CP/ACH Volume ($)", key="Annual_CP_ACH_Volume")

#old refund rate field
#Refund_Rate = st.number_input("Refund Rate (%)", value=3.0, key="Refund_Rate", step=0.1, format="%0.1f")
Refund_Rate = 0.05
Refund_Days = st.number_input("Refund Days (#) #Default 30 ie. If official 90 day return policy for online sales, Use 90", value=30, key="Refund_Days")

#old chargeback rate field
#Chargeback_Rate = st.number_input("'Chargeback Rate (%)", value=0.5, key="Chargeback_Rate", step=0.1, format="%0.1f")
Refund_Rate = 0.005
Chargeback_Days = 180

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

max_dd = CNP_DD  # Default value for max_dd

def calculate_results(df):
    weighted_avg_DD = (df['DD'] * df['Vol']).sum() / df['Vol'].sum()
    volume = df['Vol'].sum()
    
    if weighted_avg_DD:
        weighted_avg_DD = float(weighted_avg_DD)
    
    max_dd = max(weighted_avg_DD, CNP_DD)
    
    return weighted_avg_DD, volume, max_dd

if st.button("Calculate"):
    weighted_avg_DD, volume, max_dd = calculate_results(edited_df)
    
    st.write('Calculated Results:')
    st.write(f'Weighted Average DD: {weighted_avg_DD}')
    st.write(f'Total Volume: {volume}')
    st.write(f'Max DD: {max_dd}')

# Now max_dd is defined outside the "Calculate" block and can be used as a default value in st.number_input
Delayed_Delivery = st.number_input("Delayed Delivery (DD)", key='Delayed_Delivery', value=max_dd)

#st.write(f'MCC ACH_Delayed_Delivery_Days: {CP_ACH_DD}')
ACH_Delayed_Delivery_Days = st.number_input("ACH_Delayed_Delivery_Days", key='ACH_Delayed_Delivery_Days', value=CP_ACH_DD)

ACH_Reject_Rate = st.number_input('ACH Reject (%)',min_value=0.0, max_value=100.0, key='ACH_Reject_Rate')
ACH_Reject_Days = st.number_input("ACH Reject Days (#)", key='ACH_Reject_Days', value=5)

#Calculations Section Exposure
Refund_Risk = (Annual_CNP_Volume/365) * Refund_Rate * Refund_Days /100
Chargeback_Risk = (Annual_CNP_Volume/365) * Chargeback_Rate * Chargeback_Days /100
DD_Risk = (Annual_CNP_Volume/365) * Delayed_Delivery 

ACH_Reject_Exposure = ((Annual_CP_ACH_Volume/365)*ACH_Delayed_Delivery_Days) + ((Annual_CP_ACH_Volume/365)*ACH_Reject_Rate*ACH_Reject_Days)
Total_Volume = Annual_CNP_Volume + Annual_CP_ACH_Volume
Total_Exposure = Refund_Risk + Chargeback_Risk + DD_Risk + ACH_Reject_Exposure

st.header('Tiering Fields')

Fulfillment = max(Delayed_Delivery, ACH_Delayed_Delivery_Days)

#Tiering Calc Fields
BusinessAge = st.radio('How old is the business?', options=['Less than 6 months', '6 months to 1 year', '1 year to 5 years', '5 years to 10 years', '>10 years'], 
            horizontal=True)

BankHistory = st.selectbox(
        'What is the customers business processing and banking history?',
        (['Customer refuses to provide any bank or processing statements OR has no recordkeeping information to provide.',\
        'Customer provided one (1) month of EITHER most recent business banking statements or prior processing statements.',\
        'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements. OR sub-merchant with approved exemption.',\
        'Customer provided one (1) month of BOTH their most recent business banking and prior processing statements.',\
        'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements.']))


ReturnPolicy = st.selectbox(
        'What is the customers return policy?',
        (['No return policy or return policy not posted', 'Refunds for returns, but only up to 7 days and/or the buyer must pay return shipping', \
        'Refunds for returns, but only up to 15 days', 'Refunds for returns, but only up to 30 days', 'Refunds issued for returns even 60 days+ post-order']))

AvgReview = st.radio('What is the business average review score across all review platforms?', options=['< 4.0 Stars', '> 4.0 Stars – 4.3 Stars', '> 4.3 Stars to 4.5 Stars OR less than 20 reviews across all review sites.', \
        '> 4.5 Stars to 4.8 Stars', '> 4.8 Stars'], 
            horizontal=True)

SignerCreditScore = st.radio('What is the signers credit score?', options=['<550','551-579 or Unknown', '580-650', '651-750', '751-850'], \
            horizontal=True)

#Calculations Section Tier


if  BusinessAge == 'Less than 6 months' \
    or BankHistory == 'Customer refuses to provide any bank or processing statements OR has no recordkeeping information to provide.'\
    or SignerCreditScore == '<550' \
    or ReturnPolicy == 'No return policy or return policy not posted' \
    or AvgReview == '< 4.0 Stars'\
    or Fulfillment >= 90 \
    or mcc_risk == 5:
    final_score = 5
elif BusinessAge == '6 months to 1 year' \
    or BankHistory == 'Customer provided one (1) month of EITHER most recent business banking statements or prior processing statements.'\
    or SignerCreditScore == '551-579 or Unknown' \
    or ReturnPolicy == 'Refunds for returns, but only up to 7 days and/or the buyer must pay return shipping' \
    or AvgReview == '> 4.0 Stars – 4.3 Stars'\
    or Fulfillment >= 31\
    or mcc_risk == 4: 
    final_score = 4
elif BusinessAge == '1 year to 5 years'\
    or BankHistory == 'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements. OR sub-merchant with approved exemption.'\
    or SignerCreditScore == '580-650' \
    or ReturnPolicy == 'Refunds for returns, but only up to 15 days' \
    or AvgReview == '> 4.3 Stars to 4.5 Stars OR less than 20 reviews across all review sites'\
    or Fulfillment >= 16\
    or mcc_risk == 3:
    final_score = 3
elif BusinessAge == '5 years to 10 years' \
    or BankHistory == 'Customer provided one (1) month of BOTH their most recent business banking and prior processing statements.'\
    or SignerCreditScore == '651-750' \
    or ReturnPolicy == 'Refunds for returns, but only up to 30 days' \
    or AvgReview == '> 4.5 Stars to 4.8 Stars' \
    or Fulfillment >= 6\
    or mcc_risk == 2:
    final_score = 2
elif BusinessAge == '> 10 years' \
    or BankHistory == 'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements.' \
    or SignerCreditScore == '751-850' \
    or ReturnPolicy == 'Refunds issued for returns even 60 days+ post-order' \
    or AvgReview == '> 4.8 Stars' \
    or Fulfillment > 0 \
    or mcc_risk == 1:
    final_score = 1

st.header('Final Results')

#st.write('Refund_Risk:', Refund_Risk)
#st.write('Chargeback_Risk:', Chargeback_Risk)
#st.write('DD_Risk:', DD_Risk)
#st.write('ACH_Reject_Exposure:', ACH_Reject_Exposure)

formatted_exposure = "${:,.0f}".format(Total_Exposure)
st.write('The Final Exposure of the Customer is:', formatted_exposure)
st.write('The Final Tier of the Customer is: ', final_score)



#dont need dataframes atm
#Tiering = pd.DataFrame({'BusinessAge':[BusinessAge],
#                                'BankHistory':[BankHistory],
#                                'Fulfillment':[Fulfillment], 
#                                'International':[International],
#                                'Custom':[Custom],
#                                'ReturnPolicy':[ReturnPolicy],                      
#                                'AvgReview':[AvgReview],
#                                'SignerCreditScore':[SignerCreditScore],
#                                'FinalTier':[final_score],
#                                })

 
#Exposure = pd.DataFrame({'Annual_CNP_Volume':[Annual_CNP_Volume],
#                            'Annual_CP_ACH_Volume':[Annual_CP_ACH_Volume],
#                            'Refund_Rate':[Refund_Rate],
#                            'Refund_Days':[Refund_Days],
#                            'Chargeback_Rate':[Chargeback_Rate],
#                            'Chargeback_Days':[Chargeback_Days],
#                            'Delayed_Delivery':[Delayed_Delivery], 
#                            'ACH_Delayed_Delivery_Days':[ACH_Delayed_Delivery_Days],
#                            'ACH_Reject_Rate':[ACH_Reject_Rate],
#                            'ACH_Reject_Days':[ACH_Reject_Days],     
#                            'MCC':[MCC],
#                            'CNP_DD':[CNP_DD],
#                            'CP_ACH_DD':[CP_ACH_DD],
#                            'Refund_Risk':[Refund_Risk],
#                            'Chargeback_Risk':[Chargeback_Risk],
#                            'DD_Risk':[DD_Risk],
#                            'ACH_Reject_Exposure':[ACH_Reject_Exposure],
#                            'Total_Exposure':[Total_Exposure],
#                            'Total_Volume':[Total_Volume],
#                                })

# Download To Be Worked on in the future

#    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
#        Tiering.to_excel(writer, sheet_name='Tier_Data')
#        Exposure.to_excel(writer, sheet_name='Exposure_Data')

        # Close the Pandas Excel writer and output the Excel file to the buffer
#        writer.close()

#        st.download_button(
#            label="Download Excel worksheets",
#            data=buffer,
#            file_name=f"{st.session_state.filename}.xlsx",
#            mime="application/vnd.ms-excel"
#        )
