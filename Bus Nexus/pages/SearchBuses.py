import streamlit as st
from datetime import datetime
from pages.utils.database import get_search_results
from pages.utils.helpers import inject_custom_css, show_navigation, show_footer, format_datetime

def main():
    # Set page configuration
    st.set_page_config(page_title="Search Buses - BusNexus", layout="wide")
    
    # Inject custom CSS for consistent styling
    inject_custom_css()
    
    # Display navigation bar
    
    # Check if search parameters exist in session state
    if "search_params" not in st.session_state:
        st.error("Please perform a search from the home page.")
        st.button("Back to Home", on_click=lambda: st.switch_page("main.py"))
        return
    
    # Retrieve search parameters
    search_params = st.session_state["search_params"]
    origin = search_params.get("origin")
    destination = search_params.get("destination")
    travel_date = search_params.get("travel_date")
    bus_type = search_params.get("bus_type")
    min_price = search_params.get("min_price")
    max_price = search_params.get("max_price")
    
    # Page title with search criteria
    st.title(f"Available Buses from {origin} to {destination} on {travel_date.strftime('%B %d, %Y')}")
    
    # Fetch search results from the database
    results = get_search_results(
        origin=origin,
        destination=destination,
        travel_date=travel_date.strftime("%Y-%m-%d")
    )
    
    # Filter results based on additional parameters
    filtered_results = [
        result for result in results
        if (not bus_type or result["bus_type"] == bus_type) and
        (min_price <= result["base_fare"] <= max_price)
    ] if results else []
    
    # Display search results
    if not filtered_results:
        st.warning("No buses found for the selected criteria.")
    else:
        for result in filtered_results:
            with st.expander(f"Bus {result['bus_no']} - {result['bus_type']}"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.write(f"**Bus No:** {result['bus_no']}")
                    st.write(f"**Type:** {result['bus_type']}")
                
                with col2:
                    st.write(f"**Departure:** {format_datetime(result['departure_datetime'])}")
                    st.write(f"**Arrival:** {format_datetime(result['arrival_datetime'])}")
                
                with col3:
                    st.write(f"**Seats Available:** {result['seats_available']}")
                    st.write(f"**Duration:** {calculate_duration(result['departure_datetime'], result['arrival_datetime'])}")
                
                with col4:
                    st.write(f"**Fare:** ${result['base_fare']:.2f}")
                    if st.button("Book Now", key=f"book_{result['trip_id']}"):
                        # Store full trip details in session state
                        st.session_state['selected_trip'] = result
                        st.switch_page("pages/Booking.py")
    
    # Back button to return to home
    st.button("Back to Home", on_click=lambda: st.switch_page("main.py"))
    
    # Display footer
    show_footer()

def calculate_duration(departure, arrival):
    """Calculate and format the duration between departure and arrival times."""
    if isinstance(departure, str):
        departure = datetime.strptime(departure, "%Y-%m-%d %H:%M:%S")
    if isinstance(arrival, str):
        arrival = datetime.strptime(arrival, "%Y-%m-%d %H:%M:%S")
    
    duration = arrival - departure
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    days = duration.days
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

if __name__ == "__main__":
    main()