import streamlit as st
import streamlit_authenticator as stauth

def init_authenticator():
    """Initialize the authenticator object"""
    credentials = st.secrets["credentials"].to_dict()
    cookie_cfg = st.secrets["cookie"].to_dict()
    
    authenticator = stauth.Authenticate(
        credentials,
        cookie_cfg["name"],
        cookie_cfg["key"],
        int(cookie_cfg["expiry_days"])
    )
    return authenticator

def check_authentication():
    """Check if user is authenticated. If not, redirect to login page."""
    
    # Initialize session state if not exists
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = None
    if "name" not in st.session_state:
        st.session_state.name = None
    if "username" not in st.session_state:
        st.session_state.username = None
    
    # If not authenticated, show access denied and redirect
    if st.session_state.authentication_status != True:
        st.error("🔒 Access Denied")
        st.warning("You must be logged in to access this page.")
        st.info("Please go to the main page to log in.")
        
        # Add a button to redirect to main page
        if st.button("Go to Login Page"):
            st.switch_page("main.py")  # For Streamlit 1.29.0+
            
        # Alternative redirect method for older Streamlit versions
        # st.markdown("[Click here to login](./)")
        
        st.stop()
    
    return True

def get_user_info():
    """Get current user information"""
    return {
        "name": st.session_state.get("name"),
        "username": st.session_state.get("username"),
        "authentication_status": st.session_state.get("authentication_status")
    }

def show_logout_sidebar():
    """Show logout button in sidebar"""
    authenticator = init_authenticator()
    authenticator.logout('Logout', 'sidebar')
    
    # Show user info
    with st.sidebar:
        st.success("✅ Authenticated")
        st.write(f"**User:** {st.session_state.name}")
        st.write(f"**Email:** {st.session_state.username}")

def require_auth(page_title="Protected Page"):
    """Decorator-like function to protect pages"""
    st.set_page_config(page_title=page_title, page_icon="🔒")
    
    if check_authentication():
        show_logout_sidebar()
        return True
    return False
