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

# Create authenticator
authenticator = stauth.Authenticate(
    credentials,
    cookie_cfg["name"],
    cookie_cfg["key"],
    int(cookie_cfg["expiry_days"])
)

# Authentication - using the correct syntax for version 0.2.3
name, authentication_status, username = authenticator.login('Login', 'main')

# Update session state with current authentication results
st.session_state.name = name
st.session_state.authentication_status = authentication_status
st.session_state.username = username

# Display content based on authentication status
if st.session_state.authentication_status == True:
    st.success(f'Welcome *{st.session_state.name}*!')
    
    # Add logout button to sidebar
    authenticator.logout('Logout', 'sidebar')
    
    # Your main app content here
    st.header("🎉 Main Application")
    st.write("You are successfully logged in and can now access the application!")
    
    # Add your actual app content below
    st.subheader("Application Features")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("📊 Feature 1")
        st.write("Add your first feature here")
        
    with col2:
        st.info("📈 Feature 2") 
        st.write("Add your second feature here")
    
    # Example of protected content
    with st.expander("Protected Data"):
        st.write("This content is only visible to authenticated users")
        st.dataframe({"Sample": [1, 2, 3], "Data": [4, 5, 6]})

elif st.session_state.authentication_status == False:
    st.error('Username/password is incorrect')
    st.info('Please check your credentials and try again')

elif st.session_state.authentication_status == None:
    st.warning('Please enter your username and password')
    st.info('👆 Use the login form above to access the application')

# Optional: Show login status in sidebar for debugging
with st.sidebar:
    st.write("**Login Status:**")
    if st.session_state.authentication_status == True:
        st.success("✅ Authenticated")
        st.write(f"User: {st.session_state.name}")
        st.write(f"Email: {st.session_state.username}")  # This will show the email
    else:
        st.warning("🔒 Not authenticated")
        
    # Show available usernames (emails) for testing
    if st.checkbox("Show available emails"):
        available_emails = list(credentials.get('usernames', {}).keys())
        st.write("Available email addresses:")
        for email in available_emails:
            st.write(f"📧 {email}")
