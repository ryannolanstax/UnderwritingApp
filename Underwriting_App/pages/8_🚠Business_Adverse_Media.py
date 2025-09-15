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

                Report on ANY type of negative coverage, including but not limited to:
                - Lawsuits, regulatory scrutiny, fines, or bankruptcy
                - Negative or critical news articles, reviews, or complaints
                - Political, social, or cultural controversies where the business is named
                - Public closures, safety or health code violations, or other scandals
                
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

                Report on ANY type of negative coverage, including but not limited to:
                - Lawsuits, regulatory scrutiny, fines, or bankruptcy
                - Negative or critical news articles, reviews, or complaints
                - Political, social, or cultural controversies where the business is named
                - Public closures, safety or health code violations, or other scandals
                
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

            # Replace your existing Firecrawl section with this corrected version:
            if "No adverse media or negative news" in perplexity_text and FIRECRAWL_API_KEY:
                st.info("ℹ️ No results from Perplexity. Searching Firecrawl (20 results)...")
            
                firecrawl = Firecrawl(api_key=FIRECRAWL_API_KEY)
                if st.session_state.prompt_version == "Regional Coverage":
                    fc_query = f"{business_legal_name} {city_state} news"
                else:
                    fc_query = f"{business_legal_name} news"
            
                try:
                    fc_results = firecrawl.search(
                        query=fc_query,
                        limit=20,
                        sources=["news"],
                        scrape_options={"formats": ["markdown", "links"]}
                    )
            
                    # The correct way to access search results
                    # fc_results should be a dict-like object with 'data' key containing the results
                    if hasattr(fc_results, 'data') and fc_results.data:
                        news_items = fc_results.data
                    elif isinstance(fc_results, dict) and 'data' in fc_results:
                        news_items = fc_results['data']
                    elif isinstance(fc_results, list):
                        # Sometimes results come directly as a list
                        news_items = fc_results
                    else:
                        # Try to access the results directly if it's a different structure
                        news_items = fc_results
            
                    # --- Print all news URLs ---
                    st.subheader("📰 Firecrawl News URLs (all results)")
                    if news_items:
                        # Handle different possible structures of news_items
                        for i, item in enumerate(news_items, 1):
                            if isinstance(item, dict):
                                # If item is a dictionary, try different possible keys
                                title = item.get('title', item.get('name', f'Article {i}'))
                                url = item.get('url', item.get('link', '#'))
                                st.markdown(f"{i}. [{title}]({url})")
                            elif hasattr(item, 'title') and hasattr(item, 'url'):
                                # If item has attributes
                                st.markdown(f"{i}. [{item.title}]({item.url})")
                            else:
                                # Fallback - try to display whatever we have
                                st.markdown(f"{i}. {item}")
                    else:
                        st.info("No news items returned from Firecrawl.")
            
                    # Optional: send URLs back to Perplexity for summaries
                    if news_items:
                        # Extract URLs from the results
                        urls = []
                        for item in news_items:
                            if isinstance(item, dict):
                                url = item.get('url', item.get('link'))
                                if url:
                                    urls.append(url)
                            elif hasattr(item, 'url'):
                                urls.append(item.url)
                        
                        if urls:
                            urls_text = "\n".join(urls)
                            followup_prompt = f"""
                            You are a business researcher. Summarize any adverse media from the following URLs.
                            Provide two-sentence summaries for each. URLs:
                            {urls_text}
                            """
            
                            payload_followup = {
                                "model": "sonar-pro",
                                "messages": [{"role": "user", "content": followup_prompt}],
                                "max_tokens": 1000
                            }
            
                            response_followup = requests.post(perplexity_url, headers=headers, json=payload_followup)
            
                            if response_followup.status_code == 200:
                                followup_result = response_followup.json()
                                st.session_state["results"] = followup_result["choices"][0]["message"]["content"]
                                st.session_state["sources"] = urls
                            else:
                                st.error(f"❌ Perplexity follow-up failed: {response_followup.status_code}")
            
                except Exception as e:
                    st.error(f"❌ Firecrawl search failed: {e}")
                    # Add debug information
                    st.error(f"Debug: fc_results type: {type(fc_results)}")
                    if hasattr(fc_results, '__dict__'):
                        st.error(f"Debug: fc_results attributes: {list(fc_results.__dict__.keys())}")
                    else:
                        st.error(f"Debug: fc_results content: {fc_results}")

     

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
