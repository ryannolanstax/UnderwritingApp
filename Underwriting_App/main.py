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
try:
    credentials = st.secrets["credentials"].to_dict()
    cookie_cfg = st.secrets["cookie"].to_dict()
    
    # Check if we have the required data
    st.write("Debug: Loaded credentials and cookie config successfully")
    
except Exception as e:
    st.error(f"Error loading secrets: {e}")
    st.stop()

# Create authenticator
try:
    authenticator = stauth.Authenticate(
        credentials,
        cookie_cfg["name"],
        cookie_cfg["key"],
        int(cookie_cfg["expiry_days"])
    )
    st.write("Debug: Authenticator created successfully")
    
except Exception as e:
    st.error(f"Error creating authenticator: {e}")
    st.stop()

# Authentication logic - try different approaches
if st.session_state.authentication_status != True:
    
    # Method 1: Try the standard approach
    try:
        st.write("Debug: Attempting login method 1...")
        result = authenticator.login(location='main')
        st.write(f"Debug: Login result type: {type(result)}")
        st.write(f"Debug: Login result: {result}")
        
        if result is not None:
            if isinstance(result, tuple) and len(result) == 3:
                name, authentication_status, username = result
                st.session_state.name = name
                st.session_state.authentication_status = authentication_status
                st.session_state.username = username
                st.write("Debug: Successfully unpacked tuple result")
            else:
                st.write("Debug: Result is not a 3-tuple, trying as dict...")
                if hasattr(result, 'get'):
                    st.session_state.name = result.get('name')
                    st.session_state.authentication_status = result.get('authentication_status')
                    st.session_state.username = result.get('username')
    
    except Exception as e:
        st.error(f"Login method 1 failed: {e}")
        
        # Method 2: Try without location parameter
        try:
            st.write("Debug: Attempting login method 2...")
            result = authenticator.login()
            st.write(f"Debug: Login result: {result}")
            
            if result is not None:
                if isinstance(result, tuple) and len(result) == 3:
                    name, authentication_status, username = result
                    st.session_state.name = name
                    st.session_state.authentication_status = authentication_status
                    st.session_state.username = username
        
        except Exception as e2:
            st.error(f"Login method 2 also failed: {e2}")
            
            # Method 3: Try with form parameters
            try:
                st.write("Debug: Attempting login method 3...")
                result = authenticator.login('Login', 'main')
                st.write(f"Debug: Login result: {result}")
                
            except Exception as e3:
                st.error(f"All login methods failed. Last error: {e3}")
                st.write("Please check your streamlit-authenticator version:")
                st.code("pip show streamlit-authenticator")

# Display current session state
st.write("### Current Session State:")
st.write(f"Authentication Status: {st.session_state.authentication_status}")
st.write(f"Name: {st.session_state.name}")
st.write(f"Username: {st.session_state.username}")

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

# Show secrets structure for debugging (remove in production)
st.write("### Secrets Debug Info:")
st.write("Usernames available:", list(credentials.get('usernames', {}).keys()) if 'usernames' in credentials else 'No usernames key found')
st.write("Cookie config keys:", list(cookie_cfg.keys()))
