import streamlit as st
from datetime import datetime, timedelta
from pages.utils.helpers import inject_custom_css, show_navigation, show_footer
from pages.utils.database import get_distinct_origins, get_distinct_destinations, login_user


    
def main():
    # Set page configuration
    st.set_page_config(page_title="BusNexus - Home", layout="wide")    
    # Inject custom CSS for consistent styling
    inject_custom_css()
    
    # Display navigation bar
    
    # Hero section with app title and tagline
    st.markdown("""
    <div class="hero">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">BusNexus</h1>
        <p style="font-size: 1.5rem; opacity: 0.8;">Book your bus tickets with ease</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search section
    st.subheader("Find Your Journey")
    
    # Create columns for search inputs
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Fetch distinct origins from the database or use placeholders
        origins = get_distinct_origins()
        if not origins:
            origins = ["New York", "Boston", "Chicago", "Los Angeles", "Washington D.C."]
        origin = st.selectbox("From", options=origins, index=0, key="origin")
    
    with col2:
        # Fetch distinct destinations from the database or use placeholders
        destinations = get_distinct_destinations()
        if not destinations:
            destinations = ["Boston", "New York", "Chicago", "Los Angeles", "Washington D.C."]
        destination = st.selectbox("To", options=destinations, index=1, key="destination")
    
    with col3:
        # Set default date to tomorrow and restrict to future dates
        tomorrow = datetime.now() + timedelta(days=1)
        travel_date = st.date_input("Journey Date", value=tomorrow, min_value=datetime.now().date(), key="travel_date")
    
    # Additional filters
    col4, col5 = st.columns(2)
    
    with col4:
        bus_type = st.selectbox("Bus Type", options=["Any", "AC", "Non-AC", "Sleeper", "Deluxe"], index=0, key="bus_type")
    
    with col5:
        price_range = st.slider("Price Range ($)", min_value=10, max_value=200, value=(10, 200), step=5, key="price_range")
    
    # Search button with validation and navigation
    if st.button("Search Buses", key="search_button", use_container_width=True):
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
            # Navigate to the search results page
            st.switch_page("pages/SearchBuses.py")
    
    # Features section
    st.markdown("### Why Choose BusNexus?")
    
    feature_col1, feature_col2, feature_col3 = st.columns(3)
    
    with feature_col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🌐</div>
            <h3>Wide Selection</h3>
            <p>Access multiple bus operators and routes in one place.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💰</div>
            <h3>Best Prices</h3>
            <p>Compare fares to find the best deals for your journey.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feature_col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🛡️</div>
            <h3>Comfort & Safety</h3>
            <p>Choose from various seating and bus types for a secure ride.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Optional: Popular routes section (commented out for simplicity)
    # st.markdown("### Popular Routes")
    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     st.markdown("""
    #     <div class="route-card">
    #         <h4>New York → Boston</h4>
    #         <p>Starting from $45</p>
    #         <button class="view-route-btn">View</button>
    #     </div>
    #     """, unsafe_allow_html=True)
    # # Add more routes as needed
    
    # Display footer
    show_footer()

if __name__ == "__main__":
    main()