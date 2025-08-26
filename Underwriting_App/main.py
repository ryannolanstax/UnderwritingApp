import streamlit as st
import streamlit_authenticator as stauth

# Must set page config before any other Streamlit commands
st.set_page_config(
    page_title="Welcome",
    page_icon="👋",
)

# Initialize session state variables
if "authentication_status" not in st.session_state:
    st.session_state.authentication_status = None
if "name" not in st.session_state:
    st.session_state.name = None
if "username" not in st.session_state:
    st.session_state.username = None

# Load configuration from secrets
credentials = st.secrets["credentials"].to_dict()
cookie_cfg = st.secrets["cookie"].to_dict()

# Create authenticator (without preauthorized for now to simplify)
authenticator = stauth.Authenticate(
    credentials,
    cookie_cfg["name"],
    cookie_cfg["key"],
    int(cookie_cfg["expiry_days"])
)

# Authentication logic
if st.session_state.authentication_status != True:
    try:
        name, authentication_status, username = authenticator.login(location='main')
        
        if name is not None or authentication_status is not None:
            st.session_state.name = name
            st.session_state.authentication_status = authentication_status
            st.session_state.username = username
            
    except Exception as e:
        st.error("Login error occurred. Please refresh the page.")
        st.stop()

# Display content based on authentication
if st.session_state.authentication_status == True:
    st.success(f'Welcome *{st.session_state.name}*')
    authenticator.logout('Logout', 'sidebar')
    
    # Your main app content here
    st.header("Main Application")
    st.write("You are successfully logged in!")
    
elif st.session_state.authentication_status == False:
    st.error('Username/password is incorrect')
    
elif st.session_state.authentication_status == None:
    st.warning('Please enter your username and password')
