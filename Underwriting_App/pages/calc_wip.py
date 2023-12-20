#22723f66-163f-4a5a-8a55-a10227f0eb1f

#DD Not working

import streamlit as st
import redshift_connector
import pandas as pd
import re
from datetime import datetime
import math


#button to insert this record into the Database



def insert_into_redshift(Stax_Merchant_ID, MCC, Department, DepartmentPin, Annual_CNP_Volume, Annual_CP_ACH_Volume, Refund_Days, Delayed_Delivery, BusinessAgeDBVal, BankHistoryDBVal, ReturnPolicyDBVal, AvgReviewDBVal, SignerCreditScoreDBVal, ChargebackRefundHistoryDBVal, Total_Exposure, final_score, current_timestamp):
    try:
        conn = redshift_connector.connect(
            host='redhouse.cedak34tz6ud.us-west-2.redshift.amazonaws.com',
            database='redhouse',
            port=5439,
            user='python.risk.uw',
            password='94TPRCoBv9geUz4byQkm4MYC'
        )

        cur = conn.cursor()

        insert_query = '''
        INSERT INTO risk.tier_exposure_calculations_test (stax_merchant_id, mcc, department, pin, annual_cnp_volume, annual_cp_ach_volume, refund_days, delayed_delivery, biz_age_time_of_calc, processing_bank_history, return_policy, avg_biz_review_score, signer_credit_score, chargeback_refund_history, final_exposure, final_risk_tier, date_calculated) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''

        data = (Stax_Merchant_ID, MCC, Department, DepartmentPin, Annual_CNP_Volume, Annual_CP_ACH_Volume, Refund_Days, Delayed_Delivery, BusinessAgeDBVal, BankHistoryDBVal, ReturnPolicyDBVal, AvgReviewDBVal, SignerCreditScoreDBVal, ChargebackRefundHistoryDBVal, Total_Exposure, final_score, current_timestamp)
        cur.execute(insert_query, data)
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        print("Error:", e)
        return False

def main():
    

    current_timestamp = datetime.now().strftime('%Y-%m-%d')
    st.set_page_config(page_title="Underwriting Calculator", page_icon="💾", layout="wide")

    st.title("Underwriting Calculator")
    st.markdown("This New Calculator Combines the older Tiering + Exposure Calculators")

    st.header('Merchant Info')

    Stax_Mid = st.text_input("Stax MID (PMID or OMID)", key='StaxMid')
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

    # Check if the input matches the pattern
    if not re.match(pattern, Stax_Mid):
        st.error("Please input a valid format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX")

    delayed = pd.read_csv('Underwriting_App/MCC & Business Models - MCC Ratings_Sales.csv')

    MCC = st.number_input("MCC", key='MCC', value=1711)

    st.header('Underwriter or Analyst')

    #Tiering Calc Fields
    Department = st.radio('What Department do you report under?', options=['Underwriting', 'Risk Monitoring'], 
                horizontal=True)

    DepartmentPin = st.number_input("PIN", key='Department_PIN', step=1)

    if len(str(DepartmentPin)) != 5:
        st.error("Please input a valid 5-digit PIN.")

    st.header('Exposure Fields')

    testing = delayed.loc[delayed['MCC'] == MCC, ['CNP Delayed Delivery']].iloc[0, 0]

    CNP_DD = delayed.loc[delayed['MCC'] == MCC, ['CNP Delayed Delivery']].iloc[0, 0]
    CP_ACH_DD = delayed.loc[delayed['MCC'] == MCC, ['CP/ACH Delayed Delivery']].iloc[0, 0]
    max_cnp_cp_dd = max(CNP_DD, CP_ACH_DD)




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
    Chargeback_Rate = 0.005
    Chargeback_Days = 180

    #st.write(f'MCC ACH_Delayed_Delivery_Days: {CP_ACH_DD}')
    #ACH_Delayed_Delivery_Days = st.number_input("ACH_Delayed_Delivery_Days", key='ACH_Delayed_Delivery_Days', value=CP_ACH_DD)


    #ACH_Reject_Rate = st.number_input('ACH Reject (%)',min_value=0.0, max_value=100.0, key='ACH_Reject_Rate')
    ACH_Reject_Rate = 0.005
    #ACH_Reject_Days = st.number_input("ACH Reject Days (#)", key='ACH_Reject_Days', value=5)

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

    #CP_ACH_DD

    max_dd = max_cnp_cp_dd  # Default value for max_dd

    if 'Delayed_Delivery' not in st.session_state:
        st.session_state['Delayed_Delivery'] = max_dd  # Set initial value here


    def calculate_results(df):
        weighted_avg_DD = math.ceil((df['DD'] * df['Vol']).sum() / df['Vol'].sum())
        volume = df['Vol'].sum()
        
        if weighted_avg_DD:
            weighted_avg_DD = float(weighted_avg_DD)
        
        max_dd = max(weighted_avg_DD, max_cnp_cp_dd)
        st.session_state['Delayed_Delivery'] = max_dd  # Store the value in session state
        return weighted_avg_DD, volume, max_dd
        
    if st.button("Calculate"):
        weighted_avg_DD, volume, max_dd = calculate_results(edited_df)
        
        st.write('Calculated Results:')
        st.write(f'Weighted Average DD: {weighted_avg_DD}')
        st.write(f'Total Volume: {volume}')
        st.write(f'Max DD: {max_dd}')

    # Now max_dd is defined outside the "Calculate" block and can be used as a default value in st.number_input
    Delayed_Delivery = st.number_input("Delayed Delivery (DD)", key='Delayed_Delivery', value=st.session_state['Delayed_Delivery'])

    #Calculations Section Exposure
    Refund_Risk = (Annual_CNP_Volume/365) * Refund_Rate * Refund_Days /100
    Chargeback_Risk = (Annual_CNP_Volume/365) * Chargeback_Rate * Chargeback_Days /100
    DD_Risk = (Annual_CNP_Volume/365) * Delayed_Delivery 

    ACH_Reject_Exposure = ((Annual_CP_ACH_Volume/365)*Delayed_Delivery) + ((Annual_CP_ACH_Volume/365)*ACH_Reject_Rate*ACH_Reject_Days)
    Total_Volume = Annual_CNP_Volume + Annual_CP_ACH_Volume
    Total_Exposure = Refund_Risk + Chargeback_Risk + DD_Risk + ACH_Reject_Exposure

    st.header('Tiering Fields')

    Fulfillment = Delayed_Delivery

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

    AvgReview = st.radio('What is the business average review score across all review platforms?', options=['> 4.0 Stars – 4.3 Stars', '> 4.3 Stars to 4.5 Stars OR less than 20 reviews across all review sites.', \
            '> 4.5 Stars to 4.8 Stars', '> 4.8 Stars'], 
                horizontal=True)

    SignerCreditScore = st.radio('What is the signers credit score?', options=['<550','551-579 or Unknown', '580-650', '651-750', '751-850'], \
                horizontal=True)

    ChargebackRefundHistory = st.selectbox(
            'What is the customers business processing and banking history?',
            (['Underwriting Skip if Not Provided',\
            'Merchants chargeback rate over the last 180 days is 2% or higher OR merchants refund rate in the last 90 days is 10% or higher OR merchants ACH reversal rate in the last 30 days is 0.5% or higher where the majority of codes are R05, R07, R08, R10, R29, R51 or 15% or higher where the majority of codes are not previously listed.',\
            'Merchants chargeback rate over the last 180 days is at least 1%, but lower than 2% OR merchants refund rate in the last 90 days is at least 7.5%, but lower than 10% OR merchants ACH reversal rate in the last 30 days is 0.4% where the majority of codes are R05, R07, R08, R10, R29, R51 or at least 10%, but lower than 15% where the majority of codes are not previously listed.',\
            'Merchants chargeback rate over the last 180 days is at least 0.75%, but lower than 1% OR merchants refund rate in the last 90 days is at least 5%, but lower than 7.5% OR merchants ACH reversal rate in the last 30 days is 0.3% where the majority of codes are R05, R07, R08, R10, R29, R51 or at least 7.5%, but lower than 10% where the majority of codes are not previously listed.',\
            'Merchants chargeback rate over the last 180 days is at least 0.05%, but lower than 0.75% OR merchants refund rate in the last 90 days is at least 3%, but lower than 5% OR merchants ACH reversal rate in the last 30 days is 0.2% where the majority of codes are R05, R07, R08, R10, R29, R51 or at least 5%, but lower than 7.5% where the majority of codes are not previously listed.',\
            'Merchants chargeback rate over the last 180 days is less than 0.05% OR merchants refund rate in the last 90 days is less than 3% OR merchants ACH reversal rate in the last 30 days is less than 0.2% where the majority of codes are R05, R07, R08, R10, R29, R51 or less than 5% where the majority of codes are not previously listed.']))
    

    Business_Age_Mapping = {
    'Less than 6 months': 5,
    '6 months to 1 year': 4,
    '1 year to 5 years': 3,
    '5 years to 10 years': 2,
    '>10 years': 1
    }


    Bank_History_Mapping = {
    'Customer refuses to provide any bank or processing statements OR has no recordkeeping information to provide.': 5,
    'Customer provided one (1) month of EITHER most recent business banking statements or prior processing statements.': 4,
    'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements. OR sub-merchant with approved exemption.': 3,
    'Customer provided one (1) month of BOTH their most recent business banking and prior processing statements.': 2,
    'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements.': 1
    }

    Return_Policy_Mapping = {
    'No return policy or return policy not posted': 5, 
    'Refunds for returns, but only up to 7 days and/or the buyer must pay return shipping': 4, 
    'Refunds for returns, but only up to 15 days': 3, 
    'Refunds for returns, but only up to 30 days': 2, 
    'Refunds issued for returns even 60 days+ post-order': 1
    }

    Avg_Review_Mapping = {
    '> 4.0 Stars – 4.3 Stars': 4,
    '> 4.3 Stars to 4.5 Stars OR less than 20 reviews across all review sites.': 3,
    '> 4.5 Stars to 4.8 Stars': 2,
    '> 4.8 Stars': 1
    }

    Signer_Credit_Score_Mapping = {
    '<550': 5,
    '551-579 or Unknown': 4,
    '580-650': 3,
    '651-750': 2,
    '751-850': 1
    }


    Chargeback_Refund_History_Mapping = {
    'Merchants chargeback rate over the last 180 days is 2% or higher OR merchants refund rate in the last 90 days is 10% or higher OR merchants ACH reversal rate in the last 30 days is 0.5% or higher where the majority of codes are R05, R07, R08, R10, R29, R51 or 15% or higher where the majority of codes are not previously listed.': 5,
    'Merchants chargeback rate over the last 180 days is at least 1%, but lower than 2% OR merchants refund rate in the last 90 days is at least 7.5%, but lower than 10% OR merchants ACH reversal rate in the last 30 days is 0.4% where the majority of codes are R05, R07, R08, R10, R29, R51 or at least 10%, but lower than 15% where the majority of codes are not previously listed.': 4,
    'Merchants chargeback rate over the last 180 days is at least 0.75%, but lower than 1% OR merchants refund rate in the last 90 days is at least 5%, but lower than 7.5% OR merchants ACH reversal rate in the last 30 days is 0.3% where the majority of codes are R05, R07, R08, R10, R29, R51 or at least 7.5%, but lower than 10% where the majority of codes are not previously listed.': 3,
    'Merchants chargeback rate over the last 180 days is at least 0.05%, but lower than 0.75% OR merchants refund rate in the last 90 days is at least 3%, but lower than 5% OR merchants ACH reversal rate in the last 30 days is 0.2% where the majority of codes are R05, R07, R08, R10, R29, R51 or at least 5%, but lower than 7.5% where the majority of codes are not previously listed.': 2,
    'Merchants chargeback rate over the last 180 days is less than 0.05% OR merchants refund rate in the last 90 days is less than 3% OR merchants ACH reversal rate in the last 30 days is less than 0.2% where the majority of codes are R05, R07, R08, R10, R29, R51 or less than 5% where the majority of codes are not previously listed.': 1,
    'Underwriting Skip if Not Provided': 0
    }

    # Get the value from the selected option
    BusinessAgeDBVal = Business_Age_Mapping[BusinessAge]
    BankHistoryDBVal = Bank_History_Mapping[BankHistory]
    ReturnPolicyDBVal = Return_Policy_Mapping[ReturnPolicy]
    AvgReviewDBVal = Avg_Review_Mapping[AvgReview]
    SignerCreditScoreDBVal = Signer_Credit_Score_Mapping[SignerCreditScore]
    ChargebackRefundHistoryDBVal = Chargeback_Refund_History_Mapping[ChargebackRefundHistory]

    if  BusinessAge == 'Less than 6 months' \
        or BankHistory == 'Customer refuses to provide any bank or processing statements OR has no recordkeeping information to provide.'\
        or SignerCreditScore == '<550' \
        or ReturnPolicy == 'No return policy or return policy not posted' \
        or Fulfillment >= 90 \
        or ChargebackRefundHistory == 'Merchants chargeback rate over the last 180 days is 2% or higher OR merchants refund rate in the last 90 days is 10% or higher OR merchants ACH reversal rate in the last 30 days is 0.5% or higher where the majority of codes are R05, R07, R08, R10, R29, R51 or 15% or higher where the majority of codes are not previously listed.' \
        or mcc_risk == 5:
        final_score = 5
    elif BusinessAge == '6 months to 1 year' \
        or BankHistory == 'Customer provided one (1) month of EITHER most recent business banking statements or prior processing statements.'\
        or SignerCreditScore == '551-579 or Unknown' \
        or ReturnPolicy == 'Refunds for returns, but only up to 7 days and/or the buyer must pay return shipping' \
        or AvgReview == '> 4.0 Stars – 4.3 Stars'\
        or Fulfillment >= 31\
        or ChargebackRefundHistory == 'Merchants chargeback rate over the last 180 days is at least 1%, but lower than 2% OR merchants refund rate in the last 90 days is at least 7.5%, but lower than 10% OR merchants ACH reversal rate in the last 30 days is 0.4% where the majority of codes are R05, R07, R08, R10, R29, R51 or at least 10%, but lower than 15% where the majority of codes are not previously listed.' \
        or mcc_risk == 4: 
        final_score = 4
    elif BusinessAge == '1 year to 5 years'\
        or BankHistory == 'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements. OR sub-merchant with approved exemption.'\
        or SignerCreditScore == '580-650' \
        or ReturnPolicy == 'Refunds for returns, but only up to 15 days' \
        or AvgReview == '> 4.3 Stars to 4.5 Stars OR less than 20 reviews across all review sites'\
        or Fulfillment >= 16\
        or ChargebackRefundHistory == 'Merchants chargeback rate over the last 180 days is at least 0.75%, but lower than 1% OR merchants refund rate in the last 90 days is at least 5%, but lower than 7.5% OR merchants ACH reversal rate in the last 30 days is 0.3% where the majority of codes are R05, R07, R08, R10, R29, R51 or at least 7.5%, but lower than 10% where the majority of codes are not previously listed.' \
        or mcc_risk == 3:
        final_score = 3
    elif BusinessAge == '5 years to 10 years' \
        or BankHistory == 'Customer provided one (1) month of BOTH their most recent business banking and prior processing statements.'\
        or SignerCreditScore == '651-750' \
        or ReturnPolicy == 'Refunds for returns, but only up to 30 days' \
        or AvgReview == '> 4.5 Stars to 4.8 Stars' \
        or Fulfillment >= 6\
        or ChargebackRefundHistory == 'Merchants chargeback rate over the last 180 days is at least 0.05%, but lower than 0.75% OR merchants refund rate in the last 90 days is at least 3%, but lower than 5% OR merchants ACH reversal rate in the last 30 days is 0.2% where the majority of codes are R05, R07, R08, R10, R29, R51 or at least 5%, but lower than 7.5% where the majority of codes are not previously listed.' \
        or mcc_risk == 2:
        final_score = 2
    elif BusinessAge == '> 10 years' \
        or BankHistory == 'Customer provided three (3) months of EITHER most recent business banking statements or prior processing statements.' \
        or SignerCreditScore == '751-850' \
        or ReturnPolicy == 'Refunds issued for returns even 60 days+ post-order' \
        or AvgReview == '> 4.8 Stars' \
        or Fulfillment > 0 \
        or ChargebackRefundHistory == 'Merchants chargeback rate over the last 180 days is less than 0.05% OR merchants refund rate in the last 90 days is less than 3% OR merchants ACH reversal rate in the last 30 days is less than 0.2% where the majority of codes are R05, R07, R08, R10, R29, R51 or less than 5% where the majority of codes are not previously listed.'\
        or ChargebackRefundHistory == 'Underwriting Skip if Not Provided' \
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

    ### Button at the bottom to add into the records

    if st.button("Add to Records"):
        progress_bar = st.empty()  # Create an empty slot to later show the progress bar
        progress = st.progress(0)  # Initialize the progress bar
        if Stax_Mid:
            inserted = insert_into_redshift(Stax_Mid, MCC, Department, DepartmentPin, Annual_CNP_Volume, Annual_CP_ACH_Volume, Refund_Days, Delayed_Delivery,  BusinessAgeDBVal, BankHistoryDBVal, ReturnPolicyDBVal, AvgReviewDBVal, SignerCreditScoreDBVal, ChargebackRefundHistoryDBVal, Total_Exposure, final_score, current_timestamp)
            if inserted:
                for percent_complete in range(101):
                    progress.progress(percent_complete)
                    st.session_state.progress = percent_complete  # Update progress in session state
                st.success("Inserted successfully into the database!")
            else:
                st.error("Failed to insert. Please check logs and contact Ryan Nolan.")
        else:
            st.warning("Please enter a Stax Merchant ID.")

if __name__ == "__main__":
    main()


