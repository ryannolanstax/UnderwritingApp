import streamlit as st
import sys
import os

# Add the parent directory to Python path to import auth_utils
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from auth_utils import require_auth, get_user_info

# This will check authentication and redirect if not logged in
if require_auth("Your Page Title"):
    # Your protected page content goes here
    user_info = get_user_info()
