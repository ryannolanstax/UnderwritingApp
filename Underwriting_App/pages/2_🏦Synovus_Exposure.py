# python3 -m streamlit run Underwriting_App/pages/calc_2025_synovus.py 
#last Updated End of April

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
import sys
import os
from auth_utils import require_auth, get_user_info


st.set_page_config(page_title="Synovus Underwriting Calculator", page_icon="💾", layout="wide")

# Add the parent directory to Python path to import auth_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# This will check authentication and redirect if not logged in
if require_auth("Synovus Underwriting and Risk Calculator"):
    # Your protected page content goes here
    user_info = get_user_info()

  
  
  st.title("Synovus Underwriting and Risk Calculator")
  st.markdown("Having Issues or Ideas to improve the APP? Reach out to Ryan Nolan")
  
  st.header('Exposure Fields')
  
  delayed = pd.read_csv('Underwriting_App/MCC & Business Models - MCC Ratings_Sales.csv')
  
  MCC = st.number_input("MCC", key='MCC', value=1711)
  
  CNP_DD = delayed.loc[delayed['MCC'] == MCC, ['CNP Delayed Delivery']].iloc[0, 0]
  CP_DD = delayed.loc[delayed['MCC'] == MCC, ['CP/ACH Delayed Delivery']].iloc[0, 0]
  
  NDX = (CNP_DD + CP_DD) / 2
  
  Annual_Volume = st.number_input("Annual Volume Card Only ($)", key="Annual_Volume", step=1)
  
  daily_vol = Annual_Volume / 365
  monthly_vol = Annual_Volume / 12
  
  step_size = 0.001
  
  Refund_Rate = st.number_input("Refund Rate (Volume) Last 90 Days", key="Refund_Rate", value=0.05)
  Chargeback_Rate = st.number_input("Chargeback Rate (Volume) Last 90 Days", key="Chargeback_Rate", value=0.005, step=step_size, format="%f")
  
  Total_Exposure = ((daily_vol * NDX) + (monthly_vol * Refund_Rate) + (monthly_vol * Chargeback_Rate))
  
  formatted_exposure = "${:,.0f}".format(Total_Exposure)
  st.write('The Final Estimated Synovus Exposure of the Customer is:', formatted_exposure)
