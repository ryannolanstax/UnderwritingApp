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


# ---- Updated login method (newer versions) ----
try:
    # For newer versions of streamlit-authenticator
    name, authentication_status, username = authenticator.login()
    
    # ---- check login ----
    if authentication_status:
        st.success(f"Welcome {name}!")
        authenticator.logout("Logout", "sidebar")
        
        # Your main app content goes here
        st.write("You are now logged in and can access the app!")
        
    elif authentication_status is False:
        st.error("Username/password is incorrect")
    else:
        st.info("Please enter your username and password")
        
except Exception as e:
    # Fallback for older versions or different return format
    st.error(f"Authentication error: {str(e)}")
    
    # Try the old method as fallback
    try:
        login_result = authenticator.login()
        if isinstance(login_result, dict):
            if login_result.get("authentication_status"):
                st.success(f"Welcome {login_result.get('name')}!")
                authenticator.logout("Logout", "sidebar")
            elif login_result.get("authentication_status") is False:
                st.error("Username/password is incorrect")
            else:
                st.info("Please enter your username and password")
    except Exception as e2:
        st.error(f"Login system error: {str(e2)}")
        st.info("Please check your streamlit-authenticator version and configuration")

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
