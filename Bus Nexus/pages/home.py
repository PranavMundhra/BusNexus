import streamlit as st
from datetime import datetime, timedelta
from utils.helpers import inject_custom_css, show_navigation, show_footer
from utils.database import get_distinct_origins, get_distinct_destinations, get_search_results

def main():
    st.set_page_config(
        page_title="BusNexus - Home",
        page_icon="🚌",
        layout="wide"
    )
    
    # Store current page in session state
    st.session_state['current_page'] = "Home"
    
    # Apply custom styling
    inject_custom_css()
    
    # Show navigation
    show_navigation()
    
    # Hero section
    st.markdown("""
    <div class="hero">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">BusNexus</h1>
        <p style="font-size: 1.5rem; opacity: 0.8;">Book your bus tickets with ease</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search section
    st.subheader("Find Your Journey")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get distinct origins from database
        origins = get_distinct_origins()
        # If there are no origins in the database, use placeholder data
        if not origins:
            origins = ["New York", "Boston", "Chicago", "Los Angeles", "Washington D.C."]
        origin = st.selectbox(
            "From",
            options=origins,
            index=0,
            key="origin"
        )
    
    with col2:
        # Get distinct destinations from database
        destinations = get_distinct_destinations()
        # If there are no destinations in the database, use placeholder data
        if not destinations:
            destinations = ["Boston", "New York", "Chicago", "Los Angeles", "Washington D.C."]
        destination = st.selectbox(
            "To",
            options=destinations,
            index=1,
            key="destination"
        )
    
    with col3:
        # Default date is tomorrow
        tomorrow = datetime.now() + timedelta(days=1)
        travel_date = st.date_input(
            "Journey Date",
            value=tomorrow,
            min_value=datetime.now().date(),
            key="travel_date"
        )
    
    # Additional filters
    col1, col2 = st.columns(2)
    
    with col1:
        bus_type = st.selectbox(
            "Bus Type",
            options=["Any", "AC", "Non-AC", "Sleeper", "Deluxe"],
            index=0,
            key="bus_type"
        )
    
    with col2:
        price_range = st.slider(
            "Price Range ($)",
            min_value=10,
            max_value=200,
            value=(10, 200),
            step=5,
            key="price_range"
        )
    
    # Search button
    if st.button("Search Buses", key="search_button", use_container_width=True):
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
        st.session_state["current_page"] = "SearchBuses"
        st.experimental_rerun()
    
    # Features section
    st.markdown("### Why Choose BusNexus?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🌐</div>
            <h3>Wide Selection</h3>
            <p>Access multiple bus operators and routes in one place.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💰</div>
            <h3>Best Prices</h3>
            <p>Compare fares to find the best deals for your journey.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🛡️</div>
            <h3>Comfort & Safety</h3>
            <p>Choose from various seating and bus types for a secure ride.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Popular routes section
    st.markdown("### Popular Routes")
    
    col1, col2, col3 = st.columns(3)
    
    popular_routes = [
        {"from": "New York", "to": "Boston", "price": "$45"},
        {"from": "Chicago", "to": "Detroit", "price": "$35"},
        {"from": "Los Angeles", "to": "San Francisco", "price": "$65"}
    ]
    
    with col1:
        st.markdown(f"""
        <div class="route-card">
            <h4>{popular_routes[0]['from']} → {popular_routes[0]['to']}</h4>
            <p>Starting from {popular_routes[0]['price']}</p>
            <button class="view-route-btn">View</button>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="route-card">
            <h4>{popular_routes[1]['from']} → {popular_routes[1]['to']}</h4>
            <p>Starting from {popular_routes[1]['price']}</p>
            <button class="view-route-btn">View</button>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="route-card">
            <h4>{popular_routes[2]['from']} → {popular_routes[2]['to']}</h4>
            <p>Starting from {popular_routes[2]['price']}</p>
            <button class="view-route-btn">View</button>
        </div>
        """, unsafe_allow_html=True)
    
    # Show footer
    show_footer()

if __name__ == "__main__":
    main()