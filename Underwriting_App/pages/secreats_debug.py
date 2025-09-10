import streamlit as st

st.title("🔑 Secrets Debugger")

# Check if key is available
if "PERPLEXITY_API_KEY" in st.secrets:
    st.success("✅ Found PERPLEXITY_API_KEY in secrets")
    st.write("Key length:", len(st.secrets["PERPLEXITY_API_KEY"]))
else:
    st.error("❌ PERPLEXITY_API_KEY not found in secrets")
    st.write("Available keys:", list(st.secrets.keys()))
