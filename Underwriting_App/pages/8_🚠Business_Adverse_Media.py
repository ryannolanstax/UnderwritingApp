import os
import streamlit as st
import requests
import io
import sys
from auth_utils import require_role, get_user_info

# Load API key
PERPLEXITY_API_KEY = st.secrets["api"]["PERPLEXITY_API_KEY"]

# Safety check
if not PERPLEXITY_API_KEY:
    st.error("❌ Missing PERPLEXITY_API_KEY. Please set it in Streamlit Cloud Secrets or your local environment.")
    st.stop()

# Streamlit app
st.set_page_config(page_title="Adverse Media Finder", page_icon="🔍")

# Add the parent directory to Python path to import auth_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Auth check
if require_role(["Risk", "Underwriting"], "Exposure Decay Portfolio"):

    user_info = get_user_info()

    st.title("🔍 Business Adverse Media Finder")
    st.write("Please Enter ALL Results in here: https://docs.google.com/spreadsheets/d/1eTjNKEeFBisDNHMGgZSxn2o5-L4-pFCQqlJc0LL4HIo/edit?gid=0#gid=0")
    st.markdown("Enter details below to check for **adverse media or negative news** on a business.")

    # --- Inputs with session state ---
    business_legal_name = st.text_input("Business Legal Name", key="business_legal_name")
    business_dba_name = st.text_input("Business DBA Name", key="business_dba_name")
    website = st.text_input("Website (optional)", key="website")

    # --- Prompt version selector ---
    prompt_version = st.radio(
        "Choose Prompt Style:",
        ["Regional Coverage", "National Coverage"],
        index=0,
        key="prompt_version"
    )

    # Show city/state only if Regional
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
            # --- Build prompt based on choice ---
            if st.session_state.prompt_version == "Regional Coverage":
                prompt = f"""
                You are a business researcher looking for any adverse media, controversies, or negative news 
                regarding a business. The company may appear as: {business_legal_name}, 
                {business_dba_name}, or any variant.       
                Location: {city_state}. 
                Website: {website}

                Focus your search on coverage relevant to the business and its location. 
                If the same-named business exists elsewhere but is unrelated, ignore it. 
                Prioritize adverse news tied to the business’s operations, customers, or regulatory environment 
                in the stated region.

                Report on ANY type of negative coverage, including but not limited to:
                - Lawsuits, regulatory scrutiny, fines, or bankruptcy
                - Local news articles, reviews, or complaints
                - Safety/health code violations, closures, or scandals

                Include a two-sentence summary and a link to each article found. 
                If the business cannot be located, print: "Can’t Locate Business." 
                If no adverse media exists, print: "No adverse media or negative news."
                """
            else:  # National Coverage
                prompt = f"""
                You are a business researcher looking for any adverse media, controversies, or negative news 
                regarding a business. The company may appear as: {business_legal_name}, 
                {business_dba_name}, or any variant.       
                Website: {website}

                Ignore the provided city/state location. Search broadly across national or international sources. 
                Include controversies, lawsuits, negative reviews, or scandals at any scale, regardless of where 
                they occurred geographically.

                Report on ANY type of negative coverage, including but not limited to:
                - Lawsuits, regulatory scrutiny, fines, or bankruptcy
                - National or global news coverage, reviews, or complaints
                - Political, social, or cultural controversies
                - Public closures, safety/health code violations, or other scandals

                Include a two-sentence summary and a link to each article found. 
                If the business cannot be located, print: "Can’t Locate Business." 
                If no adverse media exists, print: "No adverse media or negative news."
                """

            # --- API call ---
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 600
            }

            with st.spinner("🔎 Searching for adverse media..."):
                response = requests.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                result = response.json()

                # Store results in session_state
                st.session_state["results"] = result["choices"][0]["message"]["content"]
                st.session_state["sources"] = result.get("citations", [])

            else:
                st.error(f"❌ API request failed: {response.status_code} - {response.text}")

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

        # --- Reset button at bottom ---
        if st.button("🔄 Reset (inputs + results)"):
            st.session_state.clear()
            st.rerun()
