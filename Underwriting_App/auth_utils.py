# auth_utils.py - Create this file in your app directory
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

def get_user_role():
    """Get the current user's role"""
    if st.session_state.authentication_status == True and st.session_state.username:
        credentials = st.secrets["credentials"].to_dict()
        usernames = credentials.get("usernames", {})
        user_data = usernames.get(st.session_state.username, {})
        return user_data.get("role", "Unknown")
    return None

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
            
        st.stop()
    
    return True

def check_role_access(allowed_roles):
    """Check if current user has required role access"""
    user_role = get_user_role()
    
    if user_role is None:
        return False
        
    # Admin always has access to everything
    if user_role == "Admin":
        return True
        
    # Check if user's role is in allowed roles
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
        
    return user_role in allowed_roles

def require_role(allowed_roles, page_title="Restricted Page"):
    """Check authentication and role access"""
    st.set_page_config(page_title=page_title, page_icon="🔒")
    
    # First check authentication
    if not check_authentication():
        return False
    
    # Then check role access
    if not check_role_access(allowed_roles):
        user_role = get_user_role()
        st.error("🚫 Access Restricted")
        st.warning(f"This page requires one of these roles: {', '.join(allowed_roles) if isinstance(allowed_roles, list) else allowed_roles}")
        st.info(f"Your current role: **{user_role}**")
        st.info("Contact your administrator if you need access to this page.")
        
        # Show back button
        if st.button("← Back to Main Page"):
            st.switch_page("main.py")
            
        st.stop()
        return False
    
    # If we reach here, user is authenticated and authorized
    show_logout_sidebar()
    return True

def get_user_info():
    """Get current user information including role"""
    user_role = get_user_role()
    return {
        "name": st.session_state.get("name"),
        "username": st.session_state.get("username"),
        "authentication_status": st.session_state.get("authentication_status"),
        "role": user_role
    }

def show_logout_sidebar():
    """Show logout button in sidebar with role info"""
    authenticator = init_authenticator()
    authenticator.logout('Logout', 'sidebar')
    
    # Show user info including role
    with st.sidebar:
        st.success("✅ Authenticated")
        st.write(f"**User:** {st.session_state.name}")
        st.write(f"**Email:** {st.session_state.username}")
        st.write(f"**Role:** {get_user_role()}")

def require_auth(page_title="Protected Page"):
    """Decorator-like function to protect pages (authentication only)"""
    st.set_page_config(page_title=page_title, page_icon="🔒")
    
    if check_authentication():
        show_logout_sidebar()
        return True
    return False

# Role hierarchy helper functions
def is_admin():
    """Check if current user is admin"""
    return get_user_role() == "Admin"

def can_access_risk():
    """Check if user can access risk features"""
    return check_role_access(["Admin", "Risk"])

def can_access_underwriting():
    """Check if user can access underwriting features"""
    return check_role_access(["Admin", "Underwriting"])

def can_access_direct():
    """Check if user can access direct features"""
    return check_role_access(["Admin", "Direct"])
