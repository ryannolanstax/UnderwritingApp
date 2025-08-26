import streamlit as st
from PIL import Image
import streamlit_authenticator as stauth
from copy import deepcopy
#import streamlit-authenticator
#https://blog.streamlit.io/streamlit-authenticator-part-1-adding-an-authentication-component-to-your-app/

st.set_page_config(
    page_title="Welcome",
    page_icon="👋",
)

# ---- convert secrets to mutable dict ----
credentials = st.secrets["credentials"].to_dict()
cookie_cfg = st.secrets["cookie"].to_dict()
preauthorized = st.secrets["preauthorized"].to_dict()

# ---- create authenticator ----
authenticator = stauth.Authenticate(
    credentials,
    cookie_cfg["name"],
    cookie_cfg["key"],
    int(cookie_cfg["expiry_days"]),
    preauthorized
)

# ---- Handle authentication ----
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = None
    st.session_state["name"] = None
    st.session_state["username"] = None

# ---- Login widget ----
try:
    # Check if this is the first run or if we need to show login
    if st.session_state["authentication_status"] is None:
        result = authenticator.login('Login', 'main')
        
        # Handle different return formats
        if result is not None:
            if isinstance(result, tuple) and len(result) == 3:
                # New format: returns (name, auth_status, username)
                name, authentication_status, username = result
                st.session_state["authentication_status"] = authentication_status
                st.session_state["name"] = name
                st.session_state["username"] = username
            elif isinstance(result, dict):
                # Old format: returns dictionary
                st.session_state["authentication_status"] = result.get("authentication_status")
                st.session_state["name"] = result.get("name")
                st.session_state["username"] = result.get("username")
        
        # If still None after login attempt, keep showing login form
        if st.session_state["authentication_status"] is None:
            st.rerun()

except Exception as e:
    st.error(f"Authentication error: {str(e)}")
    st.info("Please check your streamlit-authenticator version and try refreshing the page")
    st.stop()

# ---- Check authentication status ----
if st.session_state["authentication_status"]:
    # User is authenticated
    st.success(f"Welcome *{st.session_state['name']}*!")
    
    # Add logout button to sidebar
    authenticator.logout('Logout', 'sidebar')
    
    # Your main app content goes here
    st.write("🎉 You are successfully logged in!")
    st.write("Add your main application content below this line.")
    
    # Example content
    st.header("Main Application")
    st.write("This is where your main app functionality would go.")
    
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
    
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')

# ---- Display current session info for debugging ----
if st.sidebar.checkbox("Debug Info"):
    st.sidebar.write("Session State:")
    st.sidebar.write(f"Auth Status: {st.session_state.get('authentication_status')}")
    st.sidebar.write(f"Name: {st.session_state.get('name')}")
    st.sidebar.write(f"Username: {st.session_state.get('username')}")
    
#password_attempt = st.text_input('Please Enter The Password')
#if password_attempt != 'StaxPeriodicReview':
#    st.write('Incorrect Password!')
#    st.stop

#image = Image.open('Final_Periodic_App/Stax_Banner.png')

#st.image(image)

st.write("# Welcome to Stax Underwriting")

st.markdown(
    """
    This calculator combines the old Tiering + Exposure calculators

    **👈 Select an app from the sidebar** to get started

    If an app isn't working correctly, reach out to Ryan Nolan on
    Slack or email ryan.nolan@fattmerchant.com


    ### Want to learn more?
    - Check out [SOP: Underwriting (NEED LINK)](#)

"""
)
