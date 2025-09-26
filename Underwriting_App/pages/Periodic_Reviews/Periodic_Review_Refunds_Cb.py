# code to run test python3 -m streamlit run Final_Periodic_App/Welcome.py
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import json
import numpy as np
import datetime
from datetime import date, timedelta #, datetime
import io
from auth_utils import require_role, get_user_info
import sys
import os




#https://www.youtube.com/watch?v=uCqqGsEsIL4

st.set_page_config(page_title="Refunds_Chargebacks", page_icon="❗")

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


if require_role(["Risk", "Underwriting"], "Synovus Underwriting and Risk Calculator"):    # Your protected page content goes here
    user_info = get_user_info()
    
    def download_button(objects_to_download, download_filename):
        """
        Generates a link to download the given objects_to_download as separate sheets in an Excel file.
        Params:
        ------
        objects_to_download (dict): A dictionary where keys are sheet names and values are objects to be downloaded.
        download_filename (str): filename and extension of the Excel file. e.g. mydata.xlsx
        Returns:
        -------
        (str): the anchor tag to download the Excel file with multiple sheets
        """
        try:
            # Create an in-memory Excel writer
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as excel_writer:
                for sheet_name, object_to_download in objects_to_download.items():
                    if isinstance(object_to_download, pd.DataFrame):
                        # Write DataFrame as a sheet
                        object_to_download.to_excel(excel_writer, sheet_name=sheet_name)
                    else:
                        # Convert other objects to a DataFrame and write as a sheet
                        df = pd.DataFrame({"Data": [object_to_download]})
                        df.to_excel(excel_writer, sheet_name=sheet_name)
    
            workbook = excel_writer.book     
            worksheet = excel_writer.sheets['History']  
    
            header_format = workbook.add_format({
            "valign": "vcenter",
            "align": "center",
            "bold": True,
            })
    
    
            # Seek to the beginning of the in-memory stream
            output.seek(0)
            excel_data = output.read()
    
            # Encode the Excel file to base64 for download
            b64 = base64.b64encode(excel_data).decode()
    
            dl_link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{download_filename}">Download Excel</a>'
    
            return dl_link
        except Exception as e:
            # Log the error and return an error message
            st.error(f"An error occurred during file generation: {e}")
            return None
    
    def download_df():
        if uploaded_files:
            for file in uploaded_files:
                file.seek(0)
            uploaded_data_read = [pd.read_csv(file) for file in uploaded_files]
            df = pd.concat(uploaded_data_read)
    
            days90 = date.today() - timedelta(days=90)
            days180 = date.today() - timedelta(days=180)
    
            df2 = df[df['created_at'].str.split(expand=True)[1].isna() == False]
            dfbaddates = df[df['created_at'].str.split(expand=True)[1].isna() == True].copy()
    
            dfbaddates['created_at'] = dfbaddates['created_at'].apply(lambda x: datetime.datetime(1900, 1, 1, 0, 0, 0) + datetime.timedelta(days=float(x)))
            dfbaddates['created_at'] = pd.to_datetime(dfbaddates['created_at'])
            dfbaddates['created_at'] = dfbaddates['created_at'].dt.strftime('%m/%d/%y')
            df.loc[df['created_at'].str.split(expand=True)[1].isna() == False, 'created_at'] = df2['created_at'].str.split(expand=True)[0].str.strip()
            newdf = pd.concat([df2, dfbaddates])
    
            def custom_datetime_parser(x):
            # Check if the datetime string contains a space
                if ' ' in x:
            # Split the datetime string into date and time parts
                    date_part, time_part = x.split()
            # Parse the date part as a date and the time part as a custom time representation
                    return pd.to_datetime(date_part) + pd.Timedelta(hours=int(time_part.split(':')[0]))
                else:
            # Handle the case where there is no space in the datetime string
                    return pd.to_datetime(x)
    
            newdf['created_at'] = newdf['created_at'].apply(custom_datetime_parser)
            
            newdf['created_at'] = pd.to_datetime(newdf['created_at']).dt.date
            newdf2 = newdf.query("success == 1")
            df3 = newdf2.query("payment_method == 'card' | payment_method == 'bank'")
            df3.drop(['id','merchant_id','user_id','customer_id','subtotal','tax','is_manual','success','donation','tip','meta','pre_auth','updated_at','source', 'issuer_auth_code'], axis=1, inplace=True)
            df4 = df3.loc[:,['type', 'created_at', 'total', 'payment_person_name', 'customer_firstname', 'customer_lastname',\
                'payment_last_four', 'last_four', 'payment_method', 'channel', 'memo', 'payment_note', 'reference', \
                'payment_card_type', 'payment_card_exp', 'payment_bank_name', 'payment_bank_type',\
                'payment_bank_holder_type', 'billing_address_1', 'billing_address_2','billing_address_city', \
                'billing_address_state', 'billing_address_zip', 'customer_company','customer_email', 'customer_phone', \
                'customer_address_1','customer_address_2', 'customer_address_city', 'customer_address_state', \
                'customer_address_zip', 'customer_notes', 'customer_reference', 'customer_created_at', \
                'customer_updated_at', 'customer_deleted_at', 'gateway_id', 'gateway_name', 'gateway_type', \
                'gateway_created_at', 'gateway_deleted_at', 'user_name', 'system_admin', 'user_created_at',\
                'user_updated_at', 'user_deleted_at']]
    
            volume = df3.query("type == 'charge'")
            volumetotal = np.sum(volume['total'])
            volume90 = np.sum(volume[volume['created_at'] > days90]['total'])
            volume180 = np.sum(volume[volume['created_at'] > days180]['total'])
    
            refund = df3.query("type == 'refund'")
            refundtotal = np.sum(refund['total'])
            refund90 = np.sum(refund[refund['created_at'] > days90]['total'])
    
            cardonly = df3.query("type == 'charge' & payment_method == 'card'")
            cardtotal = np.sum(cardonly['total'])
            card180days = np.sum(cardonly[cardonly['created_at'] > days180]['total'])
    
            ###########################################################
            achonly = df3.query("type == 'charge' & payment_method == 'bank'")
            achtotal = np.sum(achonly['total'])
            ach180days = np.sum(achonly[achonly['created_at'] > days180]['total'])
    
    
    
            Lifetime_refund_rate = (refundtotal / volumetotal)
            day90_refund_rate = (refund90/volume90)
            Lifetime_chargeback_rate = (chargebackslifetime / cardtotal)
            day180_chargeback_rate = (chargebacks180/card180days)
    
    
            #####################################
    
            d = date.today()
            var_names = ["CurrentMonth", "PastMonth", "PastMonth2", "PastMonth3", "PastMonth4", "PastMonth5", "PastMonth6"]
            count = 0
            
            for name in var_names:
                month, year = (d.month - count, d.year) if d.month > count else (12 - (count - d.month), d.year - 1)
                month = month if month >= 1 else month + 12  # Adjust negative month value
                globals()[name] = d.replace(day=1, month=month, year=year)
                count += 1
    
    
            #CARD ONLY VOL
            volume_card = df3.query("type == 'charge' & payment_method == 'card'")
            volume_card_total = np.sum(volume_card['total'])
            volume_card_CurrentMonth = np.sum(volume_card[volume_card['created_at'] >= CurrentMonth]['total'])
            volume_card_PastMonth = np.sum(volume_card[volume_card['created_at'] >= PastMonth]['total']) - volume_card_CurrentMonth
            volume_card_PastMonth2 = np.sum(volume_card[volume_card['created_at'] >= PastMonth2]['total']) - volume_card_CurrentMonth - volume_card_PastMonth
            volume_card_PastMonth3 = np.sum(volume_card[volume_card['created_at'] >= PastMonth3]['total']) - volume_card_CurrentMonth - volume_card_PastMonth - volume_card_PastMonth2
            volume_card_PastMonth4 = np.sum(volume_card[volume_card['created_at'] >= PastMonth4]['total']) - volume_card_CurrentMonth - volume_card_PastMonth - volume_card_PastMonth2 - volume_card_PastMonth3
            volume_card_PastMonth5 = np.sum(volume_card[volume_card['created_at'] >= PastMonth5]['total']) - volume_card_CurrentMonth - volume_card_PastMonth - volume_card_PastMonth2 - volume_card_PastMonth3 - volume_card_PastMonth4
            volume_card_PastMonth6 = np.sum(volume_card[volume_card['created_at'] >= PastMonth6]['total']) - volume_card_CurrentMonth - volume_card_PastMonth - volume_card_PastMonth2 - volume_card_PastMonth3 - volume_card_PastMonth4 - volume_card_PastMonth5
            volume_card_6monthtotal = np.sum(volume_card[volume_card['created_at'] >= PastMonth6]['total'])
    
            dfsalesvolume = pd.DataFrame({'Past Month 6':[volume_card_PastMonth6],
                                        'Past Month 5':[volume_card_PastMonth5],
                                        'Past Month 4':[volume_card_PastMonth4],
                                        'Past Month 3':[volume_card_PastMonth3],
                                        'Past Month 2':[volume_card_PastMonth2],
                                        'Past Month 1':[volume_card_PastMonth],
                                        'Current Month To Date':[volume_card_CurrentMonth],
                                        '6 month total':[volume_card_6monthtotal],
                                #        'lifetime_total':[volumetotal]
                                }, index=['Card Sales Amount'])
    
            card_counttotal = np.count_nonzero(volume_card['total'])
            card_countCurrentMonth = np.count_nonzero(volume_card[volume_card['created_at'] >= CurrentMonth]['total'])
            card_countPastMonth = np.count_nonzero(volume_card[volume_card['created_at'] >= PastMonth]['total']) - card_countCurrentMonth
            card_countPastMonth2 = np.count_nonzero(volume_card[volume_card['created_at'] >= PastMonth2]['total']) - card_countCurrentMonth - card_countPastMonth
            card_countPastMonth3 = np.count_nonzero(volume_card[volume_card['created_at'] >= PastMonth3]['total']) - card_countCurrentMonth - card_countPastMonth - card_countPastMonth2
            card_countPastMonth4 = np.count_nonzero(volume_card[volume_card['created_at'] >= PastMonth4]['total']) - card_countCurrentMonth - card_countPastMonth - card_countPastMonth2 - card_countPastMonth3
            card_countPastMonth5 = np.count_nonzero(volume_card[volume_card['created_at'] >= PastMonth5]['total']) - card_countCurrentMonth - card_countPastMonth - card_countPastMonth2 - card_countPastMonth3 - card_countPastMonth4
            card_countPastMonth6 = np.count_nonzero(volume_card[volume_card['created_at'] >= PastMonth6]['total']) - card_countCurrentMonth - card_countPastMonth - card_countPastMonth2 - card_countPastMonth3 - card_countPastMonth4 - card_countPastMonth5
            card_counttotalPastMonth6 = np.count_nonzero(volume_card[volume_card['created_at'] >= PastMonth6]['total'])
    
            dfsalescount = pd.DataFrame({'Past Month 6':[card_countPastMonth6],
                                        'Past Month 5':[card_countPastMonth5],
                                        'Past Month 4':[card_countPastMonth4],
                                        'Past Month 3':[card_countPastMonth3],
                                        'Past Month 2':[card_countPastMonth2],
                                        'Past Month 1':[card_countPastMonth],
                                        'Current Month To Date':[card_countCurrentMonth],
                                        '6 month total':[card_countPastMonth6],
                                #        'lifetime_total':[volumecounttotal]
                                }, index=['Card Sales Count'])
    
    
            volume90 = np.sum(volume[volume['created_at'] > days90]['total'])
            volume180 = np.sum(volume[volume['created_at'] > days180]['total'])
    
    
            #ACH Transactions
            ach_volume = df3.query("type == 'charge' & payment_method == 'bank'")
            ach_volumetotal = np.sum(ach_volume['total'])
            ach_volumeCurrentMonth = np.sum(ach_volume[ach_volume['created_at'] >= CurrentMonth]['total'])
            ach_volumePastMonth = np.sum(ach_volume[ach_volume['created_at'] >= PastMonth]['total']) - ach_volumeCurrentMonth
            ach_volumePastMonth2 = np.sum(ach_volume[ach_volume['created_at'] >= PastMonth2]['total']) - ach_volumeCurrentMonth - ach_volumePastMonth
            ach_volumePastMonth3 = np.sum(ach_volume[ach_volume['created_at'] >= PastMonth3]['total']) - ach_volumeCurrentMonth - ach_volumePastMonth - ach_volumePastMonth2
            ach_volumePastMonth4 = np.sum(ach_volume[ach_volume['created_at'] >= PastMonth4]['total']) - ach_volumeCurrentMonth - ach_volumePastMonth - ach_volumePastMonth2 - ach_volumePastMonth3
            ach_volumePastMonth5 = np.sum(ach_volume[ach_volume['created_at'] >= PastMonth5]['total']) - ach_volumeCurrentMonth - ach_volumePastMonth - ach_volumePastMonth2 - ach_volumePastMonth3 - ach_volumePastMonth4
            ach_volumePastMonth6 = np.sum(ach_volume[ach_volume['created_at'] >= PastMonth6]['total']) - ach_volumeCurrentMonth - ach_volumePastMonth - ach_volumePastMonth2 - ach_volumePastMonth3 - ach_volumePastMonth4 - ach_volumePastMonth5
            ach_volume6monthtotal = np.sum(ach_volume[ach_volume['created_at'] >= PastMonth6]['total'])
    
            dfachsalesvolume = pd.DataFrame({'Past Month 6':[ach_volumePastMonth6],
                                        'Past Month 5':[ach_volumePastMonth5],
                                        'Past Month 4':[ach_volumePastMonth4],
                                        'Past Month 3':[ach_volumePastMonth3],
                                        'Past Month 2':[ach_volumePastMonth2],
                                        'Past Month 1':[ach_volumePastMonth],
                                        'Current Month To Date':[ach_volumeCurrentMonth],
                                        '6 month total':[ach_volume6monthtotal],
                                #        'lifetime_total':[volumetotal]
                                }, index=['ACH Sales Amount'])
    
            ach_volumecounttotal = np.count_nonzero(ach_volume['total'])
            ach_countCurrentMonth = np.count_nonzero(ach_volume[ach_volume['created_at'] >= CurrentMonth]['total'])
            ach_countPastMonth = np.count_nonzero(ach_volume[ach_volume['created_at'] >= PastMonth]['total']) - ach_countCurrentMonth
            ach_countPastMonth2 = np.count_nonzero(ach_volume[ach_volume['created_at'] >= PastMonth2]['total']) - ach_countCurrentMonth - ach_countPastMonth
            ach_countPastMonth3 = np.count_nonzero(ach_volume[ach_volume['created_at'] >= PastMonth3]['total']) - ach_countCurrentMonth - ach_countPastMonth - ach_countPastMonth2
            ach_countPastMonth4 = np.count_nonzero(ach_volume[ach_volume['created_at'] >= PastMonth4]['total']) - ach_countCurrentMonth - ach_countPastMonth - ach_countPastMonth2 - ach_countPastMonth3
            ach_countPastMonth5 = np.count_nonzero(ach_volume[ach_volume['created_at'] >= PastMonth5]['total']) - ach_countCurrentMonth - ach_countPastMonth - ach_countPastMonth2 - ach_countPastMonth3 - ach_countPastMonth4
            ach_countPastMonth6 = np.count_nonzero(ach_volume[ach_volume['created_at'] >= PastMonth6]['total']) - ach_countCurrentMonth - ach_countPastMonth - ach_countPastMonth2 - ach_countPastMonth3 - ach_countPastMonth4 - ach_countPastMonth5
            ach_counttotalPastMonth6 = np.count_nonzero(ach_volume[ach_volume['created_at'] >= PastMonth6]['total'])
    
            dfachsalescount = pd.DataFrame({'Past Month 6':[ach_countPastMonth6],
                                        'Past Month 5':[ach_countPastMonth5],
                                        'Past Month 4':[ach_countPastMonth4],
                                        'Past Month 3':[ach_countPastMonth3],
                                        'Past Month 2':[ach_countPastMonth2],
                                        'Past Month 1':[ach_countPastMonth],
                                        'Current Month To Date':[ach_countCurrentMonth],
                                        '6 month total':[ach_counttotalPastMonth6],
                                #        'lifetime_total':[volumecounttotal]
                                }, index=['ACH Sales Count'])
    
    
         #   volume90 = np.sum(volume[volume['created_at'] > days90]['total'])
         #   volume180 = np.sum(volume[volume['created_at'] > days180]['total'])
    
    
    
    
    
            #Refund Values
    
            refund = df3.query("type == 'refund'")
    
            refundtotal = np.sum(refund['total'])
    
            refundCurrentMonth = np.absolute(np.sum(refund[refund['created_at'] >= CurrentMonth]['total']))
            refundCurrentMonth = np.absolute(refundCurrentMonth)
    
            refundPastMonth = np.absolute(np.sum(refund[refund['created_at'] >= PastMonth]['total'])) - refundCurrentMonth
            refundPastMonth = np.absolute(refundPastMonth)
    
            refundPastMonth2 = np.absolute(np.sum(refund[refund['created_at'] >= PastMonth2]['total'])) - refundCurrentMonth - refundPastMonth
            refundPastMonth2 = np.absolute(refundPastMonth2)
    
            refundPastMonth3 = np.absolute(np.sum(refund[refund['created_at'] >= PastMonth3]['total'])) - refundCurrentMonth - refundPastMonth - refundPastMonth2
            refundPastMonth3 = np.absolute(refundPastMonth3)
    
            refundPastMonth4 = np.absolute(np.sum(refund[refund['created_at'] >= PastMonth4]['total'])) - refundCurrentMonth - refundPastMonth - refundPastMonth2 - refundPastMonth3
            refundPastMonth4 = np.absolute(refundPastMonth4)
    
            refundPastMonth5 = np.absolute(np.sum(refund[refund['created_at'] >= PastMonth5]['total'])) - refundCurrentMonth - refundPastMonth - refundPastMonth2 - refundPastMonth3 - refundPastMonth4
            refundPastMonth5 = np.absolute(refundPastMonth5)
    
            refundPastMonth6 = np.absolute(np.sum(refund[refund['created_at'] >= PastMonth6]['total'])) - refundCurrentMonth - refundPastMonth - refundPastMonth2 - refundPastMonth3 - refundPastMonth4 - refundPastMonth5
            refundPastMonth6 = np.absolute(refundPastMonth6)
    
            refundtotalPastMonth6 = refundCurrentMonth + refundPastMonth + refundPastMonth2 + refundPastMonth3 + refundPastMonth4 + refundPastMonth5 + refundPastMonth6
            refundtotalPastMonth6 = np.absolute(refundtotalPastMonth6)
    
            dfrefundamount = pd.DataFrame({'Past Month 6':[refundPastMonth6],
                                        'Past Month 5':[refundPastMonth5],
                                        'Past Month 4':[refundPastMonth4],
                                        'Past Month 3':[refundPastMonth3],
                                        'Past Month 2':[refundPastMonth2],
                                        'Past Month 1':[refundPastMonth],
                                        'Current Month To Date':[refundCurrentMonth],
                                        '6 month total':[refundtotalPastMonth6],
                                #        'lifetime_total':[refundtotal]
                                }, index=['Refund Amount'])
    
            refundcounttotal = np.count_nonzero(refund['total'])
    
            refundCountCurrentMonth = np.count_nonzero(refund[refund['created_at'] >= CurrentMonth]['total'])
    
            refundCountPastMonth = np.count_nonzero(refund[refund['created_at'] >= PastMonth]['total']) - refundCountCurrentMonth
    
            refundCountPastMonth2 = np.count_nonzero(refund[refund['created_at'] >= PastMonth2]['total']) - refundCountCurrentMonth - refundCountPastMonth
    
            refundCountPastMonth3 = np.count_nonzero(refund[refund['created_at'] >= PastMonth3]['total']) - refundCountCurrentMonth - refundCountPastMonth - refundCountPastMonth2
    
            refundCountPastMonth4 = np.count_nonzero(refund[refund['created_at'] >= PastMonth4]['total']) - refundCountCurrentMonth - refundCountPastMonth - refundCountPastMonth2 - refundCountPastMonth3
    
            refundCountPastMonth5 = np.count_nonzero(refund[refund['created_at'] >= PastMonth5]['total']) - refundCountCurrentMonth - refundCountPastMonth - refundCountPastMonth2 - refundCountPastMonth3 - refundCountPastMonth4
    
            refundCountPastMonth6 = np.count_nonzero(refund[refund['created_at'] >= PastMonth6]['total']) - refundCountCurrentMonth - refundCountPastMonth - refundCountPastMonth2 - refundCountPastMonth3 - refundCountPastMonth4 - refundCountPastMonth5
    
            refundCounttotalPastMonth6 = np.count_nonzero(refund[refund['created_at'] >= PastMonth6]['total'])
    
            dfrefundcount = pd.DataFrame({'Past Month 6':[refundCountPastMonth6],
                                        'Past Month 5':[refundCountPastMonth5],
                                        'Past Month 4':[refundCountPastMonth4],
                                        'Past Month 3':[refundCountPastMonth3],
                                        'Past Month 2':[refundCountPastMonth2],
                                        'Past Month 1':[refundCountPastMonth],
                                        'Current Month To Date':[refundCountCurrentMonth],
                                        '6 month total':[refundCounttotalPastMonth6],
                                #        'lifetime_total':[refundcounttotal]
                                }, index=['Refund Count'])
    
            #Average Ticket
    
            avgcounttotal = np.average(volume['total'])
    
            avgCurrentMonth = np.average(volume[volume['created_at'] >= CurrentMonth]['total'])
    
            avgPastMonth = np.average(volume[(volume['created_at'] >= PastMonth) & (volume['created_at'] < CurrentMonth) ]['total'])
    
            avgPastMonth2 = np.average(volume[(volume['created_at'] >= PastMonth2) & (volume['created_at'] < PastMonth)  ]['total'])
    
            avgPastMonth3 = np.average(volume[(volume['created_at'] >= PastMonth3) &  (volume['created_at'] < PastMonth2)]['total'])
    
            avgPastMonth4 = np.average(volume[(volume['created_at'] >= PastMonth4) &  (volume['created_at'] < PastMonth3)]['total'])
    
            avgPastMonth5 = np.average(volume[(volume['created_at'] >= PastMonth5) & (volume['created_at'] < PastMonth4)]['total'])
    
            avgPastMonth6 = np.average(volume[(volume['created_at'] >= PastMonth6) & (volume['created_at'] < PastMonth5)]['total'])
    
            avgtotalPastMonth6 = np.average(volume[volume['created_at'] >= PastMonth6]['total'])
    
            dfavgsalescount = pd.DataFrame({'Past Month 6':[avgPastMonth6],
                                        'Past Month 5':[avgPastMonth5],
                                        'Past Month 4':[avgPastMonth4],
                                        'Past Month 3':[avgPastMonth3],
                                        'Past Month 2':[avgPastMonth2],
                                        'Past Month 1':[avgPastMonth],
                                        'Current Month To Date':[avgCurrentMonth],
                                        '6 month total':[avgcounttotal],
                                #        'lifetime_total':[avgtotalPastMonth6]
                                }, index=['Average Ticket'])
    
            #add in high ticket
    
            highesttran = np.max(volume['total'])
    
            highesttranCurrentMonth = np.max(volume[volume['created_at'] >= CurrentMonth]['total'])
    
            highesttranPastMonth = np.max(volume[(volume['created_at'] >= PastMonth) & (volume['created_at'] < CurrentMonth) ]['total'])
    
            highesttranPastMonth2 = np.max(volume[(volume['created_at'] >= PastMonth2) & (volume['created_at'] < PastMonth)  ]['total'])
    
            highesttranPastMonth3 = np.max(volume[(volume['created_at'] >= PastMonth3) &  (volume['created_at'] < PastMonth2)]['total'])
    
            highesttranPastMonth4 = np.max(volume[(volume['created_at'] >= PastMonth4) &  (volume['created_at'] < PastMonth3)]['total'])
    
            highesttranPastMonth5 = np.max(volume[(volume['created_at'] >= PastMonth5) & (volume['created_at'] < PastMonth4)]['total'])
    
            highesttranPastMonth6 = np.max(volume[(volume['created_at'] >= PastMonth6) & (volume['created_at'] < PastMonth5)]['total'])
    
            highesttrantotalPastMonth6 = np.max(volume[volume['created_at'] >= PastMonth6]['total'])
    
            dfhighesttrans = pd.DataFrame({'Past Month 6':[highesttranPastMonth6],
                                        'Past Month 5':[highesttranPastMonth5],
                                        'Past Month 4':[highesttranPastMonth4],
                                        'Past Month 3':[highesttranPastMonth3],
                                        'Past Month 2':[highesttranPastMonth2],
                                        'Past Month 1':[highesttranPastMonth],
                                        'Current Month To Date':[highesttranCurrentMonth],
                                        '6 month total':[highesttrantotalPastMonth6],
                                #        'lifetime_total':[highesttran]
                                }, index=['Highest Transaction'])
            
    
            #add in amount of highesttran, groupby high ticket?
    
            highticketcountCurrentMonth = np.count_nonzero((volume['created_at'] >= CurrentMonth) & (volume['total'] == highesttranCurrentMonth))
    
            highticketcountPastMonth = np.count_nonzero((volume['created_at'] >= PastMonth) & (volume['created_at'] < CurrentMonth) & (volume['total'] == highesttranPastMonth))
    
            highticketcountPastMonth2 = np.count_nonzero((volume['created_at'] >= PastMonth2) & (volume['created_at'] < PastMonth) & (volume['total'] == highesttranPastMonth2))
    
            highticketcountPastMonth3 = np.count_nonzero((volume['created_at'] >= PastMonth3) & (volume['created_at'] < PastMonth2) & (volume['total'] == highesttranPastMonth3))
    
            highticketcountPastMonth4 = np.count_nonzero((volume['created_at'] >= PastMonth4) & (volume['created_at'] < PastMonth3) & (volume['total'] == highesttranPastMonth4))
    
            highticketcountPastMonth5 = np.count_nonzero((volume['created_at'] >= PastMonth5) & (volume['created_at'] < PastMonth4) & (volume['total'] == highesttranPastMonth5))
    
            highticketcountPastMonth6 = np.count_nonzero((volume['created_at'] >= PastMonth6) & (volume['created_at'] < PastMonth5) & (volume['total'] == highesttranPastMonth6))
    
            highticketcounttotalPastMonth6 = np.count_nonzero((volume['created_at'] >= PastMonth6) & (volume['total'] == highesttrantotalPastMonth6))
    
            dfhighesttranscount = pd.DataFrame({'Past Month 6':[highticketcountPastMonth6],
                                        'Past Month 5':[highticketcountPastMonth5],
                                        'Past Month 4':[highticketcountPastMonth4],
                                        'Past Month 3':[highticketcountPastMonth3],
                                        'Past Month 2':[highticketcountPastMonth2],
                                        'Past Month 1':[highticketcountPastMonth],
                                        'Current Month To Date':[highticketcountCurrentMonth],
                                        '6 month total':[highticketcounttotalPastMonth6],
            }, index=['Highest Transaction Count'])
    
    
            #add in 20% range of highest tran
    
    
            highticketcount20PercentLowerCurrentMonth = np.count_nonzero((volume['created_at'] >= CurrentMonth) & (volume['total'] >= highesttranCurrentMonth * 0.8))
    
            highticketcount20PercentLowerPastMonth = np.count_nonzero((volume['created_at'] >= PastMonth) & (volume['created_at'] < CurrentMonth) & (volume['total'] >= highesttranPastMonth * 0.8))
    
            highticketcount20PercentLowerPastMonth2 = np.count_nonzero((volume['created_at'] >= PastMonth2) & (volume['created_at'] < PastMonth) & (volume['total'] >= highesttranPastMonth2 * 0.8))
    
            highticketcount20PercentLowerPastMonth3 = np.count_nonzero((volume['created_at'] >= PastMonth3) & (volume['created_at'] < PastMonth2) & (volume['total'] >= highesttranPastMonth3 * 0.8))
    
            highticketcount20PercentLowerPastMonth4 = np.count_nonzero((volume['created_at'] >= PastMonth4) & (volume['created_at'] < PastMonth3) & (volume['total'] >= highesttranPastMonth4 * 0.8))
    
            highticketcount20PercentLowerPastMonth5 = np.count_nonzero((volume['created_at'] >= PastMonth5) & (volume['created_at'] < PastMonth4) & (volume['total'] >= highesttranPastMonth5 * 0.8))
    
            highticketcount20PercentLowerPastMonth6 = np.count_nonzero((volume['created_at'] >= PastMonth6) & (volume['created_at'] < PastMonth5) & (volume['total'] >= highesttranPastMonth6 * 0.8))
    
            highticketcount20PercentLowertotalPastMonth6 = np.count_nonzero((volume['created_at'] >= PastMonth6) & (volume['total'] >= highesttrantotalPastMonth6 * 0.8))
    
            dfhighesttranscount20percent = pd.DataFrame({'Past Month 6':[highticketcount20PercentLowerPastMonth6],
                                        'Past Month 5':[highticketcount20PercentLowerPastMonth5],
                                        'Past Month 4':[highticketcount20PercentLowerPastMonth4],
                                        'Past Month 3':[highticketcount20PercentLowerPastMonth3],
                                        'Past Month 2':[highticketcount20PercentLowerPastMonth2],
                                        'Past Month 1':[highticketcount20PercentLowerPastMonth],
                                        'Current Month To Date':[highticketcount20PercentLowerCurrentMonth],
                                        '6 month total':[highticketcount20PercentLowertotalPastMonth6],
            }, index=['Highest Transaction Count 20% Percent Range'])     
            
    
    
    
    
    
    
            if (ach_volumePastMonth6 + volume_card_PastMonth6) > 0: 
                refundamountmonth6 = (refundPastMonth6 / (ach_volumePastMonth6 + volume_card_PastMonth6))
            else: 
                refundamountmonth6 = 0
    
            if (ach_volumePastMonth5 + volume_card_PastMonth5) > 0: 
                refundamountmonth5 = (refundPastMonth5 / (ach_volumePastMonth5 + volume_card_PastMonth5))
            else: 
                refundamountmonth5 = 0
    
            if (ach_volumePastMonth4 + volume_card_PastMonth4) > 0: 
                refundamountmonth4 = (refundPastMonth4 / (ach_volumePastMonth4 + volume_card_PastMonth4))
            else: 
                refundamountmonth4 = 0
    
            if (ach_volumePastMonth3 + volume_card_PastMonth3) > 0: 
                refundamountmonth3 = (refundPastMonth3 / (ach_volumePastMonth3 + volume_card_PastMonth3))
            else: 
                refundamountmonth3 = 0
    
            if (ach_volumePastMonth2 + volume_card_PastMonth2) > 0: 
                refundamountmonth2 = (refundPastMonth2 / (ach_volumePastMonth2 + volume_card_PastMonth2))
            else: 
                refundamountmonth2 = 0
    
            if (ach_volumePastMonth + volume_card_PastMonth) > 0: 
                refundamountmonth = (refundPastMonth / (ach_volumePastMonth + volume_card_PastMonth))
            else: 
                refundamountmonth = 0
    
            if (ach_volumeCurrentMonth + volume_card_CurrentMonth) > 0: 
                refundamountcurrentmonth = (refundCurrentMonth / (ach_volumeCurrentMonth + volume_card_CurrentMonth))
            else: 
                refundamountcurrentmonth = 0
    
            if (ach_volume6monthtotal + volume_card_6monthtotal) > 0: 
                refundamount6month = (refundtotalPastMonth6 / (ach_volume6monthtotal + volume_card_6monthtotal))
            else: 
                refundamount6month = 0
    
            if (ach_volumetotal + volume_card_total) > 0: 
                refundamounttotal = (refundtotal / (ach_volumetotal + volume_card_total))
            else: 
                refundamounttotal = 0
    
            dfrefundamountpercent = pd.DataFrame({'Past Month 6':[refundamountmonth6],
                                 'Past Month 5':[refundamountmonth5],
                                 'Past Month 4':[refundamountmonth4],
                                 'Past Month 3':[refundamountmonth3],
                                 'Past Month 2':[refundamountmonth2],
                                 'Past Month 1':[refundamountmonth],
                                 'Current Month To Date':[refundamountcurrentmonth],
                                 '6 month total':[refundamount6month],
                           #      'lifetime_total':[refundamounttotal]
                           }, index=['Refund Amount Ratio'])
    
    
    
    
            
            if (ach_countPastMonth6 + card_countPastMonth6) > 0: 
                refundcountpercentmonth6 = (refundCountPastMonth6 / (ach_countPastMonth6 + card_countPastMonth6))
            else: 
                refundcountpercentmonth6 = 0
    
            if (ach_countPastMonth5 + card_countPastMonth5) > 0: 
                refundcountpercentmonth5 = (refundCountPastMonth5 / (ach_countPastMonth5 + card_countPastMonth5))
            else: 
                refundcountpercentmonth5 = 0
    
            if (ach_countPastMonth4 + card_countPastMonth4) > 0: 
                refundcountpercentmonth4 = (refundCountPastMonth4 / (ach_countPastMonth4 + card_countPastMonth4))
            else: 
                refundcountpercentmonth4 = 0
    
            if (ach_countPastMonth3 + card_countPastMonth3) > 0: 
                refundcountpercentmonth3 = (refundCountPastMonth3 / (ach_countPastMonth3 + card_countPastMonth3))
            else: 
                refundcountpercentmonth3 = 0
    
            if (ach_countPastMonth2 + card_countPastMonth2) > 0: 
                refundcountpercentmonth2 = (refundCountPastMonth2 / (ach_countPastMonth2 + card_countPastMonth2))
            else: 
                refundcountpercentmonth2 = 0
    
            if (ach_countPastMonth + card_countPastMonth) > 0: 
                refundcountpercentmonth = (refundCountPastMonth / (ach_countPastMonth + card_countPastMonth))
            else: 
                refundcountpercentmonth = 0
    
            if (ach_countCurrentMonth + card_countCurrentMonth) > 0: 
                refundcountpercentcurrentmonth = (refundCountCurrentMonth / (ach_countCurrentMonth + card_countCurrentMonth))
            else: 
                refundcountpercentcurrentmonth = 0
    
            if (ach_counttotalPastMonth6 + card_counttotalPastMonth6) > 0: 
                refundcountpercent6month = (refundCounttotalPastMonth6 / (ach_counttotalPastMonth6 + card_counttotalPastMonth6))
            else: 
                refundcountpercent6month = 0
    
            if (ach_volumecounttotal + card_counttotalPastMonth6) > 0: 
                refundcountpercenttotal = (refundcounttotal / (ach_volumecounttotal + card_counttotalPastMonth6))
            else: 
                refundcountpercenttotal = 0
    
    
    
            dfrefundpercentcount = pd.DataFrame({'Past Month 6':[refundcountpercentmonth6],
                                 'Past Month 5':[refundcountpercentmonth5],
                                 'Past Month 4':[refundcountpercentmonth4],
                                 'Past Month 3':[refundcountpercentmonth3],
                                 'Past Month 2':[refundcountpercentmonth2],
                                 'Past Month 1':[refundcountpercentmonth],
                                 'Current Month To Date':[refundcountpercentcurrentmonth],
                                 '6 month total':[refundcountpercent6month],
                           #      'lifetime_total':[refundcountpercenttotal]
                           }, index=['Refund Count Ratio'])
    
            Chargeback_Amount = pd.DataFrame({'Past Month 6': '',
                                 'Past Month 5':'',
                                 'Past Month 4':'',
                                 'Past Month 3':'',
                                 'Past Month 2':'',
                                 'Past Month 1':'',
                                 'Current Month To Date':'',
                                 '6 month total':'',
                            #     'lifetime_total':'',
                           }, index=['Chargeback Amount'])
            
            Chargeback_Amount_Ratio = pd.DataFrame({'Past Month 6': '',
                                 'Past Month 5':'',
                                 'Past Month 4':'',
                                 'Past Month 3':'',
                                 'Past Month 2':'',
                                 'Past Month 1':'',
                                 'Current Month To Date':'',
                                 '6 month total':'',
                            #     'lifetime_total':'',
                           }, index=['Chargeback Amount Ratio'])
    
            Chargeback_Count = pd.DataFrame({'Past Month 6': '',
                                 'Past Month 5':'',
                                 'Past Month 4':'',
                                 'Past Month 3':'',
                                 'Past Month 2':'',
                                 'Past Month 1':'',
                                 'Current Month To Date':'',
                                 '6 month total':'',
                            #     'lifetime_total':'',
                           }, index=['Chargeback Count'])
            
            Chargeback_Count_Ratio = pd.DataFrame({'Past Month 6': '',
                                 'Past Month 5':'',
                                 'Past Month 4':'',
                                 'Past Month 3':'',
                                 'Past Month 2':'',
                                 'Past Month 1':'',
                                 'Current Month To Date':'',
                                 '6 month total':'',
                           #      'lifetime_total':'',
                           }, index=['Chargeback Count Ratio'])
            
            format_mapping_dollars = {'Past Month 6': '${:,.2f}',
                                 'Past Month 5': '${:,.2f}',
                                 'Past Month 4': '${:,.2f}',
                                 'Past Month 3': '${:,.2f}',
                                 'Past Month 2': '${:,.2f}',
                                 'Past Month 1': '${:,.2f}',
                                 'Current Month To Date': '${:,.2f}',
                                 '6 month total':'${:,.2f}'}
    
            for key, value in format_mapping_dollars.items():
                dfsalesvolume[key] = dfsalesvolume[key].apply(value.format)
                dfachsalesvolume[key] = dfachsalesvolume[key].apply(value.format)
                dfrefundamount[key] = dfrefundamount[key].apply(value.format)
                dfavgsalescount[key] = dfavgsalescount[key].apply(value.format)
                dfhighesttrans[key] = dfhighesttrans[key].apply(value.format)
    
            format_mapping_percent = {'Past Month 6': '{:.2%}',
                                 'Past Month 5': '{:.2%}',
                                 'Past Month 4': '{:.2%}',
                                 'Past Month 3': '{:.2%}',
                                 'Past Month 2': '{:.2%}',
                                 'Past Month 1': '{:.2%}',
                                 'Current Month To Date': '{:.2%}',
                                 '6 month total':'{:.2%}'}
    
            for key, value in format_mapping_percent.items():
                dfrefundamountpercent[key] = dfrefundamountpercent[key].apply(value.format)
                dfrefundpercentcount[key] = dfrefundpercentcount[key].apply(value.format)    
    
            dflastersresults = pd.concat([dfsalesvolume, dfsalescount, dfachsalesvolume, dfachsalescount, Chargeback_Amount, Chargeback_Amount_Ratio, Chargeback_Count, Chargeback_Count_Ratio, dfrefundamount, dfrefundamountpercent, dfrefundcount, dfrefundpercentcount, dfavgsalescount, dfhighesttrans, dfhighesttranscount, dfhighesttranscount20percent], axis=0)
    
    
    
            dfcalc = pd.DataFrame({'Refunds for past 90 days':[refund90],
                            '90 day volume':[volume90],
                            '90 day refund rate':[day90_refund_rate],
                            'Lifetime refunds':[refundtotal],
                            'Lifetime volume':[volumetotal],
                            'Lifetime Lifetime_refund_rate ':[Lifetime_refund_rate],
                            'Chargebacks for past 180 days':[chargebacks180],
                            '180 day card volume':[card180days],
                            '180 day chargeback rate':[day180_chargeback_rate],
                            'Lifetime chargebacks':[chargebackslifetime],
                            'Lifetime card volume':[cardtotal],
                            'Lifetime chargeback rate':[Lifetime_chargeback_rate],
                            '90 Days':[days90],
                            '180 Days':[days180],
                            })
    
            format_mapping = {'Refunds for past 90 days':'${:,.2f}',
                            '90 day volume':'${:,.2f}',
                            '90 day refund rate':'{:.2%}',
                            'Lifetime refunds':'${:,.2f}',
                            'Lifetime volume':'${:,.2f}',
                            'Lifetime Lifetime_refund_rate ':'{:.2%}',
                            'Chargebacks for past 180 days':'${:,.2f}',
                            '180 day card volume':'${:,.2f}',
                            '180 day chargeback rate':'{:.2%}',
                            'Lifetime chargebacks':'${:,.2f}',
                            'Lifetime card volume':'${:,.2f}',
                            'Lifetime chargeback rate':'{:.2%}',
                            }
    
            for key, value in format_mapping.items():
                dfcalc[key] = dfcalc[key].apply(value.format)
    
            df4['total'] = df4['total'].apply('${:,.0f}'.format)
    
            #month change into automatic
            #column_names = [(current_date - timedelta(days=30 * i)).strftime("%B") for i in range(6)]
            #data = {name: [random.randint(1, 100) for _ in range(10)] for name in column_names}
    
            new_column_names = {
            'Past Month 6': (date.today() - timedelta(days=30 * 6)).strftime("%B %Y"),
            'Past Month 5': (date.today() - timedelta(days=30 * 5)).strftime("%B %Y"),
            'Past Month 4': (date.today() - timedelta(days=30 * 4)).strftime("%B %Y"),
            'Past Month 3': (date.today() - timedelta(days=30 * 3)).strftime("%B %Y"),
            'Past Month 2': (date.today() - timedelta(days=30 * 2)).strftime("%B %Y"),
            'Past Month 1': (date.today() - timedelta(days=30 * 1)).strftime("%B %Y"),
            'Current Month To Date': (date.today() - timedelta(days=30 * 0)).strftime("%B %Y")}
            
            dflastersresults.rename(columns=new_column_names, inplace=True)
    
            objects_to_download = {
                "Clean_Data": df4,
                "History": dflastersresults,
                "Calculations": dfcalc,
            }
    
            download_link = download_button(objects_to_download, st.session_state.filename)
            if download_link:
                st.markdown(download_link, unsafe_allow_html=True)
            else:
                st.error("File download failed.")
    
    if __name__ == "__main__":
        uploaded_files = None
        st.title("Refund & Chargebacks Breakdown")
    
        with st.form("my_form", clear_on_submit=True):
            st.text_input("Filename (must include .xlsx)", key="filename")
            chargebacks180 = st.number_input("Enter Chargebacks For 180 Days", key="chargebacks180")
            chargebackslifetime = st.number_input("Enter Chargebacks for Lifetime", key="chargebackslifetime")
            uploaded_files = st.file_uploader("Upload CSV", type="csv", accept_multiple_files=True)
            submit = st.form_submit_button("Download dataframe")
    
        if submit:
            download_df()
