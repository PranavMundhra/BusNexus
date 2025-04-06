import streamlit as st
from functools import wraps

def check_authentication():
    """Check if user is logged in and return user data"""
    if 'user' not in st.session_state:
        return None
    return st.session_state['user']

def requires_auth(page_function):
    """Decorator to require authentication for a page"""
    @wraps(page_function)
    def wrapper(*args, **kwargs):
        user = check_authentication()
        if not user:
            st.warning("Please log in to access this page")
            st.session_state['redirect_to'] = st.session_state['current_page']
            st.switch_page("pages/Login.py")
            return
        return page_function(*args, **kwargs)
    return wrapper

def requires_role(role):
    """Decorator to require specific role for a page"""
    def decorator(page_function):
        @wraps(page_function)
        def wrapper(*args, **kwargs):
            user = check_authentication()
            if not user:
                st.warning("Please log in to access this page")
                st.session_state['redirect_to'] = st.session_state['current_page']
                st.switch_page("pages/Login.py")
                return
            
            if user.get('role') != role:
                st.error(f"You need {role} permissions to access this page")
                st.switch_page("Home.py")
                return
            
            return page_function(*args, **kwargs)
        return wrapper
    return decorator

def logout():
    """Log out the current user"""
    if 'user' in st.session_state:
        del st.session_state['user']
    
    # Clear any other user-related session state
    for key in list(st.session_state.keys()):
        if key.startswith('user_'):
            del st.session_state[key]