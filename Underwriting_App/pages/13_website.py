# python3 -m streamlit run Underwriting_App/pages/new_combo_site.py


#The second website is verbose and contains two major red flags:
#Before and after photos.  And lots of them.  Processors do not like before and after photos.
#Guarantee.  Processors do not like guarantees.


import streamlit as st
import requests
import re
import io
import csv
import time
import os
from datetime import datetime
from firecrawl import Firecrawl
from pydantic import BaseModel
import json
from bs4 import BeautifulSoup

st.set_page_config(page_title="Website Underwriting Analyzer", page_icon="🔍", layout="wide")

st.title("🔍 Website Underwriting Analyzer")
st.write("Comprehensive website analysis: policy pages, content extraction, and domain information.")

# --- Load API Keys from Streamlit Secrets ---
firecrawl_api_key = st.secrets["api"]["FIRECRAWL_API_KEY"]
whois_api_key = st.secrets["api"]["WHOIS_API_KEY"]
anthropic_api_key = st.secrets["api"]["CLAUDE_API_KEY"]


# Check for missing API keys
missing_keys = []
if not firecrawl_api_key:
    missing_keys.append("FIRECRAWL_API_KEY")
if not whois_api_key:
    missing_keys.append("WHOIS_API_KEY")
if not anthropic_api_key:
    missing_keys.append("ANTHROPIC_API_KEY")

if missing_keys:
    st.error(f"⚠️ Missing environment variables: {', '.join(missing_keys)}")
    st.stop()

# --- Settings ---
limit = 5000
sitemap_mode = "include"

# --- Main Input ---
site_url = st.text_input("Website URL", placeholder="https://example.com")

keywords_input = st.text_area(
    "Keywords for Policy Pages",
    value="policy|refund|return|exchange|shipping|delivery|subscription|cancel|billing|renewal|terms|privacy|payment-options|terms-and-conditions|privacy-policy|refund-policy|disclaimer|about|contact|faq|guarantee|warranty|disclaimer",
    height=100
)

extraction_prompt = st.text_area(
    "Extraction Prompt",
    value="Extract any info about the website having service or delivery times. If there are any subscriptions. Refund policies. Disclaimer information. Contact information. Warranties or guarantees.",
    height=80
)

# --- Schema Definition ---
class PolicyInfo(BaseModel):
    service_times: str = None
    delivery_times: str = None
    has_subscriptions: bool = None
    refund_policy: str = None
    disclaimer: str = None
    contact_info: str = None
    warranties_guarantees: str = None
    about_business: str = None

class ContactInfo(BaseModel):
    address: str = None
    phone: str = None
    email: str = None
    business_name: str = None

# --- Functions ---
def get_domain_from_url(url):
    """Extract domain from URL."""
    match = re.search(r'https?://(?:www\.)?([^/]+)', url)
    return match.group(1) if match else None

def get_whois_info(domain, api_key):
    """Fetch WHOIS information for a domain."""
    url = f"https://prod.api.market/api/v1/magicapi/whois/whois/{domain}"
    headers = {
        "accept": "application/json",
        "x-api-market-key": api_key,
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    data = response.json()
    raw_text = data.get("Raw", "")
    
    # Extract Registrar
    registrar_match = re.search(r"Registrar:\s*(.+)", raw_text)
    registrar = registrar_match.group(1).strip() if registrar_match else "N/A"
    
    # Extract Creation Date
    creation_match = re.search(r"Creation Date:\s*(.+)", raw_text)
    creation_date_str = creation_match.group(1).strip() if creation_match else None
    
    # Calculate Site Age
    site_age = "N/A"
    if creation_date_str:
        try:
            creation_date = datetime.strptime(creation_date_str, "%Y-%m-%dT%H:%M:%SZ")
            today = datetime.utcnow()
            age_years = today.year - creation_date.year - (
                (today.month, today.day) < (creation_date.month, creation_date.day)
            )
            site_age = f"{age_years} years"
        except:
            pass
    
    return {
        "Registered Date": creation_date_str or "N/A",
        "Registrar": registrar,
        "Site Age": site_age
    }

def map_site(site_url, api_key, limit=5000, sitemap_mode="include"):
    """Call Firecrawl /map endpoint and return list of URLs."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": site_url,
        "limit": limit,
        "sitemap": sitemap_mode,
        "ignoreQueryParameters": True
    }
    r = requests.post("https://api.firecrawl.dev/v2/map", json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    resp = r.json()
    if not resp.get("success"):
        raise Exception("Firecrawl map failed", resp)
    links = [link["url"] for link in resp.get("links", []) if "url" in link]
    return links

def filter_policy_urls(urls, keywords):
    """Filter URLs using keywords."""
    pattern = re.compile(keywords, re.IGNORECASE)
    return [u for u in urls if pattern.search(u)]

def extract_policy_info(urls, api_key, prompt):
    """Extract policy information from URLs using Firecrawl."""
    try:
        firecrawl = Firecrawl(api_key=api_key)
        
        extract_job = firecrawl.start_extract(
            urls,
            prompt=prompt,
            schema=PolicyInfo.model_json_schema()
        )
        
        job_id = extract_job.id
        
        # Poll until complete
        max_attempts = 60
        attempt = 0
        while attempt < max_attempts:
            status = firecrawl.get_extract_status(job_id)
            if status.status == "completed":
                return status.data if status.data else []
            elif status.status == "failed":
                print(f"Policy extraction failed: {status}")
                return []
            time.sleep(2)
            attempt += 1
        
        print("Policy extraction timed out")
        return []
    except Exception as e:
        print(f"Error in extract_policy_info: {e}")
        return []

def extract_contact_info(url, api_key, all_site_urls=None):
    """Extract contact information from main page using BeautifulSoup + Claude."""
    try:
        # Start with homepage
        pages_to_try = [url]
        
        # If we have the site map, find relevant pages dynamically
        if all_site_urls:
            contact_keywords = [
                'contact', 'about', 'about-us', 'aboutus', 'contact-us', 'contactus',
                'get-in-touch', 'reach-us', 'find-us', 'locations', 'our-team',
                'who-we-are', 'meet-the-team', 'our-story', 'company', 'touch'
            ]
            
            # Find pages matching contact keywords
            for site_url in all_site_urls:
                url_lower = site_url.lower()
                if any(keyword in url_lower for keyword in contact_keywords):
                    if site_url not in pages_to_try:
                        pages_to_try.append(site_url)
            
            # Limit to top 5 most relevant pages
            pages_to_try = pages_to_try[:5]
        else:
            # Fallback to common patterns
            base_url = url.rstrip('/')
            pages_to_try.extend([
                f"{base_url}/contact",
                f"{base_url}/contact-us",
                f"{base_url}/about",
                f"{base_url}/about-us",
            ])
        
        st.info(f"🔍 Searching {len(pages_to_try)} pages for contact info...")
        
        all_content = ""
        successful_scrapes = []
        
        for page_url in pages_to_try:
            try:
                # Scrape with requests + BeautifulSoup
                response = requests.get(page_url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text content
                text = soup.get_text(separator='\n', strip=True)
                
                # Also specifically get footer content
                footer = soup.find('footer')
                footer_text = ""
                if footer:
                    footer_content = footer.get_text(separator='\n', strip=True)
                    footer_text = f"\n\n=== FOOTER CONTENT ===\n{footer_content}\n"
                
                if text:
                    all_content += f"\n\n=== Content from {page_url} ===\n\n{text}\n{footer_text}\n"
                    successful_scrapes.append(page_url)
                    
            except Exception as e:
                # Silent fail for 404s and other errors
                continue
        
        if not all_content or len(all_content) < 200:
            st.warning("Could not scrape sufficient content from the website")
            return {}
        
        st.success(f"✅ Successfully scraped {len(successful_scrapes)} pages")
        
        # Debug expander
        with st.expander("🔍 Debug: Scraped Content Preview", expanded=False):
            st.write(f"**Pages scraped:** {', '.join(successful_scrapes)}")
            st.write(f"**Total content length:** {len(all_content)} characters")
            st.text_area("Content preview (first 5000 chars)", all_content[:5000], height=300)
            
            # Check for contact info indicators
            has_email = '@' in all_content
            has_phone = bool(re.search(r'\d{3}[-.)]\s*\d{3}[-.)]\s*\d{4}', all_content))
            has_footer = 'FOOTER CONTENT' in all_content
            
            st.write(f"**Found:** Email={has_email}, Phone pattern={has_phone}, Footer={has_footer}")
        
        # Use Claude to extract contact info
        import anthropic
        client = anthropic.Anthropic(api_key=st.secrets["api"]["ANTHROPIC_API_KEY"])
        
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Extract contact information from this website content. 

Look through ALL the content carefully, especially sections marked "FOOTER CONTENT".

Find and extract:
- Business name (company name, brand name)
- Physical address (street, city, state, zip)
- Phone number (any format)
- Email address (look for @ symbol)

Return ONLY valid JSON: {{"business_name": "...", "address": "...", "phone": "...", "email": "..."}}
Use null for fields not found.

Content:
{all_content[:20000]}"""
            }]
        )
        
        response_text = message.content[0].text
        
        with st.expander("🤖 Debug: Claude Extraction Response", expanded=False):
            st.text(response_text)
        
        # Parse JSON
        try:
            cleaned = response_text.strip()
            if '```' in cleaned:
                cleaned = cleaned.replace('```json', '').replace('```', '')
            
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(cleaned)
        except Exception as parse_error:
            st.error(f"Parse error: {parse_error}")
            return {}
            
    except Exception as e:
        st.error(f"Error in extract_contact_info: {e}")
        import traceback
        st.text(traceback.format_exc())
        return {}

# --- Run Analysis ---
if st.button("🚀 Run Complete Analysis", type="primary"):
    if not site_url:
        st.error("Please enter a website URL.")
    else:
        if 'analysis_complete' not in st.session_state:
            st.session_state['analysis_complete'] = False
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Extract contact info
            status_text.text("Step 1/4: Extracting contact information from homepage...")
            progress_bar.progress(0.25)
            try:
                contact_data = extract_contact_info(site_url, firecrawl_api_key)
                st.session_state['contact_data'] = contact_data
            except Exception as e:
                st.warning(f"Could not extract contact info: {e}")
                st.session_state['contact_data'] = {}
            
            # Step 2: Get domain info
            status_text.text("Step 2/4: Fetching domain information...")
            progress_bar.progress(0.50)
            domain = get_domain_from_url(site_url)
            whois_info = {}
            if domain and whois_api_key:
                try:
                    whois_info = get_whois_info(domain, whois_api_key)
                except Exception as e:
                    st.warning(f"Could not fetch WHOIS info: {e}")
                    whois_info = {"Site Age": "N/A", "Registered Date": "N/A", "Registrar": "N/A"}
            st.session_state['whois_info'] = whois_info
            
            # Step 3: Map site
            status_text.text("Step 3/4: Mapping site and finding policy pages...")
            progress_bar.progress(0.75)
            try:
                all_urls = map_site(site_url, firecrawl_api_key, limit=limit, sitemap_mode=sitemap_mode)
                policy_urls = filter_policy_urls(all_urls, keywords_input)
                st.session_state['policy_urls'] = policy_urls
                st.session_state['total_urls'] = len(all_urls)
            except Exception as e:
                st.warning(f"Could not map site: {e}")
                st.session_state['policy_urls'] = []
                st.session_state['total_urls'] = 0
            
            # Step 4: Extract policy info
            status_text.text("Step 4/4: Extracting policy information...")
            policy_urls = st.session_state.get('policy_urls', [])
            if policy_urls:
                try:
                    selected_urls = policy_urls[:min(10, len(policy_urls))]
                    extracted_data = extract_policy_info(selected_urls, firecrawl_api_key, extraction_prompt)
                    st.session_state['extracted_data'] = extracted_data
                    st.session_state['extracted_urls'] = selected_urls
                except Exception as e:
                    st.warning(f"Could not extract policy info: {e}")
                    st.session_state['extracted_data'] = []
                    st.session_state['extracted_urls'] = []
            else:
                st.session_state['extracted_data'] = []
                st.session_state['extracted_urls'] = []
            
            progress_bar.progress(1.0)
            status_text.text("✅ Analysis complete!")
            st.session_state['analysis_complete'] = True
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Error during analysis: {e}")
            import traceback
            st.error(traceback.format_exc())

# --- Display Results ---
if st.session_state.get('analysis_complete', False):
    st.divider()
    
    # --- AI Summary Section ---
    st.header("📋 Underwriting Summary")
    
    if 'ai_summary' not in st.session_state:
        if st.button("Generate Summary Report", type="primary", use_container_width=True):
            with st.spinner("Generating comprehensive summary with Claude Sonnet 4.5..."):
                try:
                    import anthropic
                    
                    client = anthropic.Anthropic(api_key=anthropic_api_key)
                    
                    contact_data = st.session_state.get('contact_data', {})
                    whois_info = st.session_state.get('whois_info', {})
                    extracted_data = st.session_state.get('extracted_data', [])
                    extracted_urls = st.session_state.get('extracted_urls', [])
                    
                    data_with_sources = []
                    for idx, item in enumerate(extracted_data):
                        url = extracted_urls[idx] if idx < len(extracted_urls) else "Unknown"
                        data_with_sources.append({
                            "source_url": url,
                            "data": item
                        })
                    
                    prompt = f"""You are an underwriting analyst. Create a comprehensive summary report for this website analysis.

BUSINESS INFORMATION:
- Business Name: {contact_data.get('business_name', 'Not found')}
- Address: {contact_data.get('address', 'Not found')}
- Phone: {contact_data.get('phone', 'Not found')}
- Email: {contact_data.get('email', 'Not found')}

DOMAIN INFORMATION:
- Website Age: {whois_info.get('Site Age', 'N/A')}
- Registered Date: {whois_info.get('Registered Date', 'N/A')}
- Hosting Provider/Registrar: {whois_info.get('Registrar', 'N/A')}

POLICY DATA EXTRACTED:
{json.dumps(data_with_sources, indent=2)}

Please create a clear, professional summary that includes:

1. **Business Contact Information** - List the business name, address, phone, and email. If any are missing, state "Not found on website"

2. **Website & Domain Details** - Include website age, registration date, and hosting provider/registrar

3. **Policy Analysis** - For each policy area:
   - Summarize the key information found
   - Cite the source URL where it was found

   a. Misleading or Deceptive Content
    Exaggerated claims
    Guaranteed results
    Before-and-after photos
    Scientific claims without credible reference
    Medical or therapeutic claims without substantiation
    Anything deceptive or predatory
    Fake or paid testimonials
    Misleading “limited time” or “scarcity” language
    Hidden terms or unclear refund policies

   b. High-Risk Sales and Billing Practices

     Negative-option or continuity billing without explicit consent
    Lifetime memberships or subscriptions
    Annual memberships with unclear renewal terms
    Long delivery timeframes
    Services taking more than one year to deliver
    Deferred delivery for intangible goods
    Preorders with no confirmed delivery date
    Unclear cancellation or refund process

   c. Prohibited or Restricted Products and Services

    Adult or pornographic content
    Counterfeit or replica goods
    Unlicensed pharmaceuticals, supplements, or medical devices
    Marijuana, CBD, or hemp-derived products
    Tobacco, vaping, or e-cigarette products
    Weapons, ammunition, or explosives
    Fireworks or hazardous materials
    Gambling, betting, or sports picks
    Auction sites facilitating peer-to-peer sales
    Occult, psychic, or spiritual magic services
    Timeshare resale or exit services
    Extended warranties not backed by licensed providers
    Escort or companionship services

   d. Financial and Investment-Related Risks

    MLM (multi-level marketing) or pyramid structures
    Get-rich-quick or investment schemes
    Cryptocurrency sales, exchange, or mining services
    Debt relief, credit repair, or credit washing services
    Loan modification or foreclosure rescue
    Unlicensed money transmission or financial services
    Investment or trading advice with promised returns

   e. Regulatory or Legal Compliance Risks

    Sale of personal data or leads
    Ticket resale without authorization
    Government ID or document services (e.g., passports, licenses)
    Fundraising or donations without nonprofit verification
    Unlicensed health or legal services
    Products or services requiring professional certification without disclosure

   f. Operational or Reputational Red Flags

    Unrealistic pricing or “too good to be true” offers
    Poor or missing contact information
    Lack of clear business identity or address
    High volume of consumer complaints or negative reviews
    Domains recently registered or anonymized
    International fulfillment with no clear business registration


Format the response in clear sections with headers. Be concise but thorough."""

                    message = client.messages.create(
                        model="claude-sonnet-4-5-20250929",
                        max_tokens=2048,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    summary = message.content[0].text
                    st.session_state['ai_summary'] = summary
                    st.rerun()
                    
                except ImportError:
                    st.error("⚠️ Please install the Anthropic library: `pip install anthropic`")
                except Exception as e:
                    st.error(f"Error generating summary: {e}")
    
    if 'ai_summary' in st.session_state:
        st.markdown(st.session_state['ai_summary'])
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🗑️ Clear Summary"):
                del st.session_state['ai_summary']
                st.rerun()
        with col2:
            st.download_button(
                "📥 Download Summary",
                data=st.session_state['ai_summary'],
                file_name="underwriting_summary.txt",
                mime="text/plain"
            )
    
    st.divider()
    
    # --- Detailed Tabs ---
    st.header("📊 Detailed Analysis")
    tab1, tab2, tab3, tab4 = st.tabs(["📞 Contact Info", "🌐 Domain Info", "🧾 Policy Pages", "📝 Raw Data"])
    
    with tab1:
        st.subheader("Contact Information")
        contact_data = st.session_state.get('contact_data', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Business Name:**", contact_data.get('business_name') or "_Not found_")
            st.write("**Phone:**", contact_data.get('phone') or "_Not found_")
        with col2:
            st.write("**Email:**", contact_data.get('email') or "_Not found_")
            st.write("**Address:**", contact_data.get('address') or "_Not found_")
    
    with tab2:
        st.subheader("Domain Information")
        whois_info = st.session_state.get('whois_info', {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Site Age", whois_info.get("Site Age", "N/A"))
        with col2:
            st.metric("Registered Date", whois_info.get("Registered Date", "N/A")[:10] if whois_info.get("Registered Date") != "N/A" else "N/A")
        with col3:
            st.info(f"**Registrar:** {whois_info.get('Registrar', 'N/A')}")
    
    with tab3:
        st.subheader("Policy Page Discovery")
        total_urls = st.session_state.get('total_urls', 0)
        policy_urls = st.session_state.get('policy_urls', [])
        
        st.success(f"✅ Mapped {total_urls} URLs, found {len(policy_urls)} policy-related pages")
        
        if policy_urls:
            for url in sorted(policy_urls):
                st.markdown(f"- [{url}]({url})")
    
    with tab4:
        st.subheader("Extracted Policy Data")
        extracted_data = st.session_state.get('extracted_data', [])
        extracted_urls = st.session_state.get('extracted_urls', [])
        
        if extracted_data:
            for idx, item in enumerate(extracted_data):
                url = extracted_urls[idx] if idx < len(extracted_urls) else "Unknown"
                with st.expander(f"📄 Page {idx + 1}", expanded=False):
                    st.markdown(f"**source_url:** [{url}]({url})")
                    st.write("")
                    json_str = json.dumps(item)
                    st.code(json_str, language=None)
        else:
            st.info("No policy data extracted")
    
    st.divider()
    if st.button("🔄 Start New Analysis"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
