import streamlit as st
from pages.utils.database import login_user
from pages.utils.helpers import inject_custom_css, show_navigation, show_footer

def main():
    # Set page configuration
    st.set_page_config(page_title="Login - BusNexus", layout="centered")
    
    # Inject custom CSS for styling
    inject_custom_css()
    
    # Display navigation bar
    
    # Page title
    st.title("Log In")
    
    # Login form
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="example@email.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        # Submit button
        submit_button = st.form_submit_button("Log In")
        
        if submit_button:
            # Basic validation
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                # Attempt to log in
                success, message = login_user(email, password)
                if success:
                    # Store user data in session state
                    st.session_state['user'] = message
                    st.success("Logged in successfully!")
                    
                    # Redirect based on role
                    if message['role'] == 'passenger':
                        st.switch_page("pages\PassengerDashboard.py")
                    elif message['role'] == 'coordinator':
                        st.switch_page("pages\CoordinatorDashboard.py")
                else:
                    st.error(message)
    
    # Link to registration page
    st.markdown("Don't have an account? [Register here](/Register)")
    
    # Display footer
    show_footer()

if __name__ == "__main__":
    main()