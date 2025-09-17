import os
import streamlit as st
import requests
from datetime import date

# Load API key
PERPLEXITY_API_KEY = st.secrets["api"]["PERPLEXITY_API_KEY"]

st.title("🕵️ Applicant Reputation & Fraud Screening")

# --- Inputs ---
name = st.text_input("Name")
dob = st.date_input("Date of Birth", value=date(1980, 1, 1))
business = st.text_input("Business")
home_address = st.text_input("Home Address")

if st.button("Run Background Research"):
    if not PERPLEXITY_API_KEY:
        st.error("Missing Perplexity API Key in Streamlit secrets.")
    else:
        # Build prompt
        prompt = f"""
You are a research assistant for a payments company.
We need to investigate a potential applicant for reputational harm, fraud, or other risks.

Here is the applicant's information:
- Name: {name}
- Date of Birth: {dob.strftime('%m/%d/%Y')}
- Business: {business}
- Home Address: {home_address}

Please research and summarize:
1. Lawsuits, regulatory actions, or financial disputes involving this person or their business.
2. Criminal records, arrests, or negative legal history.
3. Negative media coverage, reputational harm, or controversies.
4. Any links to fraud, scams, or unethical behavior.
5. Other information relevant to financial risk or reputational exposure.

Return your findings in a structured format:
- **Summary**
- **Key Findings** (with sources)
- **Risk Level Assessment**
        """

        # Call Perplexity API
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar-medium-chat",
                "messages": [
                    {"role": "system", "content": "You are a highly accurate research assistant."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
            },
        )

        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            st.subheader("Research Results")
            st.markdown(answer)
        else:
            st.error(f"Error: {response.status_code} - {response.text}")
