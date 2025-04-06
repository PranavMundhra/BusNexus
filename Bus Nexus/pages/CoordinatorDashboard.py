import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim
from pages.utils.database import (
    get_all_buses, add_bus, update_bus, delete_bus,
    get_all_routes, add_route, update_route, delete_route,
    get_all_trips, add_trip,
    get_total_bookings, get_daily_revenue, get_route_popularity,
    get_all_drivers, add_driver, update_driver, delete_driver
)
from pages.utils.helpers import inject_custom_css, show_navigation, show_footer

# Initialize geolocator for geocoding
geolocator = Nominatim(user_agent="busnexus_app")

# Cached function to get coordinates from place names
@st.cache_data
def get_coords_from_place(place):
    try:
        location = geolocator.geocode(place)
        if location:
            return [location.latitude, location.longitude]
        st.warning(f"Could not find coordinates for '{place}'. Please enter a valid location.")
        return None
    except Exception as e:
        st.error(f"Geocoding error for '{place}': {str(e)}")
        return None

def main():
    # Set page configuration
    st.set_page_config(page_title="Coordinator Dashboard - BusNexus", layout="wide")
    
    # Inject custom CSS for consistent styling
    inject_custom_css()
    
    # Display navigation bar
    
    # Check if user is logged in and has 'coordinator' role
    if 'user' not in st.session_state or st.session_state['user']['role'] != 'coordinator':
        st.error("You need coordinator permissions to access this page.")
        st.switch_page("main.py")
        return
    
    # Get user details from session state
    user = st.session_state['user']
    
    # Display welcome message
    st.title(f"Coordinator Dashboard - Welcome, {user['first_name']}!")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Bus Management", "Route Management", "Trip Scheduling", "Driver Management"])
    
    with tab1:
        display_overview()
    
    with tab2:
        display_bus_management()
    
    with tab3:
        display_route_management()
    
    with tab4:
        display_trip_scheduling()
    
    with tab5:
        display_driver_management()
    
    # Display footer
    show_footer()

def display_overview():
    """Display key metrics and charts in the overview tab."""
    st.subheader("Dashboard Overview")
    
    # Fetch key metrics
    total_bookings = get_total_bookings()
    daily_revenue = get_daily_revenue(start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
    route_popularity = get_route_popularity()
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Bookings", total_bookings)
    with col2:
        if daily_revenue:
            st.metric("Revenue (Last 7 Days)", f"${sum(row['daily_revenue'] for row in daily_revenue):,.2f}")
        else:
            st.metric("Revenue (Last 7 Days)", "$0.00")
    with col3:
        upcoming_trips = len([trip for trip in get_all_trips() if trip['departure_datetime'] > datetime.now()])
        st.metric("Upcoming Trips", upcoming_trips)
    
    # Display charts
    st.subheader("Booking Trends")
    if daily_revenue:
        df_revenue = pd.DataFrame(daily_revenue)
        st.line_chart(df_revenue.set_index('booking_date')['daily_revenue'])
    else:
        st.info("No revenue data available for the last 7 days.")
    
    st.subheader("Route Popularity")
    if route_popularity:
        df_routes = pd.DataFrame(route_popularity)
        st.bar_chart(df_routes.set_index('origin')['trip_count'])
    else:
        st.info("No route popularity data available.")
    
    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Manage Buses"):
            st.switch_page("pages/CoordinatorDashboard.py#bus_management")
    with col2:
        if st.button("Manage Routes"):
            st.switch_page("pages/CoordinatorDashboard.py#route_management")
    with col3:
        if st.button("Schedule Trip"):
            st.switch_page("pages/CoordinatorDashboard.py#trip_scheduling")

def display_bus_management():
    """Display bus management interface with CRUD operations."""
    st.subheader("Bus Management")
    
    # Fetch all buses and drivers
    buses = get_all_buses()
    drivers = get_all_drivers()
    
    if not buses:
        st.info("No buses found. Add a new bus to get started.")
    else:
        # Display buses in a table
        df_buses = pd.DataFrame(buses)
        st.dataframe(df_buses[['bus_no', 'bus_type', 'capacity', 'driver_id']])
    
    # Add new bus form
    with st.expander("Add New Bus"):
        with st.form("add_bus_form"):
            bus_no = st.text_input("Bus Number")
            bus_type = st.selectbox("Bus Type", ["AC", "Non-AC", "Sleeper", "Deluxe"])
            capacity = st.number_input("Capacity", min_value=1, step=1)
            driver_options = {f"{d['first_name']} {d['last_name']} (ID: {d['driver_id']})": d['driver_id'] for d in drivers}
            driver_options["None"] = None
            selected_driver = st.selectbox("Select Driver (Optional)", options=list(driver_options.keys()), index=list(driver_options.keys()).index("None"))
            driver_id = driver_options[selected_driver]
            submit = st.form_submit_button("Add Bus")
            
            if submit:
                if not bus_no:
                    st.error("Bus number is required.")
                elif any(bus['bus_no'] == bus_no for bus in buses):
                    st.error("Bus number must be unique.")
                else:
                    success, bus_id = add_bus(bus_no, bus_type, capacity, driver_id)
                    if success:
                        st.success(f"Bus {bus_no} added successfully with ID {bus_id}.")
                        st.rerun()
                    else:
                        st.error("Failed to add bus.")
    
    # Edit or delete existing buses
    if buses:
        st.subheader("Edit or Delete Bus")
        selected_bus = st.selectbox("Select Bus to Edit/Delete", options=buses, format_func=lambda x: f"Bus {x['bus_no']}")
        
        with st.form("edit_bus_form"):
            new_bus_no = st.text_input("Bus Number", value=selected_bus['bus_no'])
            new_bus_type = st.selectbox("Bus Type", ["AC", "Non-AC", "Sleeper", "Deluxe"], index=["AC", "Non-AC", "Sleeper", "Deluxe"].index(selected_bus['bus_type']))
            new_capacity = st.number_input("Capacity", min_value=1, step=1, value=selected_bus['capacity'])
            driver_options = {f"{d['first_name']} {d['last_name']} (ID: {d['driver_id']})": d['driver_id'] for d in drivers}
            driver_options["None"] = None
            current_driver_key = next((k for k, v in driver_options.items() if v == selected_bus['driver_id']), "None")
            selected_driver = st.selectbox("Select Driver (Optional)", options=list(driver_options.keys()), index=list(driver_options.keys()).index(current_driver_key))
            new_driver_id = driver_options[selected_driver]
            update_submit = st.form_submit_button("Update Bus")
            delete_submit = st.form_submit_button("Delete Bus")
            
            if update_submit:
                if not new_bus_no:
                    st.error("Bus number is required.")
                elif new_bus_no != selected_bus['bus_no'] and any(bus['bus_no'] == new_bus_no for bus in buses):
                    st.error("Bus number must be unique.")
                else:
                    success = update_bus(selected_bus['bus_id'], new_bus_no, new_bus_type, new_capacity, new_driver_id)
                    if success:
                        st.success(f"Bus {new_bus_no} updated successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to update bus.")
            
            if delete_submit:
                if st.checkbox("Confirm deletion"):
                    success, message = delete_bus(selected_bus['bus_id'])
                    if success:
                        st.success(f"Bus {selected_bus['bus_no']} deleted successfully.")
                        st.rerun()
                    else:
                        st.error(message)

def display_route_management():
    """Display route management interface with map visualization and CRUD operations."""
    st.subheader("Route Management")
    
    # Fetch all routes
    routes = get_all_routes()
    
    # Dynamically center the map based on existing routes
    map_center = [39.8283, -98.5795]  # Default USA center
    if routes:
        coords = [route.get('origin_coords', map_center) for route in routes if route.get('origin_coords')] + \
                [route.get('dest_coords', map_center) for route in routes if route.get('dest_coords')]
        if coords:
            map_center = [sum(x[0] for x in coords) / len(coords), sum(x[1] for x in coords) / len(coords)]
    
    # Display map of existing routes
    if routes:
        st.write("### Route Map")
        m = folium.Map(location=map_center, zoom_start=4)
        for route in routes:
            origin_coords = route.get('origin_coords')
            dest_coords = route.get('dest_coords')
            if origin_coords and dest_coords:
                folium.PolyLine([origin_coords, dest_coords], color="blue", weight=2.5, opacity=1).add_to(m)
                folium.Marker(origin_coords, popup=f"Origin: {route['origin']}").add_to(m)
                folium.Marker(dest_coords, popup=f"Destination: {route['destination']}").add_to(m)
        folium_static(m)
    else:
        st.info("No routes found. Add a new route to get started.")
    
    # Display routes in a table if they exist
    if routes:
        df_routes = pd.DataFrame(routes)
        st.dataframe(df_routes[['origin', 'destination', 'distance', 'base_fare', 'route_desc']])
    
    # Add new route form with coordinate calculation and preview
    with st.expander("Add New Route"):
        with st.form("add_route_form"):
            origin = st.text_input("Origin")
            destination = st.text_input("Destination")
            distance = st.number_input("Distance (km)", min_value=1.0, step=0.1)
            base_fare = st.number_input("Base Fare ($)", min_value=0.0, step=0.01)
            route_desc = st.text_area("Description (Optional)")
            submit = st.form_submit_button("Add Route")
            
            # Preview new route
            if origin and destination:
                origin_coords = get_coords_from_place(origin)
                dest_coords = get_coords_from_place(destination)
                if origin_coords and dest_coords:
                    preview_m = folium.Map(location=origin_coords, zoom_start=6)
                    folium.PolyLine([origin_coords, dest_coords], color="red", weight=2.5, opacity=1).add_to(preview_m)
                    folium.Marker(origin_coords, popup=f"Origin: {origin}").add_to(preview_m)
                    folium.Marker(dest_coords, popup=f"Destination: {destination}").add_to(preview_m)
                    st.write("### Route Preview")
                    folium_static(preview_m)
                else:
                    st.warning("Could not generate preview due to invalid coordinates.")
            
            if submit:
                if not origin or not destination:
                    st.error("Origin and destination are required.")
                elif origin == destination:
                    st.error("Origin and destination cannot be the same.")
                else:
                    origin_coords = get_coords_from_place(origin)
                    dest_coords = get_coords_from_place(destination)
                    if not origin_coords or not dest_coords:
                        st.error("Could not find coordinates for the provided origin or destination.")
                    else:
                        origin = str(origin).strip()
                        destination = str(destination).strip()
                        success, route_id = add_route(
                            origin, destination, distance, base_fare,
                            origin_coords[0], origin_coords[1], dest_coords[0], dest_coords[1], route_desc if route_desc else None
                        )
                        if success:
                            st.success(f"Route from {origin} to {destination} added successfully with ID {route_id}.")
                            st.rerun()
                        else:
                            st.error("Failed to add route.")
    
    # Edit or delete existing routes with coordinate updates
    if routes:
        st.subheader("Edit or Delete Route")
        selected_route = st.selectbox("Select Route to Edit/Delete", options=routes, format_func=lambda x: f"{x['origin']} to {x['destination']}")
        
        with st.form("edit_route_form"):
            new_origin = st.text_input("Origin", value=selected_route['origin'])
            new_destination = st.text_input("Destination", value=selected_route['destination'])
            new_distance = st.number_input("Distance (km)", min_value=1.0, step=0.1, value=float(selected_route['distance']))
            new_base_fare = st.number_input("Base Fare ($)", min_value=0.0, step=0.01, value=float(selected_route['base_fare']))
            new_route_desc = st.text_area("Description (Optional)", value=selected_route['route_desc'] if selected_route['route_desc'] else "")
            
            # Preview updated route
            if new_origin != selected_route['origin'] or new_destination != selected_route['destination']:
                new_origin_coords = get_coords_from_place(new_origin)
                new_dest_coords = get_coords_from_place(new_destination)
                if new_origin_coords and new_dest_coords:
                    preview_m = folium.Map(location=new_origin_coords, zoom_start=6)
                    folium.PolyLine([new_origin_coords, new_dest_coords], color="red", weight=2.5, opacity=1).add_to(preview_m)
                    folium.Marker(new_origin_coords, popup=f"New Origin: {new_origin}").add_to(preview_m)
                    folium.Marker(new_dest_coords, popup=f"New Destination: {new_destination}").add_to(preview_m)
                    st.write("### Updated Route Preview")
                    folium_static(preview_m)
                else:
                    st.warning("Could not generate preview due to invalid coordinates.")
            
            update_submit = st.form_submit_button("Update Route")
            delete_submit = st.form_submit_button("Delete Route")
            
            if update_submit:
                if not new_origin or not new_destination:
                    st.error("Origin and destination are required.")
                elif new_origin == new_destination:
                    st.error("Origin and destination cannot be the same.")
                else:
                    new_origin_coords = get_coords_from_place(new_origin)
                    new_dest_coords = get_coords_from_place(new_destination)
                    if not new_origin_coords or not new_dest_coords:
                        st.error("Could not find coordinates for the new origin or destination.")
                    else:
                        new_origin = str(new_origin).strip()
                        new_destination = str(new_destination).strip()
                        success = update_route(
                            selected_route['route_id'], new_origin, new_destination,
                            new_distance, new_base_fare, new_route_desc if new_route_desc else None,
                            new_origin_coords[0], new_origin_coords[1], new_dest_coords[0], new_dest_coords[1]
                        )
                        if success:
                            st.success(f"Route from {new_origin} to {new_destination} updated successfully.")
                            st.rerun()
                        else:
                            st.error("Failed to update route.")
            
            if delete_submit:
                if st.checkbox("Confirm deletion"):
                    success, message = delete_route(selected_route['route_id'])
                    if success:
                        st.success(f"Route from {selected_route['origin']} to {selected_route['destination']} deleted successfully.")
                        st.rerun()
                    else:
                        st.error(message)

def display_trip_scheduling():
    """Display trip scheduling interface with add functionality."""
    st.subheader("Trip Scheduling")
    
    # Fetch all trips (upcoming only)
    trips = get_all_trips(include_past=False)
    
    if not trips:
        st.info("No upcoming trips found. Schedule a new trip to get started.")
    else:
        # Display trips in a table
        df_trips = pd.DataFrame(trips)
        st.dataframe(df_trips[['bus_no', 'origin', 'destination', 'departure_datetime', 'arrival_datetime', 'seats_available', 'status']])
    
    # Schedule new trip form
    with st.expander("Schedule New Trip"):
        with st.form("schedule_trip_form"):
            # Fetch buses and routes for selection
            buses = get_all_buses()
            routes = get_all_routes()
            
            if not buses or not routes:
                st.error("Please add buses and routes before scheduling a trip.")
                st.form_submit_button("Schedule Trip", disabled=True)
            else:
                bus_options = {f"{bus['bus_no']} ({bus['bus_type']})": bus['bus_id'] for bus in buses}
                route_options = {f"{route['origin']} to {route['destination']}": route['route_id'] for route in routes}
                
                selected_bus = st.selectbox("Select Bus", options=list(bus_options.keys()))
                selected_route = st.selectbox("Select Route", options=list(route_options.keys()))
                departure_date = st.date_input("Select Departure Date")
                departure_time = st.time_input("Select Departure Time")
                departure_datetime = datetime.combine(departure_date, departure_time)
                arrival_date = st.date_input("Select Arrival Date")
                arrival_time = st.time_input("Select Arrival Time")
                arrival_datetime = datetime.combine(arrival_date, arrival_time)
                seats_available = st.number_input("Initial Seats Available", min_value=1, step=1)
                
                submit = st.form_submit_button("Schedule Trip")
                
                if submit:
                    if departure_datetime >= arrival_datetime:
                        st.error("Arrival time must be after departure time.")
                    else:
                        bus_id = bus_options[selected_bus]
                        route_id = route_options[selected_route]
                        success, trip_id = add_trip(
                            bus_id=bus_id,
                            route_id=route_id,
                            departure_datetime=departure_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                            arrival_datetime=arrival_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                            seats_available=seats_available
                        )
                        if success:
                            st.success(f"Trip scheduled successfully with ID {trip_id}.")
                            st.rerun()
                        else:
                            st.error("Failed to schedule trip.")

def display_driver_management():
    """Display driver management interface with CRUD operations."""
    st.subheader("Driver Management")
    
    # Fetch all drivers
    drivers = get_all_drivers()
    
    if not drivers:
        st.info("No drivers found. Add a new driver to get started.")
    else:
        # Display drivers in a table
        df_drivers = pd.DataFrame(drivers)
        st.dataframe(df_drivers[['driver_id', 'first_name', 'last_name', 'contact_no', 'license_no', 'hired_date']])
    
    # Add new driver form
    with st.expander("Add New Driver"):
        with st.form("add_driver_form"):
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            contact_no = st.text_input("Contact Number")
            license_no = st.text_input("License Number")
            hired_date = st.date_input("Hired Date", value=datetime.now())
            submit = st.form_submit_button("Add Driver")
            
            if submit:
                if not first_name or not last_name:
                    st.error("First name and last name are required.")
                else:
                    success, driver_id = add_driver(first_name, last_name, contact_no, license_no, hired_date.strftime("%Y-%m-%d"))
                    if success:
                        st.success(f"Driver {first_name} {last_name} added successfully with ID {driver_id}.")
                        st.rerun()
                    else:
                        st.error("Failed to add driver.")
    
    # Edit or delete existing drivers
    if drivers:
        st.subheader("Edit or Delete Driver")
        selected_driver = st.selectbox("Select Driver to Edit/Delete", options=drivers, format_func=lambda x: f"{x['first_name']} {x['last_name']} (ID: {x['driver_id']})")
        
        with st.form("edit_driver_form"):
            new_first_name = st.text_input("First Name", value=selected_driver['first_name'])
            new_last_name = st.text_input("Last Name", value=selected_driver['last_name'])
            new_contact_no = st.text_input("Contact Number", value=selected_driver['contact_no'] if selected_driver['contact_no'] else "")
            new_license_no = st.text_input("License Number", value=selected_driver['license_no'] if selected_driver['license_no'] else "")
            new_hired_date = st.date_input("Hired Date", value=selected_driver['hired_date'].date() if selected_driver['hired_date'] else datetime.now().date())
            update_submit = st.form_submit_button("Update Driver")
            delete_submit = st.form_submit_button("Delete Driver")
            
            if update_submit:
                if not new_first_name or not new_last_name:
                    st.error("First name and last name are required.")
                else:
                    success = update_driver(selected_driver['driver_id'], new_first_name, new_last_name, new_contact_no, new_license_no, new_hired_date.strftime("%Y-%m-%d"))
                    if success:
                        st.success(f"Driver {new_first_name} {new_last_name} updated successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to update driver.")
            
            if delete_submit:
                if st.checkbox("Confirm deletion"):
                    success, message = delete_driver(selected_driver['driver_id'])
                    if success:
                        st.success(f"Driver {selected_driver['first_name']} {selected_driver['last_name']} deleted successfully.")
                        st.rerun()
                    else:
                        st.error(message)

if __name__ == "__main__":
    main()