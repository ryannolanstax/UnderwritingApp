import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import json
import numpy as np
import datetime
from datetime import date, timedelta
import io
from auth_utils import require_role, get_user_info
import sys
import os
import re




st.set_page_config(page_title="Transactions", page_icon="🛍️")

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
            dfpreclean = pd.concat(uploaded_data_read)
    
            highticketval = highticketstring
    
            dfprecleanv1 = dfpreclean.query("success == 1 and source != 'intuit'")
    
            dfprecleanv1.drop(['id','merchant_id','user_id','customer_id','subtotal','tax','is_manual','success','donation','tip','meta','pre_auth','updated_at','source'], axis=1, inplace=True)
            dfpreclean2 = dfprecleanv1[(dfprecleanv1['type'].isna() == False) & (dfprecleanv1['total'].isna() == False)]
            dfpreclean3 = dfpreclean2[(dfpreclean2['payment_method'] == 'card') | (dfpreclean2['payment_method'] == 'bank')]
            dfpreclean4 = dfpreclean3[dfpreclean3['type'] == 'charge']
            dfpreclean4["channel"].fillna("blank", inplace = True)
            dfpreclean4["memo"].fillna("blank", inplace = True)
            dfpreclean4["payment_note"].fillna("blank", inplace = True)
    
            df = dfpreclean4.loc[:,['created_at', 'total', 'payment_person_name', 'customer_firstname', 'customer_lastname',\
                    'payment_last_four', 'payment_method', 'memo', 'payment_note', 'type', 'last_four', 'channel', 'reference', \
                    'issuer_auth_code', 'payment_card_type', 'payment_card_exp', 'payment_bank_name', 'payment_bank_type',\
                    'payment_bank_holder_type', 'billing_address_1', 'billing_address_2','billing_address_city', \
                    'billing_address_state', 'billing_address_zip', 'customer_company','customer_email', 'customer_phone', \
                    'customer_address_1','customer_address_2', 'customer_address_city', 'customer_address_state', \
                    'customer_address_zip', 'customer_notes', 'customer_reference', 'customer_created_at', \
                    'customer_updated_at', 'customer_deleted_at', 'gateway_id', 'gateway_name', 'gateway_type', \
                    'gateway_created_at', 'gateway_deleted_at', 'user_name', 'system_admin', 'user_created_at',\
                    'user_updated_at', 'user_deleted_at']]
    
            totalsum = np.sum(df['total'])
    
            total_transactions = df['type'].count()
            total_transactions_month = total_transactions / 12
            mean_transaction = np.mean(df['total'])
            median_transaction = np.median(df['total'])
            max_transaction_card = df.loc[df['payment_method'] == 'card', 'total'].max()
            max_transaction_ach = df.loc[df['payment_method'] == 'bank', 'total'].max()
            total_unique_customer_last_four = df['payment_last_four'].nunique()
            total_unique_customer_names = df['payment_person_name'].nunique()
    
            dfgroupname = df.groupby(['payment_person_name']).agg(
                    tran_count=('total', 'count'),
                    tran_sum=('total', np.sum)
            )
    
            dfgrouplastfour = df.groupby(['payment_last_four']).agg(
                    tran_count=('total', 'count'),
                    tran_sum=('total', np.sum)
            )
    
            avg_transactions_count_per_customer_name = np.mean(dfgroupname['tran_count'])
            avg_transactions_sum_per_customer_name = np.mean(dfgroupname['tran_sum'])
            avg_transactions_count_per_customer_last_four = np.mean(dfgrouplastfour['tran_count'])
            avg_transactions_sum_per_customer_last_four = np.mean(dfgrouplastfour['tran_sum'])
    
            dfcalc = pd.DataFrame({
                           #     'totalsum':[totalsum],
                                'mean_transaction':[mean_transaction],
                           #     'median_transaction':[median_transaction], 
                                'max_transaction_card':[max_transaction_card],
                                'max_transaction_ach':[max_transaction_ach],
                                'total_transactions':[total_transactions],
                                'total_unique_customer_names':[total_unique_customer_names], 
                                'total_unique_customer_last_four':[total_unique_customer_last_four],
                                'total_transactions_month':[total_transactions_month],                                                
                                'avg_transactions_count_per_customer_name':[avg_transactions_count_per_customer_name],
                            #    'avg_transactions_sum_per_customer_name':[avg_transactions_sum_per_customer_name],
                                'avg_transactions_count_per_customer_last_four':[avg_transactions_count_per_customer_last_four],
                            #    'avg_transactions_sum_per_customer_last_four':[avg_transactions_sum_per_customer_last_four]
                                })
    
            format_mapping = {
                            #"totalsum": '${:,.2f}',
                            "mean_transaction": '${:,.2f}',
                         #   "median_transaction": '${:,.2f}',
                            "max_transaction_card": '${:,.2f}',
                            "max_transaction_ach": '${:,.2f}',
                            "total_transactions": '{:,.0f}', 
                            "total_unique_customer_names": '{:,.0f}',
                            "total_unique_customer_last_four": '{:,.0f}',
                            "total_transactions_month": '{:,.2f}',                
                            "avg_transactions_count_per_customer_name": '{:,.2f}',
                        #    "avg_transactions_sum_per_customer_name": '${:,.2f}',                                 
                            "avg_transactions_count_per_customer_last_four": '{:,.2f}',
                       #     "avg_transactions_sum_per_customer_last_four": '${:,.2f}' 
                            }
    
            for key, value in format_mapping.items():
                    dfcalc[key] = dfcalc[key].apply(value.format)
    
            #Can you make this tab look like the "Pivot Table 1" tab to the right of it that I manually created?  I also uploaded my source CSV file.
            pivottablenames = pd.pivot_table(df, index=['payment_person_name'], aggfunc={'total': np.sum, 'payment_person_name': 'count',})
            pivottablenames = pivottablenames.rename(columns={"payment_person_name": "count_of_total", "total": "sum_of_total"})
            pivottablenames = pivottablenames.loc[:,['sum_of_total', 'count_of_total']]
            pivottablenames['sum_of_total'] = pivottablenames['sum_of_total'].apply('${:,.2f}'.format)
    
            pivottablelastfour = pd.pivot_table(df, index=['payment_last_four'], aggfunc={ 'total': np.sum, 'payment_last_four': 'count'})
            pivottablelastfour = pivottablelastfour.rename(columns={"payment_last_four": "count_of_total", "total": "sum_of_total"})
            pivottablelastfour = pivottablelastfour.loc[:,['sum_of_total', 'count_of_total']]
            pivottablelastfour['sum_of_total'] = pivottablelastfour['sum_of_total'].apply('${:,.2f}'.format)
    
            pivottablechannel = pd.pivot_table(df, index=['channel'], aggfunc={'payment_last_four': 'count', 'total': np.sum})
            pivottablechannel['totalpercent'] = (pivottablechannel['total']/totalsum).apply('{:.2%}'.format)
            pivottablechannel['total'] = pivottablechannel['total'].apply('${:,.2f}'.format)
    
            payment_note = df[df['payment_note'].isna() == False]
            flagged_words = '2024|2025|2026|late|delinquent|month|months|quarter|year|CBD|medicine|drugs|\
                            loan|bail|bond|bankruptcy|bankrupt|18|21|vape|weed|career|advice|date|dating\
                            tinder|bumble|escort|sex|massage|vibrator|solar|solar panel|warranty|warranties\
                            Cuba|Iran|North Korea|Sudan|Syria|penny|credit|identity|currency|crypto|bitcoin|\
                            Ethereum|nft|Cryptocurrencies|Tether|bnb|xrp|dogecoin|cardano|solano|tron|polygon|\
                            debt|cruise|airplane|jet|charter|Tobacco|Cigarettes|egic|cigarette|theft|elimination|\
                            eliminate|reduce|reduction|colsult|consulting|wallet|prepaid|commodity|security|trading\
                            toy|airline|airplane|collection|enhance|occult|psychic|future|discount|Ammunition|gun|\
                            Silencers|Suppressors|ammo|supplement|Nutraceuticals|enhance|growth|stock|equity|donation|\
                            shipping|forwarding|adult|xxx|bride|occult|mail order|mailorder|restricted|video|penny|bidding|\
                            bid|travel|Telemarketing|videotext|membership|club|coupon|insurance|dental|dentist|Distressed|\
                            property|gamble|gambling|lottery|lotteries|gaming|fantasy|contest|sweepstake|incentive|prize|\
                            lending|interest|title|loan|investment|rich|alcohol|beer|wine|liquor|pharmacy|Pharmacies|marijuana|\
                            420|Infomercial|pawn|rebate|timeshare|time shares|resale|resell|sports|odds|forecasting|up sell|upsell|\
                            upsale|rich|quick|broker|deal|fast|dispensaries|dispensary|money|transfer|wire|transmitter|check|cashing|\
                            cash|mlm|Multi-Level Marketing|pre paid|prepaid|phone|flip|flipping|real estate|realestate|mobile|\
                            virtual|credit|re-sold|meta|Pharmaceuticals|Quasi|social|free|period|negative|reputation|subscription|\
                            trial|pay only for shipping'
    
            payment_note_final = payment_note[payment_note['payment_note'].str.contains(flagged_words, case=False)]
    
            memo = df[df['memo'].isna() == False]
            badwords = 'bbb|yelp|fraud|scam|report|sloppy|shady|broken|imporsonation|\
                        bad|not working|shady|horrible|negative|rotten|poor|terrible|\
                        abysmal|awful|inaccurate|low quality|mediocre|nasty|abuse|worst|\
                        worse|angry|pissed|disgusting|no show|alarming|atrocious|adverse|\
                        alarming|angry|annoy|anxious|apathy|appalling|banal|barbed|belligerent|\
                        bemoan|beneath|boring|broken|callous|cant|clumsy|coarse|cold|cold-hearted|\
                        collapse|confused|contradictory|contrary|corrosive|corrupt|crazy|creepy|\
                        criminal|cruel|cry|cutting|damaged|damage|damaging|dastardly|dead|decaying|\
                        deformed|deny|deplorable|depressed|deprived|despicable|detrimental|dirty|\
                        disease|disgusting|disheveled|dishonest|dishonorable|dismal|distress|dont|\
                        dreadful|dreary|enraged|eroding|evil|fail|failing|faulty|fear|feeble|fight|\
                        filthy|foul|frighten|frightful|gawky|ghastly|grave|greed|greedy|grim|grimace|\
                        gross|grotesque|gruesome|guilty|haggard|hard|hard-hearted|harmful|hate|hideous|\
                        homely|horrendous|horrible|hostile|hurt|hurtful|icky|ignorant|ignore|ill|immature|\
                        imperfect|impossible|inane|inelegant|infernal|injure|injurious|insane|insidious|\
                        insipid|jealous|junk|lose|lousy|lumpy|malicious|mean|menacing|messy|misshapenmissing|\
                        misunderstood|moan|moldy|monstrous|naive|nasty|naughty|negate|negative|never|nonobody|\
                        nondescript|nonsense|not|noxious|objectionable|odious|offensive|old|oppressive|pain|\
                        perturb|pessimistic|petty|plain|poisonous|poor|prejudice|questionable|quirky|quit|\
                        reject|renege|repellant|repell|reptilian|repugnant|repulsive|revenge|revolting|rocky\
                        |rotten|rude|ruthless|sad|savage|scare|scary|scream|severe|shocking|shoddy|sick|sickening|\
                        sinister|slimy|smelly|sobbing|sorry|spiteful|sticky|stinky|stormy|stressful|stuck|stupid|\
                        substandard|suspect|suspicious|tense|terrible|terrifying|threatening|ugly|undermine|unfair|\
                        unfavorable|unhappy|unhealthy|unjust|unlucky|unpleasant|unsatisfactory|unsightly|untoward|\
                        unwanted|unwelcome|unwholesome|unwieldy|unwise|upset|vice|vicious|vile|villainous|vindictive|\
                        wary|weary|wicked|woeful|worthless|wound|yell|yucky|zero'
    
            memofinal = memo[memo['memo'].str.contains(badwords, case=False)]
    
            highticket = df[df['total'] >= highticketval]
            highticket = highticket.loc[:,['payment_person_name', 'customer_firstname', 'customer_lastname', 'created_at', 'total', \
                        'payment_last_four', 'last_four', 'type', 'channel', 'memo', 'payment_note', 'reference', \
                        'payment_method', 'issuer_auth_code', 'payment_card_type', 'payment_card_exp', 'payment_bank_name', \
                        'payment_bank_type','payment_bank_holder_type', 'billing_address_1', 'billing_address_2', \
                        'billing_address_city', 'billing_address_state', 'billing_address_zip', 'customer_company',\
                        'customer_email', 'customer_phone', 'customer_address_1','customer_address_2', 'customer_address_city',
                        'customer_address_state', 'customer_address_zip', 'customer_notes', 'customer_reference', \
                        'customer_created_at', 'customer_updated_at', 'customer_deleted_at', 'gateway_id', 'gateway_name', \
                        'gateway_type', 'gateway_created_at', 'gateway_deleted_at', 'user_name', 'system_admin', \
                        'user_created_at', 'user_updated_at', 'user_deleted_at']]
            
            highticket = highticket.sort_values(by='total', ascending=False)
    
    
            #Convert total column to currency format with 0 zero decimal places.
    
            #Re-order columns as follows:  payment_person name, created_at, total, last_four, type channel, memo, payment_note, reference, no preference to order for remaining columns.
    
            name_parts = []
            if firstname1: name_parts.append(firstname1)
            if lastname1: name_parts.append(lastname1)
            if firstname2: name_parts.append(firstname2)
            if lastname2: name_parts.append(lastname2)
            if firstname3: name_parts.append(firstname3)
            if lastname3: name_parts.append(lastname3)
            if firstname4: name_parts.append(firstname4)
            if lastname4: name_parts.append(lastname4)
            if bizname1: name_parts.append(bizname1)
            if bizname2: name_parts.append(bizname2)
    
    
            # escape them for regex safety
            escaped_parts = [re.escape(part) for part in name_parts if part.strip() != ""]
            if escaped_parts:
                name_pattern = "|".join(escaped_parts)
            else:
                name_pattern = "$^"  # matches nothing if nothing entered
    
            # apply filter across multiple columns
            namefinal = df[
                df['payment_person_name'].astype(str).str.contains(name_pattern, case=False, na=False) |
                df['customer_lastname'].astype(str).str.contains(name_pattern, case=False, na=False) |
                df['customer_firstname'].astype(str).str.contains(name_pattern, case=False, na=False) |
                df['customer_company'].astype(str).str.contains(name_pattern, case=False, na=False)
            ]

            namefinal2 = namefinal.loc[:,['payment_person_name', 'customer_firstname', 'customer_lastname', 'created_at', 'total', \
                        'payment_last_four', 'last_four', 'type', 'channel', 'memo', 'payment_note', 'reference', \
                        'payment_method', 'issuer_auth_code', 'payment_card_type', 'payment_card_exp', 'payment_bank_name', \
                        'payment_bank_type','payment_bank_holder_type', 'billing_address_1', 'billing_address_2', \
                        'billing_address_city', 'billing_address_state', 'billing_address_zip', 'customer_company',\
                        'customer_email', 'customer_phone', 'customer_address_1','customer_address_2', 'customer_address_city',
                        'customer_address_state', 'customer_address_zip', 'customer_notes', 'customer_reference', \
                        'customer_created_at', 'customer_updated_at', 'customer_deleted_at', 'gateway_id', 'gateway_name', \
                        'gateway_type', 'gateway_created_at', 'gateway_deleted_at', 'user_name', 'system_admin', \
                        'user_created_at', 'user_updated_at', 'user_deleted_at']]
            
            namefinal3 = namefinal2.query("total > 1")
    
        #Convert total column to currency format with 0 zero decimal places.
    
            dup = df.loc[:,['payment_person_name', 'customer_firstname', 'customer_lastname', 'created_at', 'total', \
                        'payment_last_four', 'last_four', 'type', 'channel', 'memo', 'payment_note', 'reference', \
                        'payment_method', 'issuer_auth_code', 'payment_card_type', 'payment_card_exp', 'payment_bank_name', \
                        'payment_bank_type','payment_bank_holder_type', 'billing_address_1', 'billing_address_2', \
                        'billing_address_city', 'billing_address_state', 'billing_address_zip', 'customer_company',\
                        'customer_email', 'customer_phone', 'customer_address_1','customer_address_2', 'customer_address_city',
                        'customer_address_state', 'customer_address_zip', 'customer_notes', 'customer_reference', \
                        'customer_created_at', 'customer_updated_at', 'customer_deleted_at', 'gateway_id', 'gateway_name', \
                        'gateway_type', 'gateway_created_at', 'gateway_deleted_at', 'user_name', 'system_admin', \
                        'user_created_at', 'user_updated_at', 'user_deleted_at']]
            
            dup['payment_person_name_next'] = dup['payment_person_name'].shift(1)
            dup['payment_person_name_prev'] = dup['payment_person_name'].shift(-1)
            dup['payment_last_four_next'] = dup['payment_last_four'].shift(1)
            dup['payment_last_four_prev'] = dup['payment_last_four'].shift(-1)
            dup['created_at_day'] = dup['created_at'].str.split(expand=True)[0]
            dup['created_at_dayprev'] = dup['created_at_day'].shift(-1)
            dup['created_at_daynext'] = dup['created_at_day'].shift(1)
            dup['created_at_time'] = dup['created_at'].str.split(expand=True)[1]
            dup['totalmins'] = dup['created_at_time'].str.split(pat=":", expand=True)[0].astype(float) * 60 + dup['created_at_time'].str.split(pat=":", expand=True)[1].astype(float)
            dup['totalminsprev'] = dup['totalmins'].shift(-1)
            dup['totalminsnext'] = dup['totalmins'].shift(1)
           # dup2 = dup.query('created_at_day == created_at_daynext | created_at_day == created_at_dayprev')
           # dup3 = dup2.query('totalmins < totalminsprev + 60 | totalmins > totalminsnext - 60')
           # dup4 = dup3.query('payment_person_name == payment_person_name_next | \
           #         payment_person_name == payment_person_name_prev | \
           #         payment_last_four == payment_last_four_next | \
           #         payment_last_four == payment_last_four_prev') 
    
            dup4 = dup.query('(created_at_day == created_at_daynext | created_at_day == created_at_dayprev) &\
                      (totalmins < totalminsprev + 60 | totalmins > totalminsnext - 60) & \
                      (payment_person_name == payment_person_name_next | \
                        payment_person_name == payment_person_name_prev | \
                        payment_last_four == payment_last_four_next | \
                        payment_last_four == payment_last_four_prev) ')   
            dup4['nexttotal'] = dup['total'].shift(-1)
            dup4['prevtotal'] = dup['total'].shift(1)  
    
            def splitpaymentsname(row):
                if row['payment_person_name'] == row['payment_person_name_next']:
                    return row['prevtotal'] + row['total']
                elif row['payment_person_name'] == row['payment_person_name_prev']:
                    return row['nexttotal'] + row['total']
                elif row['payment_last_four'] == row['payment_last_four_next']:
                    return row['prevtotal'] + row['total']
                elif row['payment_last_four'] == row['payment_last_four_prev']:
                    return row['nexttotal'] + row['total']
                else:
                    return row['total']
    
            dup4['totalAll'] = dup4.apply(splitpaymentsname, axis=1)
    
            dup5 = dup4[dup4['totalAll'] >= highticketval]
    
            dup5['total'] = dup5['total'].apply('${:,.0f}'.format)
            namefinal['total'] = namefinal['total'].apply('${:,.0f}'.format)
            highticket['total'] = highticket['total'].apply('${:,.0f}'.format)
            df['total'] = df['total'].apply('${:,.0f}'.format)
    
            objects_to_download = {
                "Clean_Data": df,
                "Calculations": dfcalc,
                "Dup_Trans": dup5,
                "High_Ticket": highticket,         
                "Negative_Memo": memofinal,
                "Flagged_Payment_Notes": payment_note_final,
                "Flagged_Names": namefinal3,
                "Chanel_Pivot": pivottablechannel,
                "Names_Pivot": pivottablenames,
                "Last_Four_Pivot": pivottablelastfour,
            }
    
            download_link = download_button(objects_to_download, st.session_state.filename)
            if download_link:
                st.markdown(download_link, unsafe_allow_html=True)
            else:
                st.error("File download failed.")
    
    if __name__ == "__main__":
        uploaded_files = None
        st.title("Transaction Analysis")
    
        with st.form("my_form", clear_on_submit=True):
            st.text_input("Filename (must include .xlsx)", key="filename")
    
            firstname1 = st.text_input("Enter Owner First Name 1", key="firstname1")
            lastname1 = st.text_input("Enter Owner Last Name 1", key="lastname1")
    
            firstname2 = st.text_input("Enter Owner First Name 2", key="firstname2")
            lastname2 = st.text_input("Enter Owner Last Name 2", key="lastname2")
    
            firstname3 = st.text_input("Enter Owner First Name 3", key="firstname3")
            lastname3 = st.text_input("Enter Owner Last Name 3", key="lastname3")
    
            firstname4 = st.text_input("Enter Owner First Name 4", key="firstname4")
            lastname4 = st.text_input("Enter Owner Last Name 4", key="lastname4")

            st.write('No Need to put llc or extra details in biz name')
            bizname1 = st.text_input("Enter Business Name", key="businessname1")
            bizname2 = st.text_input("Enter Business Name Variant", key="businessname2")
    
            highticketstring = st.number_input("Enter High Ticket INTEGER ONLY", key="highticket")
    
            uploaded_files = st.file_uploader("Upload CSV", type="csv", accept_multiple_files=True)
            submit = st.form_submit_button("Download dataframe")
    
        if submit:
            download_df()
