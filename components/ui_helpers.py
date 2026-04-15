import streamlit as st


# ─────────────────────────────────────────────
# GLOBAL THEME CSS (SAFE + SCOPED)
# ─────────────────────────────────────────────
def inject_theme():
    """Inject CSS only once (prevents UI breaking)"""

    if st.session_state.get("theme_loaded"):
        return

    st.session_state.theme_loaded = True

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&family=DM+Mono:wght@400;500&display=swap');

    :root {
        --teal:        #3BB0A7;
        --dark-teal:   #0F4F4F;
        --mint:        #C2DCCF;
        --soft-grey:   #F6F6F2;
        --text-dark:   #1A2E2E;
    }

    /* ── BASE RESET (FIX FADED UI) ───────────────── */
    html, body, .stApp {
        opacity: 1 !important;
        filter: none !important;
        background-color: var(--soft-grey);
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: var(--text-dark);
    }

    /* ── SIDEBAR (SCOPED ONLY) ───────────────────── */
    [data-testid="stSidebar"] {
        background: var(--dark-teal);
        color: var(--mint);
    }

    [data-testid="stSidebar"] a {
        color: var(--mint);
        font-weight: 600;
    }

    [data-testid="stSidebar"] a:hover {
        color: var(--teal);
    }

    /* ── BUTTONS ─────────────────────────────────── */
    .stButton > button {
        background: var(--teal);
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
    }

    .stButton > button:hover {
        background: var(--dark-teal);
    }

    /* ── INPUTS ─────────────────────────────────── */
    input, textarea {
        border-radius: 6px !important;
    }

    /* ── HEADERS ────────────────────────────────── */
    h1, h2, h3 {
        color: var(--dark-teal);
        font-weight: 800;
    }

    /* ── CARDS ─────────────────────────────────── */
    .custom-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }

    /* ── FIX STREAMLIT BLOCK ───────────────────── */
    .block-container {
        padding-top: 2rem;
    }

    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────
def page_header(title: str, subtitle: str = "", icon: str = ""):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0F4F4F, #3BB0A7);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    ">
        <h2 style="margin:0;">{icon} {title}</h2>
        <p style="margin:0; opacity:0.9;">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TRIP CARD
# ─────────────────────────────────────────────
def trip_card(trip: dict, on_book_key: str):
    route = trip.get("route", {})
    bus   = trip.get("bus", {})

    st.markdown(f"""
    <div class="custom-card">
        <b>{route.get('source')} → {route.get('destination')}</b><br>
        🕐 {trip['departure_datetime']} → {trip['arrival_datetime']}<br>
        🪑 Seats: {trip['seats_available']}<br>
        🚌 {bus.get('bus_type')}<br>
        💰 ₹{trip.get('fare', 0)}
    </div>
    """, unsafe_allow_html=True)

    return st.button("Book Now", key=on_book_key)


# ─────────────────────────────────────────────
# BOOKING CARD
# ─────────────────────────────────────────────
def booking_card(booking: dict, on_cancel_key=None):

    st.markdown(f"""
    <div class="custom-card">
        <b>{booking.get('route_source')} → {booking.get('route_destination')}</b><br>
        📅 {booking.get('departure')}<br>
        💺 Seat: {booking.get('seat_no')}<br>
        💰 ₹{booking.get('fare')}<br>
        Status: <b>{booking.get('booking_status')}</b>
    </div>
    """, unsafe_allow_html=True)

    if booking.get("booking_status") == "confirmed" and on_cancel_key:
        return st.button("Cancel Booking", key=on_cancel_key)

    return False


# ─────────────────────────────────────────────
# SECTION TITLE
# ─────────────────────────────────────────────
def section_title(text: str, icon: str = ""):
    st.markdown(f"### {icon} {text}")