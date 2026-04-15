"""
BusNexus — Streamlit Frontend (v2)
Run: streamlit run busnexus_app.py
"""

import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
import plotly.express as px
from datetime import date, datetime, time, timedelta
import json

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="BusNexus",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════
# GLOBAL CSS
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

.main .block-container { padding-top: 1.4rem; max-width: 1200px; }

.bn-header {
    background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%);
    padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.5rem;
    box-shadow: 0 8px 32px rgba(14,165,233,0.2);
}
.bn-header h1 { color:#fff; margin:0; font-size:1.75rem; font-weight:800; letter-spacing:-.02em; }
.bn-header p  { color:rgba(255,255,255,.8); margin:.25rem 0 0; font-size:.9rem; }

.stat-card {
    background:#fff; border:1px solid #e2e8f0; border-radius:12px;
    padding:1.1rem 1.2rem; box-shadow:0 1px 6px rgba(0,0,0,.05); text-align:center;
}
.stat-card .s-label { color:#64748b; font-size:.7rem; font-weight:700;
    text-transform:uppercase; letter-spacing:.08em; }
.stat-card .s-value { color:#0f172a; font-size:1.9rem; font-weight:800;
    margin-top:3px; line-height:1.1; }
.stat-card .s-sub { font-size:.76rem; color:#94a3b8; margin-top:2px; }

.card {
    background:#fff; border:1px solid #e2e8f0; border-radius:14px;
    padding:1.2rem 1.4rem; margin-bottom:.8rem;
    box-shadow:0 1px 6px rgba(0,0,0,.04);
    transition:box-shadow .18s, transform .18s;
}
.card:hover { box-shadow:0 6px 24px rgba(0,0,0,.09); transform:translateY(-1px); }
.card-title { font-size:1.02rem; font-weight:700; color:#0f172a; }
.card-meta  { color:#64748b; font-size:.82rem; margin-top:5px; line-height:1.75; }

.badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:.7rem; font-weight:700; }
.badge-green  { background:#dcfce7; color:#15803d; }
.badge-orange { background:#fff7ed; color:#c2410c; }
.badge-blue   { background:#eff6ff; color:#1d4ed8; }
.badge-red    { background:#fef2f2; color:#b91c1c; }
.badge-gray   { background:#f1f5f9; color:#475569; }
.badge-purple { background:#f5f3ff; color:#6d28d9; }
.badge-teal   { background:#f0fdfa; color:#0f766e; }

.sec-title {
    font-size:1rem; font-weight:700; color:#0f172a;
    border-left:4px solid #0ea5e9; padding-left:.65rem;
    margin:1.3rem 0 .8rem;
}

.info-box    { background:#f0f9ff; border:1px solid #bae6fd; border-radius:10px;
               padding:.85rem 1.1rem; color:#0369a1; font-size:.86rem; margin:.6rem 0; }
.warn-box    { background:#fffbeb; border:1px solid #fde68a; border-radius:10px;
               padding:.85rem 1.1rem; color:#92400e; font-size:.86rem; margin:.6rem 0; }
.success-box { background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px;
               padding:.85rem 1.1rem; color:#166534; font-size:.86rem; margin:.6rem 0; }

.seat-grid { display:flex; flex-wrap:wrap; gap:7px; max-width:400px; }
.seat { width:40px; height:40px; border-radius:7px;
    display:flex; align-items:center; justify-content:center;
    font-size:.7rem; font-weight:700; }
.seat-avail  { background:#dcfce7; color:#15803d; border:2px solid #86efac; }
.seat-booked { background:#fee2e2; color:#b91c1c; border:2px solid #fca5a5; }

.tl  { display:flex; gap:11px; margin-bottom:11px; align-items:flex-start; }
.tl-dot  { width:11px; height:11px; border-radius:50%; background:#0ea5e9;
    margin-top:5px; flex-shrink:0; }
.tl-body { font-size:.84rem; line-height:1.55; }
.tl-body b { color:#0f172a; }
.tl-body span { color:#64748b; }

.empty-state { text-align:center; padding:2.5rem 1rem; color:#94a3b8; }
.empty-state .icon { font-size:2.8rem; margin-bottom:.4rem; }

hr.div { border:none; border-top:1px solid #e2e8f0; margin:1.1rem 0; }

.stButton > button { border-radius:8px; font-weight:600; transition:all .18s; }
.stButton > button:hover { transform:translateY(-1px); box-shadow:0 4px 14px rgba(0,0,0,.12); }

[data-testid="stDataFrame"] { border-radius:10px; overflow:hidden; border:1px solid #e2e8f0; }

[data-baseweb="tab-list"] { background:#f1f5f9; border-radius:10px; padding:3px; }
[data-baseweb="tab"] { border-radius:8px !important; font-weight:600 !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ══════════════════════════════════════════════════════════════
def get_db():
    try:
        return psycopg2.connect(
            host     = st.secrets.get("DB_HOST",     "localhost"),
            dbname   = st.secrets.get("DB_NAME",     "busnexus"),
            user     = st.secrets.get("DB_USER",     "postgres"),
            password = st.secrets.get("DB_PASSWORD", ""),
            port     = int(st.secrets.get("DB_PORT",  5432)),
        )
    except Exception as e:
        st.error(f"❌ Database connection failed — check `.streamlit/secrets.toml`\n\n`{e}`")
        st.stop()

def run_query(sql, params=None):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def run_write(sql, params=None):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def run_write_returning(sql, params=None):
    conn = get_db()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.commit()
        return row
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def run_proc(sql, params=None):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def add_driver(name, contact):
    emp = run_write_returning(
        "INSERT INTO employees(name, contact_no) VALUES(%s,%s) RETURNING emp_id",
        (name, contact)
    )
    
    run_write(
        "INSERT INTO drivers(emp_id) VALUES(%s)",
        (emp["emp_id"],)
    )

# ══════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════
_DEFAULTS = dict(
    logged_in=False, user_id=None, user_name="",
    user_role="", page="home", selected_trip=None, toast=None
)
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════
# UI HELPERS
# ══════════════════════════════════════════════════════════════
def badge(text, color="blue"):
    return f'<span class="badge badge-{color}">{text}</span>'

def status_badge(status):
    cmap = {"confirmed":"green","cancelled":"red","waitlisted":"orange",
            "scheduled":"blue","completed":"teal","issued":"green","modified":"purple"}
    return badge(status.capitalize(), cmap.get(status.lower(), "gray"))

def section(title):
    st.markdown(f'<div class="sec-title">{title}</div>', unsafe_allow_html=True)

def divider():
    st.markdown('<hr class="div">', unsafe_allow_html=True)

def stat_card(label, value, sub="", color="#0ea5e9"):
    st.markdown(f"""
    <div class="stat-card">
        <div class="s-label">{label}</div>
        <div class="s-value" style="color:{color}">{value}</div>
        <div class="s-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def empty_state(icon, msg):
    st.markdown(f'<div class="empty-state"><div class="icon">{icon}</div><p>{msg}</p></div>',
                unsafe_allow_html=True)

def show_toast():
    if st.session_state.toast:
        msg, kind = st.session_state.toast
        st.session_state.toast = None
        fn = {"success": st.success, "error": st.error,
              "warning": st.warning}.get(kind, st.info)
        fn(msg)

def nav_to(page):
    st.session_state.page = page
    st.rerun()

# ══════════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════════
def page_login():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("""
        <div style='text-align:center;padding:2rem 0 1.2rem'>
            <div style='font-size:3.8rem'>🚌</div>
            <h1 style='font-weight:800;color:#0f172a;margin:.2rem 0;font-size:2.1rem'>BusNexus</h1>
            <p style='color:#64748b;margin:0;font-size:.93rem'>Smart Bus Booking Platform</p>
        </div>""", unsafe_allow_html=True)

        tab_in, tab_reg = st.tabs(["🔑 Sign In", "✨ Create Account"])

        with tab_in:
            st.markdown("<br>", unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="you@example.com", key="li_em")
            pwd   = st.text_input("Password", type="password", placeholder="••••••••", key="li_pw")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Sign In →", use_container_width=True, type="primary"):
                _do_login(email.strip(), pwd)
            st.markdown("""
            <div class="info-box" style="margin-top:.8rem">
                🎯 <b>Demo accounts</b> (any password):<br>
                <code>anushka@gmail.com</code> · <code>rahul@gmail.com</code> ·
                <code>priya@gmail.com</code><br>
                <code>coord@gmail.com</code>
                <span style="color:#0369a1;font-weight:600"> — Coordinator</span>
            </div>""", unsafe_allow_html=True)

        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            rn = st.text_input("Full Name",  key="rn")
            re = st.text_input("Email",      key="re")
            rp = st.text_input("Phone",      key="rp")
            rr = st.selectbox("Register as", ["passenger","coordinator"], key="rr")
            rw = st.text_input("Password",   type="password", key="rw")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Create Account →", use_container_width=True, type="primary"):
                _do_register(rn, re, rp, rr, rw)

def _do_login(email, pwd):
    if not email or not pwd:
        st.warning("Enter email and password."); return
    try:
        rows = run_query(
            """SELECT u.user_id, u.name, u.role::TEXT role
               FROM users u JOIN accounts a ON u.user_id=a.user_id
               WHERE a.email=%s AND a.password_hash=%s""", (email, pwd))
        if not rows:   # demo: accept any password
            rows = run_query(
                """SELECT u.user_id, u.name, u.role::TEXT role
                   FROM users u JOIN accounts a ON u.user_id=a.user_id
                   WHERE a.email=%s""", (email,))
        if rows:
            u = rows[0]
            st.session_state.update(
                logged_in=True, user_id=u["user_id"],
                user_name=u["name"], user_role=u["role"], page="dashboard")
            st.rerun()
        else:
            st.error("No account found for that email.")
    except Exception as e:
        st.error(f"Login error: {e}")

def _do_register(name, email, phone, role, pwd):
    if not all([name, email, pwd]):
        st.warning("Name, email and password are required."); return
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users(name,email,contact_no,role) VALUES(%s,%s,%s,%s) RETURNING user_id",
            (name, email, phone or None, role))
        uid = cur.fetchone()[0]
        cur.execute(f"INSERT INTO {'passengers' if role=='passenger' else 'coordinators'}(user_id) VALUES(%s)", (uid,))
        cur.execute("INSERT INTO accounts(user_id,username,email,password_hash) VALUES(%s,%s,%s,%s)",
                    (uid, email.split("@")[0], email, pwd))
        conn.commit(); cur.close()
        st.success("Account created! Please sign in.")
    except psycopg2.errors.UniqueViolation:
        conn.rollback(); st.error("Email already registered.")
    except Exception as e:
        conn.rollback(); st.error(f"Registration failed: {e}")
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
def sidebar():
    with st.sidebar:
        role   = st.session_state.user_role
        rc     = "#38bdf8" if role == "passenger" else "#a78bfa"
        rlabel = "🧍 PASSENGER" if role == "passenger" else "🎯 COORDINATOR"
        rbg    = "#1e3a5f" if role == "passenger" else "#2d1b69"

        st.markdown(f"""
        <div style='padding:.7rem 0 .3rem'>
            <div style='font-size:1.45rem;font-weight:800;color:#f8fafc;letter-spacing:-.02em'>
                🚌 BusNexus
            </div>
            <div style='margin-top:.4rem;font-size:.8rem;color:#94a3b8'>
                Signed in as<br>
                <b style='color:#f1f5f9;font-size:.88rem'>{st.session_state.user_name}</b>
            </div>
            <div style='margin-top:.35rem'>
                <span style='background:{rbg};color:{rc};padding:2px 9px;
                    border-radius:999px;font-size:.68rem;font-weight:700'>{rlabel}</span>
            </div>
        </div>
        <hr style='border-color:#334155;margin:.75rem 0'>
        """, unsafe_allow_html=True)

        if role == "passenger":
            nav = {"🏠 Dashboard":"dashboard","🔍 Browse Trips":"browse",
                   "🎫 My Bookings":"bookings","🧾 My Tickets":"tickets",
                   "💳 Payments":"payments"}
        else:
            nav = {"📊 Analytics":"analytics","🗓️ Schedule Trip":"schedule_trip",
                   "🚌 Fleet & Trips":"fleet","🗂️ All Bookings":"all_bookings",
                   "📋 Ticket Registry":"ticket_registry","👥 Users":"users", "👤 Drivers": "drivers"}

        cur = st.session_state.page
        for label, key in nav.items():
            active = cur == key or (key == "fleet" and cur == "manage_trip")
            if st.button(label, use_container_width=True,
                         type="primary" if active else "secondary", key=f"nav_{key}"):
                nav_to(key)

        st.markdown("<br>", unsafe_allow_html=True)
        divider()
        if st.button("🚪 Sign Out", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ══════════════════════════════════════════════════════════════
# PASSENGER — DASHBOARD
# ══════════════════════════════════════════════════════════════
def page_passenger_dashboard():
    uid = st.session_state.user_id
    show_toast()

    st.markdown(f"""
    <div class="bn-header">
        <h1>👋 Welcome back, {st.session_state.user_name}!</h1>
        <p>Your travel dashboard — upcoming trips, bookings and recent activity.</p>
    </div>""", unsafe_allow_html=True)

    try:
        total    = run_query("SELECT COUNT(*) n FROM bookings WHERE user_id=%s", (uid,))[0]["n"]
        active   = run_query("SELECT COUNT(*) n FROM bookings WHERE user_id=%s AND booking_status='confirmed'", (uid,))[0]["n"]
        tix      = run_query("SELECT COUNT(*) n FROM tickets t JOIN bookings b ON t.booking_id=b.booking_id WHERE b.user_id=%s", (uid,))[0]["n"]
        upcoming = run_query("SELECT COUNT(*) n FROM bookings b JOIN trips t ON b.trip_id=t.trip_id WHERE b.user_id=%s AND b.booking_status='confirmed' AND t.departure_datetime>NOW()", (uid,))[0]["n"]
    except: total=active=tix=upcoming=0

    c1,c2,c3,c4 = st.columns(4)
    with c1: stat_card("Total Bookings",  total,    color="#0ea5e9")
    with c2: stat_card("Confirmed",       active,   color="#22c55e")
    with c3: stat_card("Tickets Issued",  tix,      color="#8b5cf6")
    with c4: stat_card("Upcoming Trips",  upcoming, color="#f59e0b")

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([3, 2])

    with left:
        section("🗓️ Upcoming Confirmed Trips")
        try:
            rows = run_query("""
                SELECT r.source, r.destination, t.departure_datetime,
                       b.seat_no, bs.stop_name boarding, ds.stop_name dropping
                FROM bookings b
                JOIN trips  t  ON b.trip_id=t.trip_id
                JOIN routes r  ON t.route_id=r.route_id
                JOIN stops  bs ON b.boarding_stop=bs.stop_id
                JOIN stops  ds ON b.dropping_stop=ds.stop_id
                WHERE b.user_id=%s AND b.booking_status='confirmed'
                  AND t.departure_datetime>NOW()
                ORDER BY t.departure_datetime LIMIT 4""", (uid,))
            if rows:
                for r in rows:
                    dep = r["departure_datetime"].strftime("%a, %d %b %Y · %I:%M %p")
                    st.markdown(f"""
                    <div class="card">
                        <div class="card-title">🚌 {r['source']} → {r['destination']}</div>
                        <div class="card-meta">
                            📅 {dep}<br>
                            🪑 Seat {r['seat_no']} · 🛫 {r['boarding']} → 🛬 {r['dropping']}
                        </div>
                    </div>""", unsafe_allow_html=True)
            else:
                empty_state("🗺️", "No upcoming trips — browse and book one!")
                if st.button("🔍 Browse Trips", type="primary"):
                    nav_to("browse")
        except Exception as e:
            st.error(f"Error: {e}")

    with right:
        section("⚡ Quick Actions")
        if st.button("🔍 Browse & Book a Trip", use_container_width=True, type="primary"):
            nav_to("browse")
        if st.button("🎫 View My Bookings",     use_container_width=True): nav_to("bookings")
        if st.button("🧾 View My Tickets",      use_container_width=True): nav_to("tickets")
        if st.button("💳 Payment History",      use_container_width=True): nav_to("payments")

        section("📜 Recent Activity")
        try:
            hist = run_query("""
                SELECT th.status, th.changed_at, r.source, r.destination
                FROM ticket_history th
                JOIN tickets  tk ON th.ticket_no=tk.ticket_no
                JOIN bookings b  ON tk.booking_id=b.booking_id
                JOIN trips    t  ON b.trip_id=t.trip_id
                JOIN routes   r  ON t.route_id=r.route_id
                WHERE b.user_id=%s
                ORDER BY th.changed_at DESC LIMIT 6""", (uid,))
            if hist:
                for h in hist:
                    icon = {"issued":"🎫","cancelled":"❌","modified":"✏️"}.get(h["status"],"📝")
                    st.markdown(f"""
                    <div class="tl"><div class="tl-dot"></div>
                    <div class="tl-body"><b>{icon} {h['status'].capitalize()}</b>
                    — {h['source']} → {h['destination']}<br>
                    <span>{h['changed_at'].strftime('%d %b, %I:%M %p')}</span>
                    </div></div>""", unsafe_allow_html=True)
            else:
                st.caption("No activity yet.")
        except Exception as e:
            st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════
# PASSENGER — BROWSE
# ══════════════════════════════════════════════════════════════
def page_browse_trips():
    show_toast()
    st.markdown("""
    <div class="bn-header">
        <h1>🔍 Browse Trips</h1>
        <p>Find available journeys and reserve your seat</p>
    </div>""", unsafe_allow_html=True)

    with st.expander("🎛️ Filter", expanded=True):
        fc1,fc2,fc3,fc4 = st.columns(4)
        with fc1:
            try: srcs = ["All"]+[r["source"] for r in run_query("SELECT DISTINCT source FROM routes ORDER BY source")]
            except: srcs=["All"]
            f_src = st.selectbox("From", srcs, key="bs_src")
        with fc2:
            try: dsts = ["All"]+[r["destination"] for r in run_query("SELECT DISTINCT destination FROM routes ORDER BY destination")]
            except: dsts=["All"]
            f_dst = st.selectbox("To", dsts, key="bs_dst")
        with fc3: f_date  = st.date_input("Date", value=None, key="bs_date")
        with fc4: f_seats = st.number_input("Min seats", min_value=1, value=1, key="bs_seats")

    try:
        conds  = ["t.status='scheduled'::trip_status", "DATE(t.departure_datetime)>=CURRENT_DATE"]
        params = []
        if f_src  != "All": conds.append("r.source=%s");      params.append(f_src)
        if f_dst  != "All": conds.append("r.destination=%s"); params.append(f_dst)
        if f_date:           conds.append("DATE(t.departure_datetime)=%s"); params.append(f_date)
        if f_seats > 0:      conds.append("t.seats_available>=%s"); params.append(f_seats)

        trips = run_query(f"""
            SELECT t.trip_id, r.source, r.destination, r.distance, r.base_fare,
                   t.departure_datetime, t.arrival_datetime, t.seats_available,
                   b.bus_type, b.capacity, b.amenities
            FROM trips t
            JOIN routes r ON t.route_id=r.route_id
            JOIN buses  b ON t.bus_id=b.bus_id
            WHERE {' AND '.join(conds)}
            ORDER BY t.departure_datetime""", params or None)
    except Exception as e:
        st.error(f"Error: {e}"); return

    if not trips:
        empty_state("🚌", "No trips match your filters."); return

    st.markdown(f"<p style='color:#64748b;margin:.2rem 0 .8rem'><b>{len(trips)}</b> trip(s) found</p>",
                unsafe_allow_html=True)

    for t in trips:
        amenities = t["amenities"] or {}
        if isinstance(amenities, str): amenities = json.loads(amenities)
        icons = "".join(filter(None,[
            "📶 " if amenities.get("wifi") else "",
            "❄️ " if amenities.get("ac")   else "",
            "🔌 " if amenities.get("charging") else "",
            "🛏️ " if amenities.get("blanket") else "",
        ]))
        dep   = t["departure_datetime"].strftime("%a, %d %b %Y · %I:%M %p")
        arr   = t["arrival_datetime"].strftime("%I:%M %p")
        seats_c = "green" if t["seats_available"]>10 else "orange" if t["seats_available"]>0 else "red"

        ci, cb = st.columns([5,1])
        with ci:
            st.markdown(f"""
            <div class="card" style='margin-bottom:.5rem'>
                <div style='display:flex;justify-content:space-between;align-items:center'>
                    <div class="card-title">🚌 {t['source']} → {t['destination']}</div>
                    <div>{badge(f"₹{int(t['base_fare'])}+","blue")} &nbsp;
                    {badge(f"{t['seats_available']} seats",seats_c)}</div>
                </div>
                <div class="card-meta">
                    📅 {dep} → {arr} · 🛣️ {t['distance']} km · 🚌 {t['bus_type']}
                    {("&nbsp;·&nbsp; "+icons) if icons else ""}
                </div>
            </div>""", unsafe_allow_html=True)
        with cb:
            st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
            if t["seats_available"] > 0:
                if st.button("Book →", key=f"bk_{t['trip_id']}", type="primary"):
                    st.session_state.selected_trip = t["trip_id"]
                    nav_to("book_trip")
            else:
                st.button("Full", key=f"fl_{t['trip_id']}", disabled=True)

# ══════════════════════════════════════════════════════════════
# PASSENGER — BOOK TRIP
# ══════════════════════════════════════════════════════════════
def page_book_trip():
    trip_id = st.session_state.get("selected_trip")
    if not trip_id: nav_to("browse")

    st.markdown("""
    <div class="bn-header">
        <h1>🎟️ Book Your Seat</h1>
        <p>Choose your stops, pick a seat and confirm</p>
    </div>""", unsafe_allow_html=True)

    if st.button("← Back to Browse"): nav_to("browse")

    try:
        trip = run_query("""
            SELECT t.trip_id, r.source, r.destination, r.route_id,
                   t.departure_datetime, t.arrival_datetime,
                   t.seats_available, b.bus_type, b.capacity
            FROM trips t
            JOIN routes r ON t.route_id=r.route_id
            JOIN buses  b ON t.bus_id=b.bus_id
            WHERE t.trip_id=%s""", (trip_id,))
        if not trip: st.error("Trip not found."); return
        trip = trip[0]
    except Exception as e:
        st.error(f"Error: {e}"); return

    left, right = st.columns([1,1])

    with left:
        dep  = trip["departure_datetime"].strftime("%a, %d %b %Y")
        dep_t = trip["departure_datetime"].strftime("%I:%M %p")
        arr_t = trip["arrival_datetime"].strftime("%I:%M %p")

        st.markdown(f"""
        <div class="card">
            <div class="card-title">🚌 {trip['source']} → {trip['destination']}</div>
            <div class="card-meta">
                📅 {dep} · 🕐 {dep_t} → {arr_t}<br>
                🚌 {trip['bus_type']} · Capacity {trip['capacity']} ·
                {badge(f"{trip['seats_available']} available","green")}
            </div>
        </div>""", unsafe_allow_html=True)

        section("🛑 Select Stops")
        try:
            stops = run_query("SELECT * FROM get_stops_for_trip(%s) ORDER BY stop_sequence", (trip_id,))
            if not stops: st.error("No stops for this route."); return
            labels  = [f"{s['stop_name']} ({s['location']})" for s in stops]
            ids     = [s["stop_id"] for s in stops]
        except Exception as e:
            st.error(f"Stops error: {e}"); return

        b_idx = st.selectbox("🛫 Board at", range(len(labels)),
                             format_func=lambda i: labels[i], key="bt_b")
        d_opts = list(range(b_idx+1, len(labels)))
        if not d_opts:
            st.warning("Select an earlier boarding stop."); return
        d_idx = st.selectbox("🛬 Drop at", d_opts,
                             format_func=lambda i: labels[i], key="bt_d")

        j_date = st.date_input("📅 Journey Date",
                               value=trip["departure_datetime"].date(),
                               min_value=date.today(), key="bt_jd")

    with right:
        section("🪑 Seat Map")
        st.markdown("""
        <div style='display:flex;gap:14px;margin-bottom:10px;font-size:.79rem'>
            <span><span style='background:#dcfce7;border:2px solid #86efac;
                border-radius:5px;padding:2px 7px;color:#15803d;font-weight:700'>12</span>
                Available</span>
            <span><span style='background:#fee2e2;border:2px solid #fca5a5;
                border-radius:5px;padding:2px 7px;color:#b91c1c;font-weight:700'>5</span>
                Booked</span>
        </div>""", unsafe_allow_html=True)

        try:
            seat_map = run_query("SELECT * FROM get_seat_map(%s) ORDER BY seat_no", (trip_id,))
            avail = [s["seat_no"] for s in seat_map if s["status"]=="available"]

            html = '<div class="seat-grid">'
            for s in seat_map:
                cls = "seat-avail" if s["status"]=="available" else "seat-booked"
                html += f'<div class="seat {cls}">{s["seat_no"]}</div>'
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            if not avail: st.error("All seats booked."); return
            sel_seat = st.selectbox("Choose seat", avail,
                                    format_func=lambda n: f"Seat {n}", key="bt_seat")
        except Exception as e:
            st.error(f"Seat map error: {e}"); return

        try:
            fare_val = int(run_query("SELECT calculate_fare(%s,'AC') fare", (trip["route_id"],))[0]["fare"])
        except: fare_val = "—"

        st.markdown(f"""
        <div class="success-box" style='margin-top:1rem'>
            🪑 <b>Seat {sel_seat}</b> &nbsp;·&nbsp; 💰 Estimated <b>₹{fare_val}</b> (AC)<br>
            🛫 {labels[b_idx]} → 🛬 {labels[d_idx]}
        </div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("✅ Confirm Booking", type="primary", use_container_width=True, key="btn_bk_confirm"):
            try:
                run_proc("CALL create_booking(%s,%s,%s,%s,%s,%s)",
                         (st.session_state.user_id, trip_id,
                          ids[b_idx], ids[d_idx], sel_seat, j_date))
                st.session_state.toast = ("🎉 Booking confirmed! Ticket generated.", "success")
                nav_to("bookings")
            except Exception as e:
                st.error(f"Booking failed: {e}")

# ══════════════════════════════════════════════════════════════
# PASSENGER — MY BOOKINGS
# ══════════════════════════════════════════════════════════════
def page_my_bookings():
    uid = st.session_state.user_id
    show_toast()

    st.markdown("""
    <div class="bn-header">
        <h1>🎫 My Bookings</h1>
        <p>View, track and manage all your bookings</p>
    </div>""", unsafe_allow_html=True)

    f_status = st.selectbox("Filter by status",
                            ["All","confirmed","cancelled","waitlisted"],
                            key="mb_filter", label_visibility="collapsed")

    try:
        conds  = ["b.user_id=%s"]
        params = [uid]
        if f_status != "All":
            conds.append("b.booking_status=%s::booking_status_enum")
            params.append(f_status)

        rows = run_query(f"""
            SELECT b.booking_id, b.seat_no, b.journey_date, b.booking_status::TEXT,
                   b.booking_time, r.source, r.destination,
                   t.departure_datetime, t.arrival_datetime,
                   bs.stop_name boarding, ds.stop_name dropping,
                   tk.ticket_no, tk.fare
            FROM bookings b
            JOIN trips  t  ON b.trip_id=t.trip_id
            JOIN routes r  ON t.route_id=r.route_id
            JOIN stops  bs ON b.boarding_stop=bs.stop_id
            JOIN stops  ds ON b.dropping_stop=ds.stop_id
            LEFT JOIN tickets tk ON tk.booking_id=b.booking_id
            WHERE {' AND '.join(conds)}
            ORDER BY b.booking_time DESC""", params)
    except Exception as e:
        st.error(f"Error: {e}"); return

    if not rows:
        empty_state("🎫","No bookings found.")
        if st.button("🔍 Browse Trips", type="primary"): nav_to("browse")
        return

    for b in rows:
        dep = b["departure_datetime"].strftime("%a, %d %b %Y · %I:%M %p")
        sc  = {"confirmed":"#22c55e","cancelled":"#ef4444","waitlisted":"#f59e0b"}.get(
              b["booking_status"],"#94a3b8")
        tkt = (f'&nbsp;·&nbsp; 🎟️ Ticket #{b["ticket_no"]} &nbsp;·&nbsp; ₹{int(b["fare"])}'
               if b["ticket_no"] else "")

        cm, ca = st.columns([5,1])
        with cm:
            st.markdown(f"""
            <div class="card" style='border-left:4px solid {sc}'>
                <div style='display:flex;justify-content:space-between'>
                    <div class="card-title">
                        🚌 {b['source']} → {b['destination']}
                        &nbsp;{status_badge(b['booking_status'])}
                    </div>
                    <span style='font-size:.73rem;color:#94a3b8'>#{b['booking_id']}</span>
                </div>
                <div class="card-meta">
                    📅 {dep} · 🪑 Seat {b['seat_no']}{tkt}<br>
                    🛫 {b['boarding']} → 🛬 {b['dropping']} ·
                    Booked {b['booking_time'].strftime('%d %b, %I:%M %p')}
                </div>
            </div>""", unsafe_allow_html=True)
        with ca:
            st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
            if b["booking_status"] == "confirmed":
                if st.button("❌ Cancel", key=f"cx_{b['booking_id']}"):
                    try:
                        run_proc("CALL cancel_booking(%s,%s)", (b["booking_id"], uid))
                        st.session_state.toast = ("Booking cancelled.", "success")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Cancel failed: {e}")
            else:
                st.button("—", key=f"nop_{b['booking_id']}", disabled=True)

# ══════════════════════════════════════════════════════════════
# PASSENGER — MY TICKETS
# ══════════════════════════════════════════════════════════════
def page_my_tickets():
    uid = st.session_state.user_id

    st.markdown("""
    <div class="bn-header">
        <h1>🧾 My Tickets</h1>
        <p>All issued tickets with full audit history</p>
    </div>""", unsafe_allow_html=True)

    try:
        tickets = run_query("""
            SELECT tk.ticket_no, tk.fare, tk.duration, tk.issued_at,
                   b.seat_no, b.booking_status::TEXT,
                   r.source, r.destination,
                   t.departure_datetime, t.arrival_datetime,
                   bs.stop_name boarding, ds.stop_name dropping
            FROM tickets tk
            JOIN bookings b  ON tk.booking_id=b.booking_id
            JOIN trips    t  ON b.trip_id=t.trip_id
            JOIN routes   r  ON t.route_id=r.route_id
            JOIN stops    bs ON b.boarding_stop=bs.stop_id
            JOIN stops    ds ON b.dropping_stop=ds.stop_id
            WHERE b.user_id=%s
            ORDER BY tk.issued_at DESC""", (uid,))
    except Exception as e:
        st.error(f"Error: {e}"); return

    if not tickets:
        empty_state("🧾","No tickets yet — book a trip first!"); return

    for tk in tickets:
        bc   = "#22c55e" if tk["booking_status"]=="confirmed" else "#ef4444"
        dur  = str(tk["duration"]).split(".")[0] if tk["duration"] else "N/A"
        dep  = tk["departure_datetime"].strftime("%a, %d %b %Y · %I:%M %p")
        iss  = tk["issued_at"].strftime("%d %b %Y") if tk["issued_at"] else "—"

        st.markdown(f"""
        <div class="card" style='border-left:4px solid {bc}'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start'>
                <div>
                    <div class="card-title">🎟️ Ticket #{tk['ticket_no']}
                        &nbsp;{status_badge(tk['booking_status'])}</div>
                    <div class="card-meta">
                        🚌 <b>{tk['source']} → {tk['destination']}</b><br>
                        📅 {dep} · 🪑 Seat {tk['seat_no']}<br>
                        🛫 {tk['boarding']} → 🛬 {tk['dropping']}<br>
                        💰 Fare: <b>₹{int(tk['fare'])}</b> · ⏱️ {dur}
                    </div>
                </div>
                <div style='font-size:.74rem;color:#94a3b8;text-align:right'>
                    Issued<br>{iss}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        with st.expander(f"📜 Ticket #{tk['ticket_no']} history"):
            try:
                hist = run_query(
                    "SELECT * FROM ticket_history WHERE ticket_no=%s ORDER BY changed_at",
                    (tk["ticket_no"],))
                for h in hist:
                    icon = {"issued":"🎫","cancelled":"❌","modified":"✏️"}.get(h["status"],"📝")
                    st.markdown(f"""
                    <div class="tl"><div class="tl-dot"></div>
                    <div class="tl-body"><b>{icon} {h['status'].capitalize()}</b>
                    {(" — "+h['remarks']) if h['remarks'] else ""}<br>
                    <span>{h['changed_at'].strftime('%d %b %Y, %I:%M %p')}</span>
                    </div></div>""", unsafe_allow_html=True)
                if not hist: st.caption("No history.")
            except Exception as e:
                st.error(f"History error: {e}")

# ══════════════════════════════════════════════════════════════
# PASSENGER — PAYMENTS
# ══════════════════════════════════════════════════════════════
def page_payments():
    uid = st.session_state.user_id

    st.markdown("""
    <div class="bn-header">
        <h1>💳 Payment History</h1>
        <p>All transactions linked to your bookings</p>
    </div>""", unsafe_allow_html=True)

    try:
        rows = run_query("""
            SELECT p.payment_id, p.amount, p.payment_mode::TEXT,
                   p.payment_status::TEXT, p.payment_date,
                   r.source, r.destination, b.seat_no
            FROM payments p
            JOIN bookings b ON p.booking_id=b.booking_id
            JOIN trips    t ON b.trip_id=t.trip_id
            JOIN routes   r ON t.route_id=r.route_id
            WHERE b.user_id=%s ORDER BY p.payment_date DESC""", (uid,))
    except Exception as e:
        st.error(f"Error: {e}"); return

    if not rows: empty_state("💳","No payment records found."); return

    total = sum(float(r["amount"]) for r in rows if r["payment_status"]=="success")
    c1,c2,c3 = st.columns(3)
    with c1: stat_card("Total Spent",  f"₹{int(total):,}", color="#22c55e")
    with c2: stat_card("Transactions", len(rows),           color="#0ea5e9")
    with c3: stat_card("Successful",   sum(1 for r in rows if r["payment_status"]=="success"), color="#8b5cf6")

    st.markdown("<br>", unsafe_allow_html=True)
    df = pd.DataFrame([{
        "ID": r["payment_id"],
        "Route": f"{r['source']} → {r['destination']}",
        "Seat": r["seat_no"], "Amount": f"₹{int(r['amount'])}",
        "Mode": r["payment_mode"].upper(),
        "Status": r["payment_status"].capitalize(),
        "Date": r["payment_date"].strftime("%d %b %Y, %I:%M %p"),
    } for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# DRIVER
# ══════════════════════════════════════════════════════════════
def page_manage_drivers():
    st.markdown("## 👤 Add Driver")

    name = st.text_input("Driver Name")
    phone = st.text_input("Contact Number")

    if st.button("Add Driver"):
        try:
            add_driver(name, phone)
            st.success("Driver added successfully")

    drivers = run_query("""
        SELECT d.emp_id, e.name, e.contact_no
        FROM drivers d
        JOIN employees e ON d.emp_id = e.emp_id
    """)

    st.dataframe(drivers)
# ══════════════════════════════════════════════════════════════
# COORDINATOR — ANALYTICS
# ══════════════════════════════════════════════════════════════
def page_analytics():
    show_toast()
    st.markdown("""
    <div class="bn-header">
        <h1>📊 Analytics Dashboard</h1>
        <p>Live operational overview of BusNexus</p>
    </div>""", unsafe_allow_html=True)

    try:
        t_trips  = run_query("SELECT COUNT(*) n FROM trips")[0]["n"]
        sched    = run_query("SELECT COUNT(*) n FROM trips WHERE status='scheduled'")[0]["n"]
        t_bk     = run_query("SELECT COUNT(*) n FROM bookings")[0]["n"]
        conf     = run_query("SELECT COUNT(*) n FROM bookings WHERE booking_status='confirmed'")[0]["n"]
        t_rev    = run_query("SELECT COALESCE(SUM(amount),0) n FROM payments WHERE payment_status='success'")[0]["n"]
        t_users  = run_query("SELECT COUNT(*) n FROM users WHERE role='passenger'")[0]["n"]
    except: t_trips=sched=t_bk=conf=t_rev=t_users=0

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: stat_card("Trips",     t_trips,             color="#0ea5e9")
    with c2: stat_card("Scheduled", sched,               color="#22c55e")
    with c3: stat_card("Bookings",  t_bk,                color="#8b5cf6")
    with c4: stat_card("Confirmed", conf,                color="#06b6d4")
    with c5: stat_card("Revenue",   f"₹{int(t_rev):,}", color="#22c55e")
    with c6: stat_card("Passengers",t_users,             color="#f59e0b")

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)

    with c1:
        section("💰 Revenue by Route")
        try:
            data = run_query("""
                SELECT r.source||' → '||r.destination route,
                       COALESCE(SUM(p.amount),0) revenue
                FROM routes r
                LEFT JOIN trips    t  ON r.route_id=t.route_id
                LEFT JOIN bookings b  ON t.trip_id=b.trip_id
                LEFT JOIN payments p  ON b.booking_id=p.booking_id AND p.payment_status='success'
                GROUP BY route ORDER BY revenue DESC""")
            if data:
                fig = px.bar(pd.DataFrame(data), x="route", y="revenue",
                             color="revenue", color_continuous_scale="Blues",
                             labels={"revenue":"₹","route":"Route"})
                fig.update_layout(coloraxis_showscale=False, showlegend=False,
                                  margin=dict(l=0,r=0,t=5,b=0),
                                  plot_bgcolor="rgba(0,0,0,0)",
                                  paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.error(f"Chart error: {e}")

    with c2:
        section("📈 Occupancy % per Trip")
        try:
            data = run_query("""
                SELECT t.trip_id,
                       r.source||'→'||r.destination route,
                       ROUND((b.capacity-t.seats_available)::NUMERIC/NULLIF(b.capacity,0)*100,1) pct,
                       t.seats_available
                FROM trips t
                JOIN routes r ON t.route_id=r.route_id
                JOIN buses  b ON t.bus_id=b.bus_id""")
            if data:
                fig = px.bar(pd.DataFrame(data), x="trip_id", y="pct",
                             color="pct",
                             color_continuous_scale=["#22c55e","#f59e0b","#ef4444"],
                             range_color=[0,100],
                             labels={"trip_id":"Trip","pct":"Occupancy %"},
                             hover_data=["route","seats_available"])
                fig.update_layout(coloraxis_showscale=False,
                                  margin=dict(l=0,r=0,t=5,b=0),
                                  plot_bgcolor="rgba(0,0,0,0)",
                                  paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.error(f"Chart error: {e}")

    c3,c4 = st.columns(2)
    with c3:
        section("🥧 Booking Status Split")
        try:
            data = run_query("SELECT booking_status::TEXT status, COUNT(*) n FROM bookings GROUP BY booking_status")
            if data:
                fig = px.pie(pd.DataFrame(data), values="n", names="status",
                             color_discrete_map={"confirmed":"#22c55e","cancelled":"#ef4444","waitlisted":"#f59e0b"})
                fig.update_layout(margin=dict(l=0,r=0,t=5,b=0), paper_bgcolor="rgba(0,0,0,0)")
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.error(f"Chart error: {e}")

    with c4:
        section("💳 Payment Mode Split")
        try:
            data = run_query("SELECT payment_mode::TEXT mode, SUM(amount) total FROM payments GROUP BY payment_mode")
            if data:
                fig = px.pie(pd.DataFrame(data), values="total", names="mode",
                             color_discrete_sequence=["#0ea5e9","#8b5cf6","#22c55e"])
                fig.update_layout(margin=dict(l=0,r=0,t=5,b=0), paper_bgcolor="rgba(0,0,0,0)")
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e: st.error(f"Chart error: {e}")

# ══════════════════════════════════════════════════════════════
# COORDINATOR — SCHEDULE TRIP  ◀ NEW
# ══════════════════════════════════════════════════════════════
def page_schedule_trip():
    show_toast()
    st.markdown("""
    <div class="bn-header">
        <h1>🗓️ Schedule a New Trip</h1>
        <p>Assign a route, bus and driver — set departure and arrival times</p>
    </div>""", unsafe_allow_html=True)

    # ── Load reference tables ─────────────────────────────────
    try:
        routes  = run_query("SELECT route_id, source, destination, distance, base_fare FROM routes ORDER BY source")
        buses   = run_query("SELECT b.bus_id, b.bus_type, b.capacity, b.amenities FROM buses b ORDER BY b.bus_type")
        drivers = run_query("SELECT d.emp_id, e.name FROM drivers d JOIN employees e ON d.emp_id=e.emp_id ORDER BY e.name")
    except Exception as e:
        st.error(f"Failed to load reference data: {e}"); return

    if not routes:
        st.markdown('<div class="warn-box">⚠️ No routes exist. Add a route first via <b>Fleet & Trips → Routes</b>.</div>',
                    unsafe_allow_html=True); return
    if not buses:
        st.markdown('<div class="warn-box">⚠️ No buses registered. Add a bus first via <b>Fleet & Trips → Buses</b>.</div>',
                    unsafe_allow_html=True); return
    if not drivers:
        st.markdown('<div class="warn-box">⚠️ No drivers registered.</div>',
                    unsafe_allow_html=True); return

    route_map  = {f"{r['source']} → {r['destination']}  (₹{int(r['base_fare'])}, {r['distance']} km)": r  for r in routes}
    bus_map    = {f"Bus #{b['bus_id']} — {b['bus_type']} ({b['capacity']} seats)": b  for b in buses}
    driver_map = {f"{d['name']} (ID {d['emp_id']})": d  for d in drivers}

    left, right = st.columns([1,1])

    with left:
        section("📋 Trip Details")
        sel_route  = st.selectbox("🛣️ Route",  list(route_map.keys()),  key="st_route")
        sel_bus    = st.selectbox("🚌 Bus",    list(bus_map.keys()),    key="st_bus")
        sel_driver = st.selectbox("👤 Driver", list(driver_map.keys()), key="st_driver")

        section("📅 Departure")
        dep_date = st.date_input("Date", value=date.today()+timedelta(days=1),
                                 min_value=date.today(), key="st_dep_date")
        dep_time = st.time_input("Time", value=time(8,0), key="st_dep_time", step=300)

        section("🏁 Arrival")
        arr_date = st.date_input("Date ", value=dep_date, min_value=dep_date, key="st_arr_date")
        arr_time = st.time_input("Time ", value=time(12,0), key="st_arr_time", step=300)

    with right:
        section("🔎 Preview & Validate")

        ro = route_map[sel_route]
        bo = bus_map[sel_bus]
        dr = driver_map[sel_driver]

        dep_dt = datetime.combine(dep_date, dep_time)
        arr_dt = datetime.combine(arr_date, arr_time)
        dur_sec = (arr_dt - dep_dt).total_seconds()
        valid   = dur_sec > 0

        # Stop chain
        try:
            stops = run_query(
                "SELECT s.stop_name FROM route_stops rs JOIN stops s ON rs.stop_id=s.stop_id WHERE rs.route_id=%s ORDER BY rs.stop_sequence",
                (ro["route_id"],))
            stop_chain = " → ".join(s["stop_name"] for s in stops) if stops else "⚠️ No stops configured"
        except: stop_chain = "—"

        # Amenities
        amenities = bo.get("amenities") or {}
        if isinstance(amenities, str): amenities = json.loads(amenities)
        amen_str = ", ".join(filter(None,[
            "WiFi"     if amenities.get("wifi") else "",
            "AC"       if amenities.get("ac")   else "",
            "Charging" if amenities.get("charging") else "",
            "Blanket"  if amenities.get("blanket") else "",
        ])) or "None"

        dur_str = f"{int(dur_sec//3600)}h {int((dur_sec%3600)//60)}m" if valid else "—"

        preview_color = "#0ea5e9" if valid else "#ef4444"
        st.markdown(f"""
        <div class="card" style='border-left:4px solid {preview_color}'>
            <div class="card-title">🚌 {ro['source']} → {ro['destination']}</div>
            <div class="card-meta">
                📅 <b>{dep_dt.strftime('%a, %d %b %Y · %I:%M %p')}</b><br>
                🏁 <b>{arr_dt.strftime('%a, %d %b %Y · %I:%M %p')}</b><br>
                ⏱️ Duration: <b>{dur_str}</b><br>
                🛣️ {ro['distance']} km · Base fare ₹{int(ro['base_fare'])}<br>
                🚌 {bo['bus_type']} — {bo['capacity']} seats · {amen_str}<br>
                👤 Driver: {dr['name']}<br>
                📍 {stop_chain}
            </div>
        </div>""", unsafe_allow_html=True)

        issues = []
        if not valid:
            issues.append("Arrival must be <b>after</b> departure.")

        # Bus conflict check
        conflict_ids = []
        if valid:
            try:
                clashes = run_query(
                    """SELECT trip_id FROM trips
                       WHERE bus_id=%s AND status='scheduled'::trip_status
                         AND NOT (arrival_datetime<=%s OR departure_datetime>=%s)""",
                    (bo["bus_id"], dep_dt, arr_dt))
                conflict_ids = [str(c["trip_id"]) for c in clashes]
                if conflict_ids:
                    issues.append(f"Bus already assigned to Trip(s) <b>{', '.join(conflict_ids)}</b> in this window.")
            except: pass

        # Driver conflict check
        if valid:
            try:
                dclashes = run_query(
                    """SELECT trip_id FROM trips
                       WHERE driver_id=%s AND status='scheduled'::trip_status
                         AND NOT (arrival_datetime<=%s OR departure_datetime>=%s)""",
                    (dr["emp_id"], dep_dt, arr_dt))
                did = [str(c["trip_id"]) for c in dclashes]
                if did:
                    issues.append(f"Driver already assigned to Trip(s) <b>{', '.join(did)}</b> in this window.")
            except: pass

        if issues:
            for iss in issues:
                st.markdown(f'<div class="warn-box">⚠️ {iss}</div>', unsafe_allow_html=True)

        if not issues:
            st.markdown('<div class="success-box">✅ All checks passed — ready to schedule.</div>',
                        unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗓️ Confirm & Schedule Trip", type="primary",
                     use_container_width=True, disabled=bool(issues),
                     key="btn_sched"):
            try:
                row = run_write_returning(
                    """INSERT INTO trips
                           (bus_id, route_id, driver_id,
                            departure_datetime, arrival_datetime,
                            status, seats_available)
                       VALUES (%s,%s,%s,%s,%s,'scheduled'::trip_status,%s)
                       RETURNING trip_id""",
                    (bo["bus_id"], ro["route_id"], dr["emp_id"],
                     dep_dt, arr_dt, bo["capacity"]))
                tid = row["trip_id"]
                st.session_state.toast = (
                    f"✅ Trip #{tid} scheduled — {ro['source']} → {ro['destination']} on "
                    f"{dep_dt.strftime('%d %b %Y')}.", "success")
                nav_to("fleet")
            except Exception as e:
                st.error(f"Scheduling failed: {e}")

# ══════════════════════════════════════════════════════════════
# COORDINATOR — FLEET & TRIPS
# ══════════════════════════════════════════════════════════════
def page_fleet():
    show_toast()
    st.markdown("""
    <div class="bn-header">
        <h1>🚌 Fleet & Trips</h1>
        <p>View and manage all trips, buses and routes</p>
    </div>""", unsafe_allow_html=True)

    tab_trips, tab_buses, tab_routes = st.tabs(["🗓️ Trips", "🚌 Buses", "🛣️ Routes & Stops"])

    # ── TRIPS ─────────────────────────────────────────────────
    with tab_trips:
        ch, cb = st.columns([5,1])
        with ch: section("All Trips")
        with cb:
            st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
            if st.button("＋ Schedule", type="primary", key="fl_new"):
                nav_to("schedule_trip")

        sf = st.radio("Show", ["All","Scheduled","Completed","Cancelled"],
                      horizontal=True, key="fl_sf")
        sfmap = {"All":None,"Scheduled":"scheduled","Completed":"completed","Cancelled":"cancelled"}

        try:
            conds  = ["1=1"]
            params = []
            if sfmap[sf]:
                conds.append("t.status=%s::trip_status"); params.append(sfmap[sf])
            trips = run_query(f"""
                SELECT t.trip_id, r.source, r.destination,
                       t.departure_datetime, t.arrival_datetime,
                       t.status::TEXT, t.seats_available,
                       b.bus_type, b.capacity, e.name driver
                FROM trips t
                JOIN routes    r ON t.route_id=r.route_id
                JOIN buses     b ON t.bus_id=b.bus_id
                JOIN employees e ON t.driver_id=e.emp_id
                WHERE {' AND '.join(conds)}
                ORDER BY t.departure_datetime DESC""", params or None)
        except Exception as e:
            st.error(f"Error: {e}"); trips=[]

        if not trips:
            empty_state("🗓️","No trips found.")
        else:
            for t in trips:
                dep   = t["departure_datetime"].strftime("%a, %d %b %Y · %I:%M %p")
                arr   = t["arrival_datetime"].strftime("%I:%M %p")
                occ   = t["capacity"] - t["seats_available"]
                occ_p = round(occ/t["capacity"]*100) if t["capacity"] else 0
                oc    = "green" if occ_p<60 else "orange" if occ_p<90 else "red"
                si    = {"scheduled":"🟢","completed":"✅","cancelled":"🔴"}.get(t["status"],"⚪")

                cm,ca = st.columns([5,2])
                with cm:
                    st.markdown(f"""
                    <div class="card">
                        <div style='display:flex;justify-content:space-between;align-items:center'>
                            <div class="card-title">
                                {si} Trip #{t['trip_id']} — {t['source']} → {t['destination']}
                                &nbsp;{status_badge(t['status'])}
                            </div>
                            {badge(f"{occ}/{t['capacity']} booked ({occ_p}%)",oc)}
                        </div>
                        <div class="card-meta">
                            📅 {dep} → {arr} · 🚌 {t['bus_type']} · 👤 {t['driver']}
                        </div>
                    </div>""", unsafe_allow_html=True)
                with ca:
                    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                    if t["status"] == "scheduled":
                        ca1,ca2 = st.columns(2)
                        with ca1:
                            if st.button("✅", key=f"comp_{t['trip_id']}", help="Mark Completed"):
                                try:
                                    run_write("UPDATE trips SET status='completed'::trip_status WHERE trip_id=%s", (t["trip_id"],))
                                    st.session_state.toast=(f"Trip #{t['trip_id']} marked completed.","success")
                                    st.rerun()
                                except Exception as e: st.error(str(e))
                        with ca2:
                            if st.button("❌", key=f"canct_{t['trip_id']}", help="Cancel Trip"):
                                try:
                                    run_write("UPDATE trips SET status='cancelled'::trip_status WHERE trip_id=%s", (t["trip_id"],))
                                    st.session_state.toast=(f"Trip #{t['trip_id']} cancelled.","success")
                                    st.rerun()
                                except Exception as e: st.error(str(e))
                    else:
                        st.caption(t["status"].capitalize())

    # ── BUSES ─────────────────────────────────────────────────
    with tab_buses:
        section("Registered Buses")
        try:
            buses = run_query("""
                SELECT b.bus_id, b.bus_type, b.capacity, b.amenities, u.name coordinator
                FROM buses b JOIN users u ON b.coordinator_id=u.user_id ORDER BY b.bus_id""")
        except Exception as e:
            st.error(f"Error: {e}"); buses=[]

        if not buses:
            empty_state("🚌","No buses registered.")
        else:
            for b in buses:
                amenities = b["amenities"] or {}
                if isinstance(amenities, str): amenities = json.loads(amenities)
                icons = " ".join(filter(None,[
                    "📶 WiFi"     if amenities.get("wifi") else "",
                    "❄️ AC"       if amenities.get("ac") else "",
                    "🔌 Charging" if amenities.get("charging") else "",
                    "🛏️ Blanket"  if amenities.get("blanket") else "",
                ]))
                try:
                    at = run_query("SELECT COUNT(*) n FROM trips WHERE bus_id=%s AND status='scheduled'", (b["bus_id"],))[0]["n"]
                except: at=0
                st.markdown(f"""
                <div class="card">
                    <div style='display:flex;justify-content:space-between;align-items:center'>
                        <div class="card-title">🚌 Bus #{b['bus_id']} — {b['bus_type']}</div>
                        {badge(f"{at} scheduled trip(s)","blue" if at else "gray")}
                    </div>
                    <div class="card-meta">
                        👥 {b['capacity']} seats · 🎯 {b['coordinator']}<br>
                        {icons or "No amenities"}
                    </div>
                </div>""", unsafe_allow_html=True)

        divider()
        with st.expander("➕ Register a New Bus"):
            try:
                coords = run_query("SELECT user_id, name FROM users WHERE role='coordinator' ORDER BY name")
                if not coords:
                    st.warning("No coordinators exist.")
                else:
                    cmap   = {c["name"]: c["user_id"] for c in coords}
                    bt     = st.text_input("Bus Type", placeholder="AC Sleeper", key="nb_t")
                    bc     = st.number_input("Capacity", 1, 100, 40, key="nb_c")
                    bco    = st.selectbox("Coordinator", list(cmap.keys()), key="nb_co")
                    st.write("**Amenities**")
                    c1,c2,c3,c4 = st.columns(4)
                    with c1: w = st.checkbox("📶 WiFi",    key="nb_w")
                    with c2: a = st.checkbox("❄️ AC",      key="nb_a")
                    with c3: ch= st.checkbox("🔌 Charging",key="nb_ch")
                    with c4: bl= st.checkbox("🛏️ Blanket", key="nb_bl")
                    if st.button("Register Bus", type="primary", key="btn_addbus"):
                        if not bt.strip():
                            st.warning("Bus type is required.")
                        else:
                            try:
                                run_write(
                                    "INSERT INTO buses(bus_type,capacity,amenities,coordinator_id) VALUES(%s,%s,%s::jsonb,%s)",
                                    (bt.strip(), bc, json.dumps({"wifi":w,"ac":a,"charging":ch,"blanket":bl}), cmap[bco]))
                                st.session_state.toast=("🚌 Bus registered.","success")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {e}")
            except Exception as e:
                st.error(f"Error: {e}")

    # ── ROUTES ────────────────────────────────────────────────
    with tab_routes:
        section("Routes & Stops")
        try:
            routes = run_query("SELECT route_id, source, destination, distance, base_fare FROM routes ORDER BY source")
        except Exception as e:
            st.error(f"Error: {e}"); routes=[]

        if not routes:
            empty_state("🛣️","No routes configured.")
        else:
            for r in routes:
                with st.expander(f"🛣️ {r['source']} → {r['destination']}  |  ₹{int(r['base_fare'])}  ·  {r['distance']} km"):
                    try:
                        stops = run_query("""
                            SELECT s.stop_name, s.location, rs.stop_sequence,
                                   rs.arrival_time, rs.departure_time
                            FROM route_stops rs JOIN stops s ON rs.stop_id=s.stop_id
                            WHERE rs.route_id=%s ORDER BY rs.stop_sequence""",
                            (r["route_id"],))
                        if stops:
                            df = pd.DataFrame([{
                                "#":       s["stop_sequence"],
                                "Stop":    s["stop_name"],
                                "Location":s["location"],
                                "Arrives": str(s["arrival_time"])   if s["arrival_time"]   else "—",
                                "Departs": str(s["departure_time"]) if s["departure_time"] else "—",
                            } for s in stops])
                            st.dataframe(df, hide_index=True, use_container_width=True)
                            st.caption("📍 " + " → ".join(s["stop_name"] for s in stops))
                        else:
                            st.info("No stops configured for this route.")
                    except Exception as e:
                        st.error(f"Stops error: {e}")

        divider()
        with st.expander("➕ Add a New Route"):
            rc1,rc2 = st.columns(2)
            with rc1:
                ns = st.text_input("Source City",      key="nr_s")
                nd = st.text_input("Destination City", key="nr_d")
            with rc2:
                ndi = st.number_input("Distance (km)", min_value=1,   value=100,   key="nr_di")
                nf  = st.number_input("Base Fare (₹)", min_value=0.0, value=200.0, step=10.0, key="nr_f")
            if st.button("Add Route", type="primary", key="btn_addroute"):
                if not ns.strip() or not nd.strip():
                    st.warning("Source and destination required.")
                else:
                    try:
                        run_write("INSERT INTO routes(source,destination,distance,base_fare) VALUES(%s,%s,%s,%s)",
                                  (ns.strip(), nd.strip(), ndi, nf))
                        st.session_state.toast=(f"Route {ns} → {nd} added.","success")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed: {e}")

# ══════════════════════════════════════════════════════════════
# COORDINATOR — ALL BOOKINGS
# ══════════════════════════════════════════════════════════════
def page_all_bookings():
    st.markdown("""
    <div class="bn-header">
        <h1>🗂️ All Bookings</h1>
        <p>Complete booking registry across all passengers</p>
    </div>""", unsafe_allow_html=True)

    fa,fb,fc = st.columns(3)
    with fa: fs  = st.selectbox("Status",["All","confirmed","cancelled","waitlisted"],key="ab_s")
    with fb: fkw = st.text_input("Route keyword", placeholder="Mumbai, Pune…", key="ab_k")
    with fc: fd  = st.date_input("Journey Date", value=None, key="ab_d")

    try:
        conds=["1=1"]; params=[]
        if fs != "All":  conds.append("b.booking_status=%s::booking_status_enum"); params.append(fs)
        if fkw.strip():  conds.append("(r.source ILIKE %s OR r.destination ILIKE %s)"); params+=[f"%{fkw}%",f"%{fkw}%"]
        if fd:           conds.append("b.journey_date=%s"); params.append(fd)

        rows = run_query(f"""
            SELECT b.booking_id, u.name passenger, r.source, r.destination,
                   b.journey_date, b.seat_no, b.booking_status::TEXT,
                   b.booking_time, t.departure_datetime,
                   tk.ticket_no, tk.fare
            FROM bookings b
            JOIN users  u  ON b.user_id=u.user_id
            JOIN trips  t  ON b.trip_id=t.trip_id
            JOIN routes r  ON t.route_id=r.route_id
            LEFT JOIN tickets tk ON tk.booking_id=b.booking_id
            WHERE {' AND '.join(conds)}
            ORDER BY b.booking_time DESC""", params or None)
    except Exception as e:
        st.error(f"Error: {e}"); return

    if not rows: empty_state("🗂️","No bookings match the filters."); return

    c1,c2,c3 = st.columns(3)
    with c1: stat_card("Total",     len(rows),  color="#0ea5e9")
    with c2: stat_card("Confirmed", sum(1 for r in rows if r["booking_status"]=="confirmed"), color="#22c55e")
    with c3: stat_card("Cancelled", sum(1 for r in rows if r["booking_status"]=="cancelled"), color="#ef4444")

    st.markdown("<br>", unsafe_allow_html=True)
    df = pd.DataFrame([{
        "ID":        r["booking_id"],
        "Passenger": r["passenger"],
        "Route":     f"{r['source']} → {r['destination']}",
        "Journey":   r["journey_date"].strftime("%d %b %Y"),
        "Departure": r["departure_datetime"].strftime("%d %b %Y, %I:%M %p"),
        "Seat":      r["seat_no"],
        "Ticket #":  r["ticket_no"] or "—",
        "Fare (₹)":  int(r["fare"]) if r["fare"] else "—",
        "Status":    r["booking_status"].capitalize(),
        "Booked At": r["booking_time"].strftime("%d %b, %I:%M %p"),
    } for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# COORDINATOR — TICKET REGISTRY
# ══════════════════════════════════════════════════════════════
def page_ticket_registry():
    st.markdown("""
    <div class="bn-header">
        <h1>📋 Ticket Registry</h1>
        <p>Full temporal audit trail across all tickets</p>
    </div>""", unsafe_allow_html=True)

    f1,f2 = st.columns(2)
    with f1: fev = st.selectbox("Event",["All","issued","cancelled","modified"],key="tr_ev")
    with f2: frk = st.text_input("Route keyword", key="tr_rk")

    try:
        conds=["1=1"]; params=[]
        if fev != "All": conds.append("th.status=%s"); params.append(fev)
        if frk.strip():  conds.append("(r.source ILIKE %s OR r.destination ILIKE %s)"); params+=[f"%{frk}%",f"%{frk}%"]

        rows = run_query(f"""
            SELECT th.history_id, th.ticket_no, u.name passenger,
                   r.source, r.destination, tk.fare,
                   th.status event, th.changed_at, th.remarks
            FROM ticket_history th
            JOIN tickets  tk ON th.ticket_no=tk.ticket_no
            JOIN bookings b  ON tk.booking_id=b.booking_id
            JOIN users    u  ON b.user_id=u.user_id
            JOIN trips    t  ON b.trip_id=t.trip_id
            JOIN routes   r  ON t.route_id=r.route_id
            WHERE {' AND '.join(conds)}
            ORDER BY th.changed_at DESC""", params or None)
    except Exception as e:
        st.error(f"Error: {e}"); return

    if not rows: empty_state("📋","No ticket history found."); return

    st.caption(f"{len(rows)} event(s) logged")
    df = pd.DataFrame([{
        "Hist. ID":  r["history_id"],
        "Ticket #":  r["ticket_no"],
        "Passenger": r["passenger"],
        "Route":     f"{r['source']} → {r['destination']}",
        "Fare (₹)":  int(r["fare"]),
        "Event":     r["event"].capitalize(),
        "Timestamp": r["changed_at"].strftime("%d %b %Y, %I:%M %p"),
        "Remarks":   r["remarks"] or "",
    } for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# COORDINATOR — USERS
# ══════════════════════════════════════════════════════════════
def page_users():
    st.markdown("""
    <div class="bn-header">
        <h1>👥 Users</h1>
        <p>All registered passengers, coordinators and employees</p>
    </div>""", unsafe_allow_html=True)

    try:
        users = run_query("""
            SELECT u.user_id, u.name, u.email, u.contact_no,
                   u.role::TEXT role,
                   passenger_booking_count(u.user_id) bookings
            FROM users u ORDER BY u.role, u.name""")
    except Exception as e:
        st.error(f"Error: {e}"); return

    pax   = [u for u in users if u["role"]=="passenger"]
    coord = [u for u in users if u["role"]=="coordinator"]

    c1,c2,c3 = st.columns(3)
    with c1: stat_card("Total Users",   len(users), color="#0ea5e9")
    with c2: stat_card("Passengers",    len(pax),   color="#22c55e")
    with c3: stat_card("Coordinators",  len(coord), color="#8b5cf6")

    st.markdown("<br>", unsafe_allow_html=True)
    tp,tc,te = st.tabs(["🧍 Passengers","🎯 Coordinators","🔧 Employees"])

    with tp:
        if pax:
            df = pd.DataFrame([{"ID":u["user_id"],"Name":u["name"],"Email":u["email"],
                                 "Phone":u["contact_no"] or "—","Bookings":u["bookings"]} for u in pax])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else: empty_state("🧍","No passengers yet.")

    with tc:
        if coord:
            df = pd.DataFrame([{"ID":u["user_id"],"Name":u["name"],"Email":u["email"],
                                 "Phone":u["contact_no"] or "—"} for u in coord])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else: empty_state("🎯","No coordinators yet.")

    with te:
        try:
            emps = run_query("""
                SELECT e.emp_id, e.name, e.contact_no,
                       CASE WHEN d.emp_id IS NOT NULL THEN 'Driver'
                            WHEN m.emp_id IS NOT NULL THEN 'Maintenance' ELSE 'Other' END role,
                       m.specialization, m.shift
                FROM employees e
                LEFT JOIN drivers          d ON d.emp_id=e.emp_id
                LEFT JOIN maintenance_staff m ON m.emp_id=e.emp_id
                ORDER BY e.name""")
            if emps:
                df = pd.DataFrame([{"ID":em["emp_id"],"Name":em["name"],"Role":em["role"],
                                     "Contact":em["contact_no"] or "—",
                                     "Specialization":em["specialization"] or "—",
                                     "Shift":em["shift"] or "—"} for em in emps])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else: empty_state("🔧","No employees registered.")
        except Exception as e:
            st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════
PASSENGER_PAGES = {
    "dashboard": page_passenger_dashboard,
    "browse":    page_browse_trips,
    "book_trip": page_book_trip,
    "bookings":  page_my_bookings,
    "tickets":   page_my_tickets,
    "payments":  page_payments,
}
COORDINATOR_PAGES = {
    "analytics":       page_analytics,
    "schedule_trip":   page_schedule_trip,
    "fleet":           page_fleet,
    "all_bookings":    page_all_bookings,
    "ticket_registry": page_ticket_registry,
    "users":           page_users,
    "dashboard":       page_analytics,
    "driver": page_manage_drivers,
}

def main():
    if not st.session_state.logged_in:
        page_login(); return

    sidebar()
    role     = st.session_state.user_role
    page     = st.session_state.page
    dispatch = PASSENGER_PAGES if role == "passenger" else COORDINATOR_PAGES
    handler  = dispatch.get(page)
    if handler:
        handler()
    else:
        st.session_state.page = "dashboard"
        st.rerun()

if __name__ == "__main__":
    main()