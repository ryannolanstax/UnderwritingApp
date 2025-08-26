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

secrets = st.secrets

credentials = {
    "usernames": {
        secrets["credentials"]["username"]: {
            "name": secrets["credentials"]["name"],
            "password": stauth.Hasher([secrets["credentials"]["password"]]).generate()[0]
        }
    }
}

cookie_cfg = secrets["cookie"]
cookie_name = cookie_cfg["name"]
cookie_key = cookie_cfg["key"]
cookie_expiry_days = int(cookie_cfg["expiry_days"])

# ---- create authenticator ----
authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    cookie_key,
    cookie_expiry_days
)

# ---- login UI ----
name, authentication_status, username = authenticator.login("Login", location="main")  # <-- fix here

if authentication_status:
    st.success(f"Welcome {name}!")
    authenticator.logout("Logout", "sidebar")
elif authentication_status is False:
    st.error("Username/password is incorrect")
else:
    st.info("Please enter your username and password")

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
