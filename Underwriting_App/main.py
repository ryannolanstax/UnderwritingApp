# Initialize session state variables first
if "authentication_status" not in st.session_state:
    st.session_state.authentication_status = None
if "name" not in st.session_state:
    st.session_state.name = None
if "username" not in st.session_state:
    st.session_state.username = None

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

# ---- Authentication Logic ----
# Only call login if not already authenticated
if st.session_state.authentication_status != True:
    try:
        name, authentication_status, username = authenticator.login(location='main')
        
        # Only update session state if we got valid results
        if name is not None or authentication_status is not None:
            st.session_state.name = name
            st.session_state.authentication_status = authentication_status
            st.session_state.username = username
            
    except Exception as e:
        st.error("Authentication system error. Please refresh the page.")
        st.stop()

# ---- Display content based on authentication status ----
if st.session_state.authentication_status == True:
    # User is authenticated - show main content
    st.success(f'Welcome *{st.session_state.name}*')
    
    # Logout button in sidebar
    authenticator.logout('Logout', 'sidebar')
    
    # Main app content
    st.header("🎉 Successfully Logged In!")
    st.write("You now have access to the application.")
    
    # Add your main application content here
    st.subheader("Main Application")
    st.write("This is where your app content goes...")
    
    # Example content
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.info("Feature 1")
            st.write("Add your first feature here")
        with col2:
            st.info("Feature 2") 
            st.write("Add your second feature here")

elif st.session_state.authentication_status == False:
    st.error('Username/password is incorrect')
    
elif st.session_state.authentication_status == None:
    st.warning('Please enter your username and password')
    st.info('Use the login form above to access the application')

# Debug information (remove in production)
with st.expander("Debug Info (Remove in Production)"):
    st.write(f"Authentication Status: {st.session_state.authentication_status}")
    st.write(f"Name: {st.session_state.name}")
    st.write(f"Username: {st.session_state.username}")
