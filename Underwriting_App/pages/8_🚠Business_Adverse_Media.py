import os
import sys
import requests
import streamlit as st
from datetime import date
from dateutil.relativedelta import relativedelta
from auth_utils import require_role, get_user_info
from firecrawl import Firecrawl

# --- API Keys ---
PERPLEXITY_API_KEY = st.secrets["api"]["PERPLEXITY_API_KEY"]
FIRECRAWL_API_KEY = st.secrets["api"]["FIRECRAWL_API_KEY"]

# Safety checks
if not PERPLEXITY_API_KEY:
    st.error("❌ Missing PERPLEXITY_API_KEY. Please set it in Streamlit Cloud Secrets or your local environment.")
    st.stop()
if not FIRECRAWL_API_KEY:
    st.warning("⚠️ Missing FIRECRAWL_API_KEY. Firecrawl fallback will be disabled.")

# Streamlit app config
st.set_page_config(page_title="Adverse Media Finder", page_icon="🔍")
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Auth
if require_role(["Risk", "Underwriting"], "Exposure Decay Portfolio"):

    user_info = get_user_info()
    st.title("🔍 Business Adverse Media Finder")
    st.write("Please Enter ALL Results here: https://docs.google.com/spreadsheets/d/1eTjNKEeFBisDNHMGgZSxn2o5-L4-pFCQqlJc0LL4HIo/edit#gid=0")
    st.markdown("Enter details below to check for **adverse media or negative news** on a business.")

    # --- Inputs ---
    business_legal_name = st.text_input("Business Legal Name", key="business_legal_name")
    business_dba_name = st.text_input("Business DBA Name", key="business_dba_name")
    website = st.text_input("Website (optional)", key="website")

    prompt_version = st.radio(
        "Choose Prompt Style:",
        ["Regional Coverage", "National Coverage"],
        index=0,
        key="prompt_version"
    )

    city_state = ""
    if st.session_state.prompt_version == "Regional Coverage":
        city_state = st.text_input("City, State", key="city_state")

    # --- Search button ---
    if st.button("Search"):

        if not business_legal_name or not business_dba_name:
            st.warning("⚠️ Please provide both Business Legal Name and DBA Name.")
        elif st.session_state.prompt_version == "Regional Coverage" and not city_state:
            st.warning("⚠️ Please provide City, State for Regional searches.")
        else:

            six_months_ago = (date.today() - relativedelta(months=6)).isoformat()
            perplexity_url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }

            # --- Step 1: Initial Perplexity Search ---
            if st.session_state.prompt_version == "Regional Coverage":
                initial_prompt = f"""
                You are a business researcher looking for any adverse media, controversies, or negative news 
                regarding a business. 

                The company may appear as: {business_legal_name}, {business_dba_name}.       
                Location: {city_state}. Website: {website}
                
                Focus on news within ~200 miles radius.
                
                Report ANY negative coverage. Start search with '{business_legal_name} {city_state} news'.
                Include two-sentence summaries + links. If not found, return 'No adverse media or negative news.'
                """
            else:
                initial_prompt = f"""
                You are a business researcher looking for any adverse media, controversies, or negative news 
                regarding a business. 

                The company may appear as: {business_legal_name}, {business_dba_name}.  
                Website: {website}. Ignore location.
                
                Report ANY negative coverage. Start search with '{business_legal_name} news'.
                Include two-sentence summaries + links. If not found, return 'No adverse media or negative news.'
                """

            payload = {
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": initial_prompt}],
                "max_tokens": 1000,
                "web_search_options": {
                    "search_context_size": "high",
                    "latest_updated": six_months_ago
                },
                "enable_search_classifier": True
            }

            with st.spinner("🔎 Searching for adverse media via Perplexity..."):
                response = requests.post(perplexity_url, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                perplexity_text = result["choices"][0]["message"]["content"]
                st.session_state["results"] = perplexity_text
                st.session_state["sources"] = result.get("citations", [])

    # --- Show results if available ---
    if "results" in st.session_state:
        st.subheader("📢 Results")
        st.markdown(st.session_state["results"])

        sources = st.session_state.get("sources", [])
        if sources:
            st.subheader("🔗 Sources")
            for i, src in enumerate(sources, 1):
                st.markdown(f"{i}. [{src}]({src})")
        else:
            st.info("No sources returned for this query.")

        # --- Reset button ---
        if st.button("🔄 Reset (inputs + results)"):
            st.session_state.clear()
            st.rerun()
