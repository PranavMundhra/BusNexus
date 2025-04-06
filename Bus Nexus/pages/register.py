import streamlit as st
import re
from pages.utils.database import register_user
from pages.utils.helpers import inject_custom_css, show_navigation, show_footer

def main():
    # Set page configuration
    st.set_page_config(page_title="Register - BusNexus", layout="centered")
    
    # Inject custom CSS for styling
    inject_custom_css()
    
    # Display navigation bar
    
    # Page title
    st.title("Create an Account")
    
    # Registration form
    with st.form("register_form"):
        first_name = st.text_input("First Name", placeholder="Enter your first name")
        last_name = st.text_input("Last Name", placeholder="Enter your last name")
        email = st.text_input("Email", placeholder="example@email.com")
        phone = st.text_input("Phone Number", placeholder="Enter your phone number")
        password = st.text_input("Password", type="password", placeholder="At least 6 characters")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
        
        # Submit button
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            # Trim input fields (except passwords)
            first_name = first_name.strip()
            last_name = last_name.strip()
            email = email.strip()
            phone = phone.strip()
            
            # Email validation pattern
            email_pattern = r"[^@]+@[^@]+\.[^@]+"
            
            # Form validation
            if not all([first_name, last_name, email, phone, password, confirm_password]):
                st.error("All fields are required.")
            elif not re.match(email_pattern, email):
                st.error("Invalid email format.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            else:
                # Attempt to register the user
                success, message = register_user(first_name, last_name, email, phone, password, role='passenger')
                if success:
                    st.success("Registration successful! You can now log in.")
                else:
                    st.error(message)
    
    # Display footer
    show_footer()

if __name__ == "__main__":
    main()