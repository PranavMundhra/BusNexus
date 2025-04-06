import streamlit as st
from datetime import datetime, timedelta

def format_datetime(dt):
    """Format datetime for display"""
    if isinstance(dt, str):
        dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return dt.strftime("%b %d, %Y %I:%M %p")

def calculate_trip_duration(departure, arrival):
    """Calculate and format trip duration"""
    if isinstance(departure, str):
        departure = datetime.strptime(departure, "%Y-%m-%d %H:%M:%S")
    if isinstance(arrival, str):
        arrival = datetime.strptime(arrival, "%Y-%m-%d %H:%M:%S")
    
    duration = arrival - departure
    hours = duration.seconds // 3600
    minutes = (duration.seconds % 3600) // 60
    
    if duration.days > 0:
        return f"{duration.days}d {hours}h {minutes}m"
    else:
        return f"{hours}h {minutes}m"

def inject_custom_css():
    """Inject custom CSS for styling"""
    st.markdown("""
    <style>
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #2D2D2D;
        margin-bottom: 1rem;
        border: 1px solid #444;
        transition: transform 0.3s ease;
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    .hero {
        padding: 3rem 1rem;
        text-align: center;
        border-radius: 10px;
        background-color: #1c1c1c;
        margin-bottom: 2rem;
        background-image: linear-gradient(135deg, #1c1c1c, #00adb5);
        color: white;
    }
    .nav-links {
        display: flex;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .nav-link {
        color: #00adb5;
        text-decoration: none;
        font-weight: bold;
        transition: color 0.2s ease;
    }
    .nav-link:hover {
        color: #00ffe1;
    }
    .feature-card {
        background-color: #2D2D2D;
        padding: 1.5rem;
        border-radius: 8px;
        height: 100%;
        border: 1px solid #444;
    }
    .feature-icon {
        font-size: 2rem;
        color: #00adb5;
        margin-bottom: 1rem;
    }
    .form-container {
        background-color: #2D2D2D;
        padding: 2rem;
        border-radius: 10px;
        max-width: 500px;
        margin: 0 auto;
        border: 1px solid #444;
    }
    .seat {
        width: 3rem;
        height: 3rem;
        margin: 0.3rem;
        display: inline-flex;
        justify-content: center;
        align-items: center;
        border-radius: 5px;
        cursor: pointer;
        font-weight: bold;
        background-color: #404040;
        color: white;
        transition: all 0.2s ease;
    }
    .seat.available {
        background-color: #2D2D2D;
        border: 2px solid #00adb5;
    }
    .seat.selected {
        background-color: #00adb5;
        color: white;
    }
    .seat.booked {
        background-color: #666;
        cursor: not-allowed;
    }
    .stat-card {
        background-color: #2D2D2D;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #444;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: #00adb5;
    }
    .stat-label {
        color: #ccc;
        font-size: 0.9rem;
    }
    .styled-table {
        width: 100%;
        border-collapse: collapse;
    }
    .styled-table th {
        background-color: #222;
        padding: 0.75rem;
        text-align: left;
        color: #00adb5;
        border-bottom: 2px solid #444;
    }
    .styled-table td {
        padding: 0.75rem;
        border-bottom: 1px solid #444;
    }
    .styled-table tr:hover {
        background-color: #333;
    }
    .styled-button {
        background-color: #00adb5;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
        cursor: pointer;
        transition: background-color 0.2s ease;
    }
    .styled-button:hover {
        background-color: #00c2c7;
    }
    .center-text {
        text-align: center;
    }
    .footer {
        margin-top: 3rem;
        padding-top: 1rem;
        text-align: center;
        border-top: 1px solid #444;
        color: #888;
    }
    </style>
    """, unsafe_allow_html=True)

def show_navigation():
    """Display navigation bar"""
    if 'user' in st.session_state:
        user = st.session_state['user']
        role = user.get('role')

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown("""
            <div class="nav-links">
                <a href="/" target="_self" class="nav-link">Home</a>
                <a href="/BookingHistory" target="_self" class="nav-link">My Bookings</a>
                <a href="/About" target="_self" class="nav-link">About</a>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="text-align: right;">
                Welcome, {user.get('first_name')}! 
                <a href="#" id="logout" class="nav-link">Logout</a>
            </div>
            """, unsafe_allow_html=True)

            # Escape script properly using triple quotes
            st.markdown("""
            <script>
            const logoutButton = window.parent.document.getElementById("logout");
            if (logoutButton) {
                logoutButton.addEventListener("click", function(e) {
                    e.preventDefault();
                    window.parent.postMessage({
                        type: "streamlit:setComponentValue",
                        value: "logout"
                    }, "*");
                });
            }
            </script>
            """, unsafe_allow_html=True)

        if role == 'coordinator':
            st.markdown("""
            <div class="nav-links">
                <a href="/CoordinatorDashboard" target="_self" class="nav-link">Dashboard</a>
                <a href="/BusManagement" target="_self" class="nav-link">Buses</a>
                <a href="/RouteManagement" target="_self" class="nav-link">Routes</a>
                <a href="/TripScheduling" target="_self" class="nav-link">Trips</a>
                <a href="/Reports" target="_self" class="nav-link">Reports</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="nav-links">
            <a href="/" target="_self" class="nav-link">Home</a>
            <a href="/Login" target="_self" class="nav-link">Login</a>
            <a href="/Register" target="_self" class="nav-link">Register</a>
            <a href="/About" target="_self" class="nav-link">About</a>
        </div>
        """, unsafe_allow_html=True)

def show_footer():
    """Display footer"""
    st.markdown("""
    <div class="footer">
        <p>© 2025 BusNexus. All rights reserved.</p>
        <p>Contact: support@busnexus.com | Phone: +1-555-123-4567</p>
    </div>
    """, unsafe_allow_html=True)
