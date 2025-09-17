import streamlit as st
import requests
import json
import io
import sys
import os
from auth_utils import require_role, get_user_info

st.set_page_config(page_title="Firecrawl + Claude Analysis", page_icon="🔎")

# Add the parent directory to Python path to import auth_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# This will check authentication and redirect if not logged in
if require_role(["Risk"], "Exposure Decay Portfolio"):

    # Your protected page content goes here
    user_info = get_user_info()

    st.title("🔎 Firecrawl News Search + Claude Analysis")
    st.write("Enter business information to search for adverse media and analyze with Claude Sonnet 4.")
    st.write("This is the Spreadsheet to Update")
    st.write("https://docs.google.com/spreadsheets/d/1eTjNKEeFBisDNHMGgZSxn2o5-L4-pFCQqlJc0LL4HIo/edit?gid=198587092#gid=198587092"
    
    # Load API keys from secrets
    try:
        FIRECRAWL_API_KEY = st.secrets["api"]["FIRECRAWL_API_KEY"]
        CLAUDE_API_KEY = st.secrets["api"]["CLAUDE_API_KEY"]
        PERPLEXITY_API_KEY = st.secrets["api"]["PERPLEXITY_API_KEY"]
    except KeyError as e:
        st.error(f"Missing API key in secrets: {e}")
        st.error("Please add your API keys to .streamlit/secrets.toml")
        st.code("""
[api]
FIRECRAWL_API_KEY = "your-firecrawl-api-key"
CLAUDE_API_KEY = "your-claude-api-key"
PERPLEXITY_API_KEY = "your-perplexity-api-key"
        """)
        st.stop()
    
    # --- Business Information Inputs ---
    business_legal_name = st.text_input("Business Legal Name", key="business_legal_name")
    business_dba_name = st.text_input("Business DBA Name", key="business_dba_name")
    
    # Checkbox for multiple variations
    use_variants = st.checkbox(
        "Search both Legal Name and DBA Name variants", 
        value=False,
        help="When checked, will run separate searches for both business names to maximize coverage"
    )
    
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
    
    # Function to generate search queries
    def generate_search_queries(legal_name, dba_name, city_state, prompt_version, use_variants):
        queries = []
        
        # Clean up inputs
        legal_name = legal_name.strip()
        dba_name = dba_name.strip()
        city_state = city_state.strip()
        
        if use_variants and legal_name and dba_name:
            # Generate queries for both names
            names_to_search = [legal_name, dba_name]
        else:
            # Use DBA if available, otherwise legal name
            primary_name = dba_name if dba_name else legal_name
            if not primary_name:
                return []
            names_to_search = [primary_name]
        
        for name in names_to_search:
            if prompt_version == "Regional Coverage" and city_state:
                query = f"{name} {city_state} news"
            else:
                query = f"{name} news"
            queries.append(query)
        
        return queries
    
    # Generate the search queries
    search_queries = generate_search_queries(
        st.session_state.business_legal_name,
        st.session_state.business_dba_name,
        city_state,
        st.session_state.prompt_version,
        use_variants
    )
    
    # Display the generated queries
    if search_queries:
        st.info(f"🔍 Generated Search Queries ({len(search_queries)}):")
        for i, query in enumerate(search_queries, 1):
            st.write(f"   {i}. **{query}**")
    else:
        st.warning("⚠️ Please enter at least a Business Legal Name or DBA Name to generate search queries")
    
    if st.button("Search & Analyze"):
        if not search_queries:
            st.error("Please enter at least a Business Legal Name or DBA Name")
            st.stop()
        
        # Step 1: Firecrawl Search(es)
        st.subheader(f"🔍 Step 1: Searching with Firecrawl ({len(search_queries)} queries)...")
        
        all_firecrawl_results = []
        firecrawl_url = "https://api.firecrawl.dev/v2/search"
        
        firecrawl_headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Run Firecrawl searches for each query
        for i, query in enumerate(search_queries, 1):
            st.write(f"🔎 Running Firecrawl search {i}/{len(search_queries)}: **{query}**")
            
            payload = {
                "query": query,
                "sources": ["web"],
                "categories": [],
                "limit": 20 if len(search_queries) > 1 else 30  # Reduce per-query limit if multiple queries
            }
            
            with st.spinner(f"Searching Firecrawl for: {query}"):
                try:
                    response = requests.post(firecrawl_url, json=payload, headers=firecrawl_headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Add query context to results
                    data['search_query'] = query
                    data['search_number'] = i
                    data['source'] = 'Firecrawl'
                    all_firecrawl_results.append(data)
                    
                    # Show brief summary
                    result_count = len(data.get('data', []))
                    st.success(f"✅ Firecrawl found {result_count} results for: {query}")
                    
                except Exception as e:
                    st.error(f"Firecrawl request failed for '{query}': {e}")
                    continue
        
        # Step 2: Perplexity Search(es)
        st.subheader(f"🧠 Step 2: Searching with Perplexity ({len(search_queries)} queries)...")
        
        all_perplexity_results = []
        perplexity_url = "https://api.perplexity.ai/chat/completions"
        
        perplexity_headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Run Perplexity searches for each query
        for i, query in enumerate(search_queries, 1):
            st.write(f"🧠 Running Perplexity search {i}/{len(search_queries)}: **{query}**")
            
            perplexity_prompt = f"""Search for recent news, controversies, legal issues, or negative coverage about: {query}

Focus on finding:
- Lawsuits, regulatory actions, or legal troubles
- Negative news coverage or scandals
- Safety violations or business closures
- Customer complaints or public controversies
- Financial issues or bankruptcy

Provide specific details with sources and dates where available."""
            
            payload = {
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "user",
                        "content": perplexity_prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.1
            }
            
            with st.spinner(f"Searching Perplexity for: {query}"):
                try:
                    response = requests.post(perplexity_url, json=payload, headers=perplexity_headers)
                    response.raise_for_status()
                    data = response.json()
                    
                    # Add query context to results
                    data['search_query'] = query
                    data['search_number'] = i
                    data['source'] = 'Perplexity'
                    all_perplexity_results.append(data)
                    
                    # Show brief summary
                    st.success(f"✅ Perplexity completed search for: {query}")
                    
                except Exception as e:
                    st.error(f"Perplexity request failed for '{query}': {e}")
                    continue
        
        # Combine all results and calculate totals
        all_results = {
            'firecrawl_results': all_firecrawl_results,
            'perplexity_results': all_perplexity_results
        }
        
        if not all_firecrawl_results and not all_perplexity_results:
            st.error("All searches failed. Please try again.")
            st.stop()
        
        # Calculate totals
        total_firecrawl = sum(len(result.get('data', [])) for result in all_firecrawl_results)
        total_perplexity = len(all_perplexity_results)
        
        # Show summary
        st.success(f"✅ Search completed! Firecrawl: {total_firecrawl} results | Perplexity: {total_perplexity} analyses")
        
        # Show raw API responses in expander
        with st.expander("📦 Raw Search Results", expanded=False):
            st.write("**Firecrawl Results:**")
            for i, result in enumerate(all_firecrawl_results, 1):
                st.write(f"*Search {i}: {result['search_query']}*")
                st.json(result)
                if i < len(all_firecrawl_results):
                    st.divider()
            
            st.write("**Perplexity Results:**")
            for i, result in enumerate(all_perplexity_results, 1):
                st.write(f"*Search {i}: {result['search_query']}*")
                st.json(result)
                if i < len(all_perplexity_results):
                    st.divider()
        
        # Step 3: Send to Claude for Analysis
        st.subheader("🤖 Step 3: Analyzing with Claude Sonnet 4...")
        
        # Prepare the prompt for Claude with all search results
        business_info = f"Legal Name: {st.session_state.business_legal_name}"
        if st.session_state.business_dba_name:
            business_info += f" | DBA: {st.session_state.business_dba_name}"
        if city_state:
            business_info += f" | Location: {city_state}"
        
        search_summary = f"Conducted searches using two different engines:\n"
        search_summary += f"FIRECRAWL: {len(all_firecrawl_results)} searches with {total_firecrawl} total results\n"
        search_summary += f"PERPLEXITY: {len(all_perplexity_results)} AI-powered analyses\n\n"
        
        for i, result in enumerate(all_firecrawl_results, 1):
            result_count = len(result.get('data', []))
            search_summary += f"  Firecrawl {i}. '{result['search_query']}' - {result_count} results\n"
        
        for i, result in enumerate(all_perplexity_results, 1):
            search_summary += f"  Perplexity {i}. '{result['search_query']}' - AI analysis completed\n"
        
        claude_prompt = f"""You are a business researcher looking for any adverse media, controversies, or negative news regarding a business. 

BUSINESS INFORMATION:
{business_info}

SEARCH OVERVIEW:
{search_summary}

I've conducted comprehensive searches using both Firecrawl (web scraping) and Perplexity (AI-powered search). Please analyze ALL results from both sources to identify potential issues such as:

- Lawsuits, regulatory scrutiny, fines, or bankruptcy
- Negative or critical news articles, reviews, or complaints  
- Political, social, or cultural controversies where the business is named
- Public closures, safety/health code violations, or other scandals

Please provide:
1. A summary of any concerning findings from both search sources
2. Specific details about each issue found (with source URLs if available)
3. Cross-reference findings between Firecrawl and Perplexity results
4. An overall risk assessment (Low/Medium/High)
5. Recommendations for further investigation if needed

COMBINED SEARCH RESULTS:

{json.dumps(all_results, indent=2)}"""

        # Send to Claude API
        claude_url = "https://api.anthropic.com/v1/messages"
        
        claude_headers = {
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01"
        }
        
        claude_payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4000,
            "messages": [
                {
                    "role": "user",
                    "content": claude_prompt
                }
            ]
        }
        
        with st.spinner(f"Claude is analyzing {total_firecrawl + total_perplexity} total results from both search engines..."):
            try:
                claude_response = requests.post(claude_url, json=claude_payload, headers=claude_headers)
                claude_response.raise_for_status()
                claude_data = claude_response.json()
                
                # Extract Claude's response
                claude_analysis = claude_data["content"][0]["text"]
                
            except Exception as e:
                st.error(f"Claude API request failed: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    st.error(f"Response: {e.response.text}")
                st.stop()
        
        # Display Claude's Analysis
        st.subheader("📊 Claude's Comprehensive Business Risk Analysis")
        st.info(f"Analysis based on {total_firecrawl} Firecrawl results + {total_perplexity} Perplexity analyses from {len(search_queries)} search queries")
        st.markdown(claude_analysis)
        
        # Optional: Show raw Claude response in expander
        with st.expander("🔧 Raw Claude API Response", expanded=False):
            st.json(claude_data)
