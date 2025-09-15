import os
import sys
import requests
import streamlit as st
from auth_utils import require_role, get_user_info

# --- Config / API key ---
PERPLEXITY_API_KEY = st.secrets["api"]["PERPLEXITY_API_KEY"]
if not PERPLEXITY_API_KEY:
    st.error("❌ Missing PERPLEXITY_API_KEY. Please set it in Streamlit Cloud Secrets or your local environment.")
    st.stop()

st.set_page_config(page_title="Adverse Media Finder", page_icon="🔍")

# Make sure we can import auth_utils (adjust path as needed)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# --- Helper: reset callback ---
def reset_all():
    """
    Remove the input keys and result keys from session_state, then force a rerun.
    This runs as the on_click callback for the Reset button.
    """
    keys = [
        "business_legal_name",
        "business_dba_name",
        "city_state",
        "website",
        "output_text",
        "sources",
    ]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

    # Force a re-run so widgets rebuild without stored values
    st.rerun()


# --- Main app ---
if require_role(["Risk", "Underwriting"], "Exposure Decay Portfolio"):

    user_info = get_user_info()

    st.title("🔍 Business Adverse Media Finder")
    st.write("Please Enter ALL Results in here: https://docs.google.com/spreadsheets/d/1eTjNKEeFBisDNHMGgZSxn2o5-L4-pFCQqlJc0LL4HIo/edit?gid=0#gid=0")
    st.markdown("Enter details below to check for **adverse media or negative news** on a business.")

    # --- Ensure default state keys exist BEFORE creating widgets ---
    # (this avoids Streamlit errors when mutating session_state later)
    for key in ["business_legal_name", "business_dba_name", "city_state", "website"]:
        if key not in st.session_state:
            st.session_state[key] = ""

    # --- Inputs (bound to keys) ---
    business_legal_name = st.text_input("Business Legal Name", key="business_legal_name")
    business_dba_name = st.text_input("Business DBA Name", key="business_dba_name")
    city_state = st.text_input("City, State", key="city_state")
    website = st.text_input("Website (optional)", key="website")

    # --- Search button (left alone on top) ---
    if st.button("Search"):
        # Validate required fields
        if not (st.session_state["business_legal_name"].strip() and
                st.session_state["business_dba_name"].strip() and
                st.session_state["city_state"].strip()):
            st.warning("⚠️ Please provide Business Name and City, State.")
        else:
            # Build the prompt (kept inline for clarity)
            prompt = f"""
            You are a business researcher looking for any adverse media, controversies, or negative news regarding a business. 
            The company may appear as: {st.session_state['business_legal_name']}, {st.session_state['business_dba_name']}, or any variant.       
            Location: {st.session_state['city_state']}. 
            Website: {st.session_state['website']}

            Consider news about the company, its products/platforms, or business practices as relevant, even if the legal name or location is not stated.
            The location is where the business is located at, not necessarily where the news story or event took place.

            Report on ANY type of negative coverage, including but not limited to:
            - Lawsuits, regulatory scrutiny, fines, or bankruptcy
            - Negative or critical news articles, reviews, or complaints
            - Political, social, or cultural controversies where the business is named
            - Public closures, safety/health code violations, or other scandals

            Include a two-sentence summary and a link to each article found. 
            If the business cannot be located, print: "Can’t Locate Business." 
            If no adverse media, controversies, or negative news exist, print: "No adverse media or negative news."
            """

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
                try:
                    resp = requests.post(url, headers=headers, json=payload, timeout=30)
                    resp.raise_for_status()
                except Exception as e:
                    st.error(f"❌ API request failed: {e}")
                else:
                    j = resp.json()
                    # Save results into session_state for display and to enable reset button
                    st.session_state["output_text"] = j["choices"][0]["message"]["content"]
                    st.session_state["sources"] = j.get("citations", [])

    # --- Results (if present) ---
    if st.session_state.get("output_text"):
        st.subheader("📢 Results")
        st.markdown(st.session_state["output_text"])

        sources = st.session_state.get("sources", [])
        if sources:
            st.subheader("🔗 Sources")
            for i, src in enumerate(sources, 1):
                st.markdown(f"{i}. [{src}]({src})")
        else:
            st.info("No sources returned for this query.")

        # --- RESET BUTTON: only shown AFTER results, at the bottom of results ---
        st.write("")  # spacer
        st.button("🔄 Reset (inputs + results)", on_click=reset_all)
