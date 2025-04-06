import streamlit as st
import pandas as pd
from datetime import datetime
from pages.utils.database import get_trip_details, add_booking, get_booking_history
from pages.utils.helpers import inject_custom_css, show_navigation, show_footer
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def send_booking_confirmation_email(user_email, booking_id, trip_details, num_seats):
    """Send a confirmation email to the user after booking."""
    # Email configuration
    sender_email = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not password:
        st.error("Email configuration is missing. Please check your .env file.")
        return False

    # Email content
    subject = "BusNexus - Booking Confirmation"
    body = f"""
    Dear {trip_details['first_name']},  <!-- Assuming first_name is available in user session -->

    Thank you for booking with BusNexus! Below are the details of your booking:

    Booking ID: {booking_id}
    Trip Details:
    - Bus No: {trip_details['bus_no']}
    - Route: {trip_details['origin']} to {trip_details['destination']}
    - Departure: {trip_details['departure_datetime']}
    - Arrival: {trip_details['arrival_datetime']}
    - Number of Seats: {num_seats}
    - Total Fare: ${trip_details['base_fare'] * num_seats:.2f}

    Please keep this email for your records. For any queries, contact us at support@busnexus.com.

    Best regards,
    The BusNexus Team
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

def main():
    # Set page configuration
    st.set_page_config(page_title="Booking - BusNexus", layout="wide")
    
    # Inject custom CSS for consistent styling
    inject_custom_css()
    
    # Display navigation bar
    
    # Check if user is logged in
    if 'user' not in st.session_state or not st.session_state.get('user'):
        st.error("Please log in to book a trip.")
        st.switch_page("main.py")
        return
    
    # Get user details from session state
    user = st.session_state['user']
    
    # Display page header
    st.title(f"Book a Trip - Welcome, {user['first_name']}!")
    
    # Check if trip details are available
    if 'selected_trip' not in st.session_state:
        # Fallback: Try to fetch trip details using selected_trip_id if available
        if 'selected_trip_id' in st.session_state:
            selected_trip = get_trip_details(st.session_state['selected_trip_id'])
            print(selected_trip)
            if selected_trip:
                st.session_state['selected_trip'] = selected_trip
            else:
                st.warning("No trip selected or trip not found. Please search for a trip first.")
                if st.button("Go to Search"):
                    st.switch_page("main.py")
                return
        else:
            st.warning("No trip selected. Please search for a trip first.")
            if st.button("Go to Search"):
                st.switch_page("main.py")
            return
    
    selected_trip = st.session_state['selected_trip']
    
    # Display trip details
    st.subheader("Trip Details")
    st.write(f"**Bus No:** {selected_trip['bus_no']}")
    st.write(f"**Route:** {selected_trip['origin']} to {selected_trip['destination']}")
    st.write(f"**Departure:** {selected_trip['departure_datetime']}")
    st.write(f"**Arrival:** {selected_trip['arrival_datetime']}")
    st.write(f"**Seats Available:** {selected_trip['seats_available']}")

    # Booking form
    st.subheader("Booking Information")
    with st.form("booking_form"):
        num_seats = st.number_input("Number of Seats", min_value=1, max_value=selected_trip['seats_available'], step=1, value=1)
        submit = st.form_submit_button("Confirm Booking")
        
        if submit:
            if num_seats > selected_trip['seats_available']:
                st.error("Requested seats exceed available seats.")
            else:
                # Prepare booking data
                booking_data = {
                    "user_id": user['user_id'],
                    "trip_id": selected_trip['trip_id'],
                    "num_seats": num_seats,
                    "booking_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                
                # Call database function to add booking
                success, booking_id = add_booking(**booking_data)
                if success:
                    # Send confirmation email
                    email_success = send_booking_confirmation_email(
                        user_email=user['email'],
                        booking_id=booking_id,
                        trip_details=selected_trip,
                        num_seats=num_seats
                    )
                    if email_success:
                        st.success(f"Booking confirmed! Your booking ID is {booking_id}. A confirmation email has been sent to {user['email']}.")
                    else:
                        st.success(f"Booking confirmed! Your booking ID is {booking_id}. Failed to send confirmation email.")
                    # Clear selected trip from session state
                    del st.session_state['selected_trip']
                    if 'selected_trip_id' in st.session_state:
                        del st.session_state['selected_trip_id']
                    st.rerun()
                else:
                    st.error("Failed to confirm booking. Please try again.")
    
    # Display booking history
    st.subheader("Your Bookings")
    bookings = get_booking_history(user['user_id'])
    if bookings:
        df_bookings = pd.DataFrame(bookings)
        st.dataframe(df_bookings[['booking_id', 'booking_datetime', 'total_fare', 'booking_status', 'payment_status']])
    else:
        st.info("No bookings found.")
    
    # Display footer
    show_footer()

if __name__ == "__main__":
    main()