import os
import streamlit as st
import requests
import io
import sys
from auth_utils import require_role, get_user_info

# Load API key (Streamlit Cloud secrets preferred, fallback to local env var)
PERPLEXITY_API_KEY = st.secrets["api"]["PERPLEXITY_API_KEY"]

# Safety check
if not PERPLEXITY_API_KEY:
    st.error("❌ Missing PERPLEXITY_API_KEY. Please set it in Streamlit Cloud Secrets or your local environment.")
    st.stop()

# Streamlit app
st.set_page_config(page_title="Adverse Media Finder", page_icon="🔍")

# Add the parent directory to Python path to import auth_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# This will check authentication and redirect if not logged in
if require_role(["Risk", "Underwriting"], "Exposure Decay Portfolio"):

    # Your protected page content goes here
    user_info = get_user_info()

    st.title("🔍 Business Adverse Media Finder")
    st.write("Please Enter ALL Results in here: https://docs.google.com/spreadsheets/d/1eTjNKEeFBisDNHMGgZSxn2o5-L4-pFCQqlJc0LL4HIo/edit?gid=0#gid=0")
    st.markdown("Enter details below to check for **adverse media or negative news** on a business.")
    
    # User input
    business_name = st.text_input("Business Name")
    city_state = st.text_input("City, State")
    website = st.text_input("Website (optional)")
    
    if st.button("Search"):
        if not business_name or not city_state:
            st.warning("⚠️ Please provide both Business Name and City, State.")
        else:
            # Build prompt
            prompt = f"""
            You are a business researcher looking for bad publicity on a business.

            Tell me any adverse media or negative news you can find regarding {business_name} in {city_state}. 

            This is the businesses website: {website}

            If you cannot find this information for the business, print: “Can’t Locate Business”

            If you cannot find adverse media or negative news, print: “No adverse media or negative news”

            Otherwise, for the output have a two sentence summary and a link to each article on the adverse media or negative news.
            """
    
            # Call Perplexity API
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "sonar-pro",  # Recommended research model
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600
            }
    
            with st.spinner("🔎 Searching for adverse media..."):
                response = requests.post(url, headers=headers, json=payload)
    
            if response.status_code == 200:
                result = response.json()

                # Main output
                output_text = result["choices"][0]["message"]["content"]
                st.subheader("📢 Results")
                st.markdown(output_text)

                # Sources / citations if available
                sources = result.get("citations", [])
                if sources:
                    st.subheader("🔗 Sources")
                    for i, src in enumerate(sources, 1):
                        st.markdown(f"{i}. [{src}]({src})")
                else:
                    st.info("No sources returned for this query.")
            else:
                st.error(f"❌ API request failed: {response.status_code} - {response.text}")
