import streamlit as st
from datetime import datetime, timedelta
from pages.utils.database import get_booking_history, cancel_booking, get_distinct_origins, get_distinct_destinations
from pages.utils.helpers import inject_custom_css, show_navigation, show_footer, format_datetime

def main():
    # Set page configuration
    st.set_page_config(page_title="Passenger Dashboard - BusNexus", layout="wide")
    
    # Inject custom CSS for consistent styling
    inject_custom_css()
    
    # Display navigation bar
    
    # Check if user is logged in and has 'passenger' role
    if 'user' not in st.session_state or st.session_state['user']['role'] != 'passenger':
        st.error("Please log in as a passenger to access this page.")
        st.switch_page("pages/Login.py")
        return
    
    # Get user details from session state
    user = st.session_state['user']
    
    # Display welcome message
    st.title(f"Welcome, {user['first_name']} {user['last_name']}!")
    
    # Display bus search form
    display_search_form()
    
    # Display booking history
    display_booking_history(user['user_id'])
    
    # Display footer
    show_footer()

def display_search_form():
    """Display the bus search form and handle search submissions."""
    st.subheader("Search Buses")
    
    # Fetch distinct origins and destinations from the database
    origins = get_distinct_origins()
    destinations = get_distinct_destinations()
    
    # Provide default options if database returns no data
    if not origins:
        origins = ["New York", "Boston", "Chicago", "Los Angeles", "Washington D.C."]
    if not destinations:
        destinations = ["Boston", "New York", "Chicago", "Los Angeles", "Washington D.C."]
    
    # Create layout with columns for search inputs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        origin = st.selectbox("From", options=origins, key="origin")
    
    with col2:
        destination = st.selectbox("To", options=destinations, key="destination")
    
    with col3:
        # Set default to tomorrow and restrict past dates
        tomorrow = datetime.now() + timedelta(days=1)
        travel_date = st.date_input("Journey Date", value=tomorrow, min_value=datetime.now().date(), key="travel_date")
    
    # Additional filters
    col4, col5 = st.columns(2)
    
    with col4:
        bus_type = st.selectbox("Bus Type", options=["Any", "AC", "Non-AC", "Sleeper", "Deluxe"], index=0, key="bus_type")
    
    with col5:
        price_range = st.slider("Price Range ($)", min_value=10, max_value=200, value=(10, 200), step=5, key="price_range")
    
    # Search button with validation
    if st.button("Search", key="search_button"):
        if not origin or not destination or not travel_date:
            st.error("Please select origin, destination, and travel date.")
        elif origin == destination:
            st.error("Origin and destination cannot be the same.")
        else:
            # Store search parameters in session state
            st.session_state["search_params"] = {
                "origin": origin,
                "destination": destination,
                "travel_date": travel_date,
                "bus_type": bus_type if bus_type != "Any" else None,
                "min_price": price_range[0],
                "max_price": price_range[1]
            }
            # Redirect to search results page
            st.switch_page("pages/SearchBuses.py")

def display_booking_history(user_id):
    """Fetch and display the user's booking history with cancellation options."""
    st.subheader("Your Bookings")
    
    # Fetch user's bookings from the database
    bookings = get_booking_history(user_id)
    
    if not bookings:
        st.info("You have no bookings yet.")
        return
    
    # Display each booking in an expander
    for booking in bookings:
        with st.expander(f"Booking ID: {booking['booking_id']} - {booking['booking_status'].capitalize()}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Trip:** {booking['origin']} to {booking['destination']}")
                st.write(f"**Departure:** {format_datetime(booking['departure_datetime'])}")
                st.write(f"**Bus:** {booking['bus_no']} ({booking['bus_type']})")
            
            with col2:
                st.write(f"**Fare:** ${booking['total_fare']:.2f}")
                st.write(f"**Status:** {booking['booking_status'].capitalize()}")
                
                # Show cancel option for eligible bookings
                if booking['booking_status'] == 'booked' and is_cancellable(booking):
                    if st.button("Cancel Booking", key=f"cancel_{booking['booking_id']}"):
                        if confirm_cancellation():
                            success, message = cancel_booking(booking['booking_id'])
                            if success:
                                st.success("Booking cancelled successfully.")
                                st.rerun()  # Refresh page to reflect changes
                            else:
                                st.error(message)

def is_cancellable(booking):
    """Check if a booking can be cancelled based on departure time."""
    cancellation_window = timedelta(hours=24)
    now = datetime.now()
    if isinstance(booking['departure_datetime'], str):
        departure = datetime.strptime(booking['departure_datetime'], "%Y-%m-%d %H:%M:%S")
    else:
        departure = booking['departure_datetime']

    return departure > now + cancellation_window

def confirm_cancellation():
    """Prompt user to confirm cancellation."""
    return st.checkbox("I confirm that I want to cancel this booking.", key="confirm_cancellation")

if __name__ == "__main__":
    main()