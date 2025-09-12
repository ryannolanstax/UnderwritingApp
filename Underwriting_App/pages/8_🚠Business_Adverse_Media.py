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
    business_legal_name = st.text_input("Business Legal Name")
    business_dba_name = st.text_input("Business DBA Name")
    
    city_state = st.text_input("City, State")
    website = st.text_input("Website (optional)")
    
    if st.button("Search"):
        if not business_legal_name or not business_dba_name or not city_state:
            st.warning("⚠️ Please provide both Business Name and City, State.")
        else:
            # Build prompt
            prompt = f"""
            You are a business researcher looking for any adverse media, controversies, or negative news regarding a business. 
            The company may appear as: {business_legal_name}, {business_dba_name}, or any variant.       
            Location: {city_state}. 
            Website: {website}

            Consider news about the company, its products/platforms, or business practices as relevant, even if the legal name or location is not stated.
            The location is where the business is located at, not necassarily where the news story or event took place. For example a software company may be located in San Fransisco, California but has news in Tampa, Florida.
            
            Report on ANY type of negative coverage, including but not limited to:
            - Lawsuits, regulatory scrutiny, fines, or bankruptcy
            - Negative or critical news articles, reviews, or complaints
            - Political, social, or cultural controversies where the business is named
            - Public closures, safety/health code violations, or other scandals

            Include:
            - Lawsuits, regulatory scrutiny, official warnings/letters, political or policy controversies, accusations of ideological bias, negative impacts from government actions, bans, or suspensions.
            - Negative reviews, user complaints, business failures, or any public criticism—even if indirect.

            If even one article contains a warning, controversy, or negative association, include it, even if it’s about use in another state.
            
            Include a two-sentence summary and a link to each article found. 
            If the business cannot be located, print: "Can’t Locate Business." 
            If no adverse media, controversies, or negative news exist, print: "No adverse media or negative news."

            """
    
            # Call Perplexity API
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "sonar-pro",  # Recommended research model
                #"model": "sonar-reasoning-pro",  # Recommended research model
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
