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

#To Do
#Remove Index Tier
#Figure out the 0 showing on the app
#upload excel for - CNP_DD = 0 | CP_ACH_DD = 0




st.set_page_config(page_title="Underwriting Calculator", page_icon="💾", layout="wide")

st.title("Underwriting Calculator")
st.markdown("This New Calculator Combines the older Tiering + Exposure Calculators")

filename = st.text_input("Filename (must include merchant name + deal id)", key="filename")

st.divider()

st.header('Tiering Fields')

buffer = io.BytesIO()

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

Fulfillment = st.radio('What is the expected fulfillment (from date of transaction to date of delivery) timeframe in days?', options=['1-5 days', '6-15 days', '16-30 days', '31-89 days', '90 days +'], 
          horizontal=True)

International = st.selectbox(
    'Does the business fulfill orders from an international supplier and/or require a port release?',
    (['Yes - international shipping and port release', 'Yes - international drop shipping',\
      'Yes - international supplier, but shipped domestically; however, not consistent on-hand inventory.',\
        'Yes - international supplier, but domestically received and shipped on-demand', 'no']))

Custom = st.selectbox(
    'Does the business take custom orders?',
    (['Yes - all custom', 'Yes - mostly custom orders', 'Yes - some, but majority appear to be on-demand shipping',\
      'Dont Know', 'No']))

ReturnPolicy = st.selectbox(
    'What is the customers return policy?',
    (['No return policy or return policy not posted', 'Refunds for returns, but only up to 7 days and/or the buyer must pay return shipping', \
      'Refunds for returns, but only up to 15 days', 'Refunds for returns, but only up to 30 days', 'Refunds issued for returns even 60 days+ post-order']))

BBBRating = st.selectbox(
    'What is the business BBB rating and accreditation?',
    (['F, regardless of accredititation OR D and not accredited', \
      'D and accredited', 'C and accredited OR no rating', 'B and accredited OR A and not accredited',\
        'A and accredited']))

AvgReview = st.radio('What is the expected fulfillment (from date of transaction to date of delivery) timeframe in days?', options=['< 4.0 Stars', '> 4.0 Stars – 4.3 Stars', '> 4.3 Stars to 4.5 Stars OR less than 20 reviews across all review sites.', \
      '> 4.5 Stars to 4.8 Stars', '> 4.8 Stars'], 
          horizontal=True)

ReviewTest = st.selectbox(
    'Are there any reviews indicating shipping delays, scams, or increased risk of chargeback?',
    (['Yes, multiple reviews and recent reviews',\
      'Yes, 3-4 lifetime including recent reviews and/or making up the majority of reviews', \
      'Yes, 1-2 but there are few reviews overall',\
      'Yes, but only 1-2 lifetime and none in the last month', 'No']))

SignerCreditScore = st.radio('How old is the business?', options=['<550','551-579 or Unknown', '580-650', '651-750', '751-850'], 
          horizontal=True)

#Calculations Section Tier
Aggregated_Score = 0

if BusinessAge == '> 10 years':
    Aggregated_Score = Aggregated_Score + 1
elif BusinessAge == '5 years to 10 years':
    Aggregated_Score = Aggregated_Score + 2
elif BusinessAge == '1 year to 5 years':
    Aggregated_Score = Aggregated_Score + 3
elif BusinessAge == '6 months to 1 year':
    Aggregated_Score = Aggregated_Score + 4
elif BusinessAge == 'Less than 6 months':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

if BankHistory == 'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements.':
    Aggregated_Score = Aggregated_Score + 1
elif BankHistory == 'Customer provided one (1) month of BOTH their most recent business banking and prior processing statements.':
    Aggregated_Score = Aggregated_Score + 2
elif BankHistory == 'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements. OR sub-merchant with approved exemption.':
    Aggregated_Score = Aggregated_Score + 3
elif BankHistory == 'Customer provided one (1) month of EITHER most recent business banking statements or prior processing statements.':
    Aggregated_Score = Aggregated_Score + 4
elif BankHistory == 'Customer refuses to provide any bank or processing statements OR has no recordkeeping information to provide.':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

if Fulfillment == '1-5 days':
    Aggregated_Score = Aggregated_Score + 1
elif Fulfillment == '6-15 days':
    Aggregated_Score = Aggregated_Score + 2
elif Fulfillment == '16-30 days':
    Aggregated_Score = Aggregated_Score + 3
elif Fulfillment == '31-89 days':
    Aggregated_Score = Aggregated_Score + 4
elif Fulfillment == '90 days +':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

if International == 'No':
    Aggregated_Score = Aggregated_Score + 1
elif International == 'Yes - international supplier, but domestically received and shipped on-demand':
    Aggregated_Score = Aggregated_Score + 2
elif International == 'Yes - international supplier, but shipped domestically; however, not consistent on-hand inventory.':
    Aggregated_Score = Aggregated_Score + 3
elif International == 'Yes - international drop shipping':
    Aggregated_Score = Aggregated_Score + 4
elif International == 'Yes - international shipping and port release':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

if Custom == 'No':
    Aggregated_Score = Aggregated_Score + 1
elif Custom == 'Dont Know':
    Aggregated_Score = Aggregated_Score + 2
elif Custom == 'Yes - some, but majority appear to be on-demand shipping':
    Aggregated_Score = Aggregated_Score + 3
elif Custom == 'Yes - mostly custom orders':
    Aggregated_Score = Aggregated_Score + 4
elif Custom == 'Yes - all custom':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

if ReturnPolicy == 'Refunds issued for returns even 60 days+ post-order':
    Aggregated_Score = Aggregated_Score + 1
elif ReturnPolicy == 'Refunds for returns, but only up to 30 days':
    Aggregated_Score = Aggregated_Score + 2
elif ReturnPolicy == 'Refunds for returns, but only up to 15 days':
    Aggregated_Score = Aggregated_Score + 3
elif ReturnPolicy == 'Refunds for returns, but only up to 7 days and/or the buyer must pay return shipping':
    Aggregated_Score = Aggregated_Score + 4
elif ReturnPolicy == 'No return policy or return policy not posted':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

if BBBRating == 'A and accredited':
    Aggregated_Score = Aggregated_Score + 1
elif BBBRating == 'B and accredited OR A and not accredited':
    Aggregated_Score = Aggregated_Score + 2
elif BBBRating == 'C and accredited OR no rating':
    Aggregated_Score = Aggregated_Score + 3
elif BBBRating == 'D and accredited':
    Aggregated_Score = Aggregated_Score + 4
elif BBBRating == 'F, regardless of accredititation OR D and not accredited':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

if AvgReview == '> 4.8 Stars':
    Aggregated_Score = Aggregated_Score + 1
elif AvgReview == '> 4.5 Stars to 4.8 Stars':
    Aggregated_Score = Aggregated_Score + 2
elif AvgReview == '> 4.3 Stars to 4.5 Stars OR less than 20 reviews across all review sites.':
    Aggregated_Score = Aggregated_Score + 3
elif AvgReview == '> 4.0 Stars – 4.3 Stars':
    Aggregated_Score = Aggregated_Score + 4
elif AvgReview == '< 4.0 Stars':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

if ReviewTest == 'No':
    Aggregated_Score = Aggregated_Score + 1
elif ReviewTest == 'Yes, but only 1-2 lifetime and none in the last month':
    Aggregated_Score = Aggregated_Score + 2
elif ReviewTest == 'Yes, 1-2 but there are few reviews overall':
    Aggregated_Score = Aggregated_Score + 3
elif ReviewTest == 'Yes, 3-4 lifetime including recent reviews and/or making up the majority of reviews':
    Aggregated_Score = Aggregated_Score + 4
elif ReviewTest == 'Yes, multiple reviews and recent reviews':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

if SignerCreditScore == '751-850':
    Aggregated_Score = Aggregated_Score + 1
elif SignerCreditScore == '651-750':
    Aggregated_Score = Aggregated_Score + 2
elif SignerCreditScore == '580-650':
    Aggregated_Score = Aggregated_Score + 3
elif SignerCreditScore == '551-579, OR unknown':
    Aggregated_Score = Aggregated_Score + 4
elif SignerCreditScore == '<550':
    Aggregated_Score = Aggregated_Score + 5
else:
    Aggregated_Score

InitialTier = 0

#Find Initial Tier
if Aggregated_Score >= 42 :
    InitialTier = 5
elif Aggregated_Score >= 34:
    InitialTier = 4
elif Aggregated_Score >= 26:
    InitialTier = 3
elif Aggregated_Score >= 18:
    InitialTier = 2 
else:
    InitialTier = 1

#Find Tier 5 Override
Tier5 = 0

if BankHistory == 'Customer refuses to provide any bank or processing statements OR has no recordkeeping information to provide.':
    Tier5 = 1
elif International == 'Yes - international shipping and port release':
    Tier5 = 1
elif Fulfillment == '90 days +':
    Tier5 = 1
elif SignerCreditScore == '<550':
    Tier5 = 1
else:
    Tier5 

#Find Tier 4 Override
Tier4 = 0

if Fulfillment == '31-89 days':
    Tier4 = 1
elif SignerCreditScore == '551-579, OR unknown':
    Tier4 = 1
else:
    Tier4

#FinalTier
FinalTier = 0

if Tier5 == 1:
    FinalTier = 5
elif InitialTier == 5:
    FinalTier = 5
elif  Tier4 == 1:
    FinalTier = 4
elif  InitialTier == 4:
    FinalTier = 4
elif  InitialTier == 3:
    FinalTier = 3
elif  InitialTier == 2:
    FinalTier = 2
elif  InitialTier == 1:
    FinalTier = 1
else:
    FinalTier == 1

Tiering = pd.DataFrame({'BusinessAge':[BusinessAge],
                            'BankHistory':[BankHistory],
                            'Fulfillment':[Fulfillment], 
                            'International':[International],
                            'Custom':[Custom],
                            'ReturnPolicy':[ReturnPolicy],                      
                            'BBBRating':[BBBRating],
                            'AvgReview':[AvgReview],
                            'ReviewText':[ReviewTest],
                            'SignerCreditScore':[SignerCreditScore],
                            'InitialTier':[InitialTier],
                            'Tier5':[Tier5],
                            'Tier4':[Tier4],
                            'FinalTier':[FinalTier],
                            })

st.write('The Final Tier of the Customer is: ', FinalTier)

#Exposure Calc Fields
#flow of this app sucks





#https://extras.streamlit.app/Grid%20Layout
st.header('Exposure Fields')

delayed = pd.read_csv('Underwriting_App/MCC & Business Models - MCC Ratings_Sales.csv')


MCC = st.number_input("MCC", key='MCC', value=1711)

#if MCC:



testing = delayed.loc[delayed['MCC'] == MCC, ['CNP Delayed Delivery']].iloc[0, 0]

CNP_DD = delayed.loc[delayed['MCC'] == MCC, ['CNP Delayed Delivery']].iloc[0, 0]
CP_ACH_DD = delayed.loc[delayed['MCC'] == MCC, ['CP/ACH Delayed Delivery']].iloc[0, 0]

Annual_CNP_Volume = st.number_input("Annual CNP Volume ($)", key="Annual_CNP_Volume")
Annual_CP_ACH_Volume = st.number_input("Annual CP/ACH Volume ($)", key="Annual_CP_ACH_Volume")

Refund_Rate = st.number_input("Refund Rate (%)", value=3.0, key="Refund_Rate", step=0.1, format="%0.1f")
Refund_Days = st.number_input("Refund Days (#) #Default 30 ie. If official 90 day return policy for online sales, Use 90", value=30, key="Refund_Days")

Chargeback_Rate = st.number_input("'Chargeback Rate (%)", value=0.5, key="Chargeback_Rate", step=0.1, format="%0.1f")
Chargeback_Days = st.number_input("Chargeback Days (#) Default 180", value=180, key="Chargeback_Days")

my_expander = st.expander(label='Delayed Delivery Calcs')

with my_expander:
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
        return weighted_avg_DD, volume

    if st.button("Calculate"):
        weighted_avg_DD, volume = calculate_results(edited_df)
        st.write('Calculated Results:')
        st.write(f'Weighted Average DD: {weighted_avg_DD}')
        st.write(f'Total Volume: {volume}')

#st.write(f'MCC Delayed_Delivery_Days: {CNP_DD}')
Delayed_Delivery = st.number_input("Delayed Delivery (DD)", key='Delayed_Delivery', value=CNP_DD)

#st.write(f'MCC ACH_Delayed_Delivery_Days: {CP_ACH_DD}')
ACH_Delayed_Delivery_Days = st.number_input("ACH_Delayed_Delivery_Days", key='ACH_Delayed_Delivery_Days', value=CP_ACH_DD)


ACH_Reject_Rate = st.number_input('ACH Reject (%)',min_value=0.0, max_value=100.0, key='ACH_Reject_Rate')
ACH_Reject_Days = st.number_input("ACH Reject Days (#)", key='ACH_Reject_Days', value=5)

Rolling_Reserve_Percent = st.number_input('Rolling Reserve Percent',min_value=0.0, max_value=100.0, key='Rolling_Reserve_Percent')
Rolling_Reserve_Days = st.number_input("Rolling Reserve Days", key='Rolling_Reserve_Days', min_value=0)

Minimium_Reserve = st.number_input("Minimium Reserve", key='Minimium_Reserve')
Capture_Rate = st.number_input('Capture Rate',min_value=0.0, max_value=100.0, key='Capture_Rate')

Flat_Reserve = st.number_input("Flat_Reserve", key='Flat_Reserve')



#Calculations Section Exposure
Refund_Risk = (Annual_CNP_Volume/365) * Refund_Rate * Refund_Days
Chargeback_Risk = (Annual_CNP_Volume/365) * Chargeback_Rate * Chargeback_Days
DD_Risk = (Annual_CNP_Volume/365) * Delayed_Delivery 

ACH_Reject_Exposure = ((Annual_CP_ACH_Volume/365)*ACH_Delayed_Delivery_Days) + ((Annual_CP_ACH_Volume/365)*ACH_Reject_Rate*ACH_Reject_Days)
Total_Exposure = Refund_Risk + Chargeback_Risk + DD_Risk + ACH_Reject_Exposure

Total_Volume = Annual_CNP_Volume + Annual_CP_ACH_Volume

Rolling_Reserve = ((Annual_CP_ACH_Volume + Annual_CP_ACH_Volume)/365) * Rolling_Reserve_Percent * Rolling_Reserve_Days

if (Annual_CP_ACH_Volume or Annual_CNP_Volume) and Total_Exposure:
    Full_Capture_Days = (Minimium_Reserve / ((Annual_CP_ACH_Volume + Annual_CNP_Volume)/365)) / Capture_Rate
    Full_Capture_Month = Full_Capture_Days / 30

    Total_Collateral = Rolling_Reserve + Minimium_Reserve + Flat_Reserve

    Exposure_Coverage = Total_Collateral / Total_Exposure
    Collateral_Coverage = Exposure_Coverage

 
    Exposure = pd.DataFrame({'Annual_CNP_Volume':[Annual_CNP_Volume],
                            'Annual_CP_ACH_Volume':[Annual_CP_ACH_Volume],
                            'Refund_Rate':[Refund_Rate],
                            'Refund_Days':[Refund_Days],
                            'Chargeback_Rate':[Chargeback_Rate],
                            'Chargeback_Days':[Chargeback_Days],
                            'Delayed_Delivery':[Delayed_Delivery], 
                            'ACH_Delayed_Delivery_Days':[ACH_Delayed_Delivery_Days],
                            'ACH_Reject_Rate':[ACH_Reject_Rate],
                            'ACH_Reject_Days':[ACH_Reject_Days],     
                            'Rolling_Reserve_Percent':[Rolling_Reserve_Percent],
                            'Rolling_Reserve_Days':[Rolling_Reserve_Days],
                            'Minimium_Reserve':[Minimium_Reserve],
                            'Capture_Rate':[Capture_Rate],
                            'Flat_Reserve':[Flat_Reserve],
                            'MCC':[MCC],
                            'CNP_DD':[CNP_DD],
                            'CP_ACH_DD':[CP_ACH_DD],
                            'Refund_Risk':[Refund_Risk],
                            'Chargeback_Risk':[Chargeback_Risk],
                            'DD_Risk':[DD_Risk],
                            'ACH_Reject_Exposure':[ACH_Reject_Exposure],
                            'Total_Exposure':[Total_Exposure],
                            'Total_Volume':[Total_Volume],
                            'Rolling_Reserve':[Rolling_Reserve],
                            'Full_Capture_Days':[Full_Capture_Days],
                            'Full_Capture_Month':[Full_Capture_Month],
                            'Total_Collateral':[Total_Collateral],
                            'Exposure_Coverage':[Exposure_Coverage],
                            'Collateral_Coverage':[Collateral_Coverage],
                                })

    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        Tiering.to_excel(writer, sheet_name='Tier_Data')
        Exposure.to_excel(writer, sheet_name='Exposure_Data')

        # Close the Pandas Excel writer and output the Excel file to the buffer
        writer.close()

        st.download_button(
            label="Download Excel worksheets",
            data=buffer,
            file_name=f"{st.session_state.filename}.xlsx",
            mime="application/vnd.ms-excel"
        )

#ACH Reject (%) / Rolling Reserve Percent needs to go down level
#Capture Rate need to go up 1 decimal places