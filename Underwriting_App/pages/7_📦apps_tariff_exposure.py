#python3 -m streamlit run trump_tariff/apps.py 


#Metrics to look at: APPS
# Number MCC Codes Impacted for each bucket
# Number of Accounts per Bucket
# Volume Per Bucket 
# Exposure Per Bucket 
# Top 10 High Impact Merchants Based on Vol
# Top 10 MCC Codes Impact Based on Vol 

import streamlit as st
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib import ticker as mticker  # Correct import

import altair as alt
import io
import sys
import os
from auth_utils import require_role, get_user_info
#from auth_utils import require_role, get_user_info

# Add the parent directory to Python path to import auth_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# This will check authentication and redirect if not logged in
#if require_auth("Exposure Decay Portfolio"):
if require_role(["Risk"], "Exposure Decay Portfolio"):

    # Your protected page content goes here
    user_info = get_user_info()
    
    
    apps_file = st.file_uploader("Upload APPS Exposure Sheet", type=['csv', 'xlsx'])
    st.write('https://docs.google.com/spreadsheets/d/1rwdTOgwB6dIym5NCbrifmNWH-f7rrNg0TEePyRQYF1A/edit?gid=0#gid=0')
    tariff_info = st.file_uploader("Upload Tariff Spreadsheet", type=['csv', 'xlsx'])
    
    
    if apps_file is not None and tariff_info is not None:
      try:
          apps_df = pd.read_excel(apps_file)
          tariff_df = pd.read_excel(tariff_info, sheet_name='Final Table')
          
          new_df = pd.merge(apps_df, tariff_df, on='MCC', how='left')
    
          tariff_impact_group = new_df.groupby('Impact_Likelihood').agg({
              'Impact_Likelihood': 'count',   # or any column for counting
              'exposure': 'sum',
              'Gross Sales Volume': 'sum'
          }).rename(columns={'Impact_Likelihood': 'count'})
    
          # Optional: reset index if needed
          tariff_impact_group = tariff_impact_group.reset_index()
    
          high_impact_df = new_df[new_df['Impact_Likelihood'] == 'High impact']
    
    
          #Get top 10 Merchants by Vol and Exposure
          top_exposure_high_impact = high_impact_df.sort_values('exposure', ascending=False).head(10)
          top_exposure_high_impact = top_exposure_high_impact.set_index('Merchant Legal Name')
    
          top_volume_high_impact = high_impact_df.sort_values('Gross Sales Volume', ascending=False).head(10)
          top_volume_high_impact = top_volume_high_impact.set_index('Merchant Legal Name')
    
          mcc_impact_group = high_impact_df.groupby('MCC').agg({
              'MCC': 'count',   # or any column for counting
              'exposure': 'sum',
              'Gross Sales Volume': 'sum'
          }).rename(columns={'MCC': 'count'})
    
    
          # Sort and take top 10 for each metric
          top_count = mcc_impact_group.sort_values('count', ascending=False).head(10)
          top_exposure = mcc_impact_group.sort_values('exposure', ascending=False).head(10)
          top_volume = mcc_impact_group.sort_values('Gross Sales Volume', ascending=False).head(10)
    
    
    
    
    
          #Values based off of buckets graphs
          def plot_bar_with_values(x, y, title, ylabel, color):
              plt.figure(figsize=(10, 6))
              bars = plt.bar(x, y, color=color)
              plt.title(title)
              plt.xlabel('Impact Likelihood')
              plt.ylabel(ylabel)
              plt.xticks(rotation=45)
    
              # Format y-axis without scientific notation
              plt.gca().yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
    
              # Add value labels on bars
              for bar in bars:
                  height = bar.get_height()
                  plt.annotate(f'{height:,.0f}',
                              xy=(bar.get_x() + bar.get_width() / 2, height),
                              xytext=(0, 5),
                              textcoords='offset points',
                              ha='center', va='bottom', fontsize=9)
    
              plt.tight_layout()
              st.pyplot(plt.gcf())
              plt.clf()
    
          # Plot each metric
          plot_bar_with_values(
              tariff_impact_group['Impact_Likelihood'],
              tariff_impact_group['count'],
              'Count by Impact Likelihood',
              'Count',
              'skyblue'
          )
    
          plot_bar_with_values(
              tariff_impact_group['Impact_Likelihood'],
              tariff_impact_group['exposure'],
              'Total Exposure by Impact Likelihood',
              'Exposure',
              'orange'
          )
    
          plot_bar_with_values(
              tariff_impact_group['Impact_Likelihood'],
              tariff_impact_group['Gross Sales Volume'],
              'Gross Sales Volume by Impact Likelihood',
              'Gross Sales Volume',
              'green'
          )
    
          #MCC PLOTS
          # Plot top 10 by count
          plt.figure(figsize=(10, 6))
          top_count['count'].plot(kind='bar', color='skyblue')
          plt.title('Top 10 MCCs by Count')
          plt.ylabel('Count')
          plt.xticks(rotation=45)
          plt.tight_layout()
          st.pyplot(plt.gcf())
          plt.clf()
    
          # Plot top 10 by exposure
          plt.figure(figsize=(10, 6))
          top_exposure['exposure'].plot(kind='bar', color='salmon')
          plt.title('Top 10 MCCs by Exposure')
          plt.ylabel('Exposure')
          plt.xticks(rotation=45)
          plt.tight_layout()
          st.pyplot(plt.gcf())
          plt.clf()
    
          # Plot top 10 by Gross Sales Volume
          plt.figure(figsize=(10, 6))
          top_volume['Gross Sales Volume'].plot(kind='bar', color='seagreen')
          plt.title('Top 10 MCCs by Gross Sales Volume')
          plt.ylabel('Gross Sales Volume')
          plt.xticks(rotation=45)
          plt.tight_layout()
          st.pyplot(plt.gcf())
          plt.clf()
    
          # Plot top 10 Merchants 10 by Exposure that are high impact
          plt.figure(figsize=(10, 6))
          top_exposure_high_impact['exposure'].plot(kind='bar', color='skyblue')
          plt.title('Top 10 High Impact Merchants by Exposure')
          plt.ylabel('Exposure')
          plt.xticks(rotation=90)
          plt.tight_layout()
          st.pyplot(plt.gcf())
          plt.clf()
    
          # Plot top 10 Merchants 10 by Vol that are high impact
         # plt.figure(figsize=(10, 6))
         # top_volume_high_impact['Gross Sales Volume'].plot(kind='bar', color='skyblue')
         # plt.title('Top 10 Merchants by Volume')
         # plt.ylabel('Volume')
         # plt.xticks(rotation=90)
         # plt.tight_layout()
         # st.pyplot(plt.gcf())
         # plt.clf()
    
          plt.figure(figsize=(10, 6))
          top_volume_high_impact['Gross Sales Volume'].plot(kind='bar', color='skyblue')
          plt.title('Top 10 Merchants by Volume')
          plt.ylabel('Volume')
          plt.xticks(rotation=90)
    
          # Format y-axis to display plain integers, not scientific notation
          plt.gca().yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))
    
          plt.tight_layout()
          st.pyplot(plt.gcf())
          plt.clf()
       
      except Exception as e:
          st.error(f"Error reading files or merging: {e}")
