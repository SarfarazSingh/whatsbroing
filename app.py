"""
app.py — What's BROing (Streamlit Cloud Compatible with Secrets)

Run web app locally:
    pip install streamlit gspread google-auth
    streamlit run app.py

Deploy to Streamlit Cloud:
    Add secrets in Streamlit Cloud dashboard under Settings > Secrets

Run tests only:
    python app.py --test
"""

from __future__ import annotations

import sys
import csv
import time
import unittest
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple

# ---- Try to import Streamlit (guarded) ----
try:
    import streamlit as st  # type: ignore
    STREAMLIT_AVAILABLE = True
except ModuleNotFoundError:
    st = None  # type: ignore
    STREAMLIT_AVAILABLE = False

# ---- Timezone (standard library) ----
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

# ---- Google Sheets imports ----
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ModuleNotFoundError:
    GSHEETS_AVAILABLE = False

# --------------------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------------------
APP_NAME = "What's BROing — CoffeeConnect Madrid"
MADRID_TZ = ZoneInfo("Europe/Madrid") if ZoneInfo else None
# Fixed public launch date/time (Madrid time)
LAUNCH_TIME = datetime(2025, 11, 1, 12, 0, 0, tzinfo=MADRID_TZ)

# ---- Load credentials from Streamlit secrets or fallback to hardcoded ----
def get_credentials():
    """Get Google Sheets credentials from Streamlit secrets or fallback"""
    if STREAMLIT_AVAILABLE and hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
        # Running on Streamlit Cloud with secrets
        return dict(st.secrets["gcp_service_account"]), st.secrets.get("spreadsheet_id", "")
    else:
        # Local development fallback
        SERVICE_ACCOUNT_INFO = {
            "type": "service_account",
            "project_id": "whatsbroing",
            "private_key_id": "815e63ba2326c79fa0767ca6477da80a405bf131",
            "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQClRfzSVSIAL5bS
M8HZsDlunkIAX5ZvO+rkf8drNIJ/vkVkuRCDphGXccMEcHG9b2FFpi0nkxM/kU40
S5zUHeCaChD2qPI7+Ut0wMZLXUDmTnRjc7w+5m7FifnNZd3HitofMuQcaUSWvuAO
01RaLcz9V24g1LvpEFSRUpdToxpW0nxKEWdyVThfmeZYXNhoa+qt+4x5K+xpV0Py
tyNaUEBPVAimjt1OKp4xNe82t0rXD8kijaXzQ96WPgFZjm3pWo0L+hHvqnVe3fMR
JFHLR+C1CKWjmK+nbS6ER6OyW/JSNY+iBjxJFgmwRuBO6lYO+RzTto/neoieCOY7
/3kMOscdAgMBAAECggEADF/MmZzpJ6ATMpglyUbh+JpzG58MiYswFOf3m4W6HZa2
kF+GJoKJFPszXEI6VId3KM/+gn+HCek3Cer9X35V14KtxCILHPAXNQh38E2XndwS
58f9uKySb5+F1gSXUdOKGEWRrF+PVJq5oN00FsUQxjPFGZfZR+PCnoIotV45YHWm
tIa9AIg08itV7Yf9RV5R/BqV/t/hzLKBAlz3hAiM813cXjTwSzDlqsppoebQHhMO
lRPvpYpQdJkgKFebRQNKPg+j/b8W3UaObfH9V37X8QJm1v1LH/85m8hYihc5MTkc
/ITcYdbJmzgSknpj6WGBqcI2knXuxloOKPxVVI7y8QKBgQDifASbDfWimtiPUt0W
Po0nNxtfi1vAtid2IJCDz6KwfU7GTfrfGZYamAcQZWivLYHGQJAb2u5CPBYb6hIO
dVpWP5EmszZRxZsxrcK5qvLt9/O8l+SLZsh8UpjwGxf8LAdLzbWp05GFLYPXJed9
fpheDPZLtoC9ymesWcawLFMw9QKBgQC6z9gcnCtV9bZ5b5qnofuqdeF3Rrz/PsHo
9RTUg4ke0eHvYU0J8jCYK6S9ba2zEUFRmEUrNDAMCjcXUFEL+LKTySNGabEAMr8j
96Zk8jpjHcp6LUlxkK7oWS3atLYtewFgljHCy3iZYRn7nDWLrtDg1LjkkW7fJnh6
osfkzRLEiQKBgQC3WxHbecywDM5gEgS9GnzqD5oQmuD4Pj/qSWjV3YZnfbsFnmII
tk0oUIX/hyneEGhs2R4R/wc/BigcBz8BB47QHnxjqVjDkMgYywTHjZdIgqGHwCyd
kuOiirgYQscDN53ch7iXuZmpCPUgfCZSGeg+1B2dpC3L+Q4/oRrSy7+59QKBgBBI
6AzubDStG8AQQ4oTa83bQtFUAEu728mD+9HeuYhPQYPNlpqkWyoYu96rffXbLjd/
r5/ph7q09UJ6BOanQmHxqbqMohpjUhg/kWjBWOelBC6MXhehRi4JAB9Nm4fxbhhO
X34coKG2Pj6Zym0nyxueT5PVPbYEM4J1SDmgyt8JAoGBAMsFQwllB54IU9sY+z91
NZv925LtEplgq6FTZnxQbRsDUknCx1zJZ1DTzpRzyzcPfMpNMbPVwmn/bTZU5g5s
GAOdGC9LNDH5zTjriiIDaaX6tDjWueQi9r0gJ7T5tGL1NFSgYp9uXDNTx8Wcb5RF
09WLeGmqvwtyph/NgHxX8Z1N
-----END PRIVATE KEY-----""",
            "client_email": "service-account@whatsbroing.iam.gserviceaccount.com",
            "client_id": "104345141303948518924",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/service-account%40whatsbroing.iam.gserviceaccount.com",
        }
        SPREADSHEET_ID = "1mHpPfmV7AqDAs-UsYwHgl9pggBenCRpEfaPiM_-22Ws"
        return SERVICE_ACCOUNT_INFO, SPREADSHEET_ID

SERVICE_ACCOUNT_INFO, SPREADSHEET_ID = get_credentials()

# --------------------------------------------------------------------------------------
# Core logic (UI-independent)
# --------------------------------------------------------------------------------------

def compute_remaining(now: datetime, launch: datetime) -> timedelta:
    """Return non-negative remaining time until launch."""
    try:
        delta = launch - now
    except Exception:
        # Handle naive/aware mismatch by stripping tzinfo
        delta = (launch.replace(tzinfo=None) - now.replace(tzinfo=None))
    if delta.total_seconds() < 0:
        return timedelta(0)
    return delta


def breakdown_timedelta(td: timedelta) -> Tuple[int, int, int, int]:
    """Break a timedelta into (days, hours, minutes, seconds)."""
    days = td.days
    hours, rem = divmod(td.seconds, 3600)
    mins, secs = divmod(rem, 60)
    return days, hours, mins, secs


# --------------------------------------------------------------------------------------
# Google Sheets helper
# --------------------------------------------------------------------------------------

def append_to_gsheet(worksheet_title: str, row: List[str], header: List[str]) -> bool:
    """
    Append a row to a Google Sheet worksheet.
    Creates the worksheet if it doesn't exist and adds the header row.
    Returns True on success, False on failure.
    """
    if not GSHEETS_AVAILABLE:
        return False
    
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SPREADSHEET_ID)

        try:
            ws = sh.worksheet(worksheet_title)
        except gspread.exceptions.WorksheetNotFound:
            # Create worksheet with header if it doesn't exist
            ws = sh.add_worksheet(title=worksheet_title, rows="2000", cols=str(len(header)))
            ws.append_row(header, value_input_option="USER_ENTERED")

        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        print(f"GSHEET ERROR ({worksheet_title}): {e}")
        return False


# --------------------------------------------------------------------------------------
# Streamlit UI (only runs if streamlit is installed)
# --------------------------------------------------------------------------------------

def _countdown_box(html_container, value: int, label: str) -> None:
    html_container.markdown(
        f"""
        <div class='countdown-box'>
            <div class='cd-number'>{value:02d}</div>
            <div class='cd-label'>{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def run_streamlit_app() -> None:
    assert STREAMLIT_AVAILABLE, "Streamlit is not available in this environment."

    st.set_page_config(
        page_title=APP_NAME, 
        page_icon="☕", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Force light mode
    st.markdown("""
        <script>
        const root = window.parent.document.querySelector('.stApp');
        if (root) {
            root.classList.remove('dark-mode');
            root.style.colorScheme = 'light';
        }
        </script>
    """, unsafe_allow_html=True)

    # Modern, minimalistic styles - FORCE LIGHT MODE
    st.markdown(
        """
        <style>
        /* Import modern font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* CSS Variables for consistent theming */
        :root {
            --primary: #2D1810;
            --primary-light: #4A2E1F;
            --accent: #D4A574;
            --accent-light: #E8C4A0;
            --bg: #FEFEFE;
            --surface: #F8F6F4;
            --surface-elevated: #FFFFFF;
            --text: #1A1A1A;
            --text-secondary: #6B7280;
            --text-muted: #9CA3AF;
            --border: #E5E7EB;
            --border-light: #F3F4F6;
            --shadow: rgba(0, 0, 0, 0.04);
            --shadow-elevated: rgba(0, 0, 0, 0.08);
            --radius: 12px;
            --radius-lg: 16px;
        }
        
        /* CRITICAL: Force light mode on ALL elements */
        * {
            color-scheme: light !important;
        }
        
        body,
        html,
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        .main,
        .stApp,
        section[data-testid="stSidebar"] {
            background-color: #FEFEFE !important;
            background: #FEFEFE !important;
            color: #1A1A1A !important;
        }
        
        /* Reset and base styles */
        .main {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #FEFEFE !important;
            color: #1A1A1A !important;
        }
        
        /* Hide Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* Custom components */
        .hero {
            background: linear-gradient(135deg, var(--surface) 0%, var(--surface-elevated) 100%);
            padding: 3rem 2rem;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-light);
            text-align: center;
            margin-bottom: 3rem;
            box-shadow: 0 1px 3px var(--shadow);
        }
        
        .hero-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            background: var(--primary);
            color: white;
            border-radius: 100px;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 1.5rem;
            letter-spacing: 0.025em;
        }
        
        .hero-title {
            font-size: 2.5rem;
            font-weight: 600;
            color: var(--text);
            margin: 0 0 1rem 0;
            line-height: 1.2;
            text-align: center;
        }
        
        .hero-subtitle {
            font-size: 1.125rem;
            color: var(--text-secondary);
            margin: 0;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
            text-align: center;
        }
        
        /* Countdown styling */
        .countdown-container {
            background: var(--surface-elevated);
            padding: 2rem;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border);
            margin: 2rem 0;
            box-shadow: 0 2px 8px var(--shadow);
        }
        
        .countdown-box {
            background: var(--bg);
            border: 1px solid var(--border-light);
            border-radius: var(--radius);
            padding: 1.5rem;
            text-align: center;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px var(--shadow);
        }
        
        .countdown-box:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px var(--shadow-elevated);
        }
        
        .cd-number {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary);
            line-height: 1;
            margin-bottom: 0.5rem;
        }
        
        .cd-label {
            font-size: 0.875rem;
            color: var(--text-muted);
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        
        /* Section styling */
        .section {
            margin: 4rem 0;
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: var(--text);
            margin-bottom: 0.5rem;
        }
        
        .section-subtitle {
            color: var(--text-secondary);
            margin-bottom: 2rem;
        }
        
        /* Card styling */
        .card {
            background: var(--surface-elevated);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: 0 1px 3px var(--shadow);
            transition: all 0.2s ease;
            height: 100%;
        }
        
        .card:hover {
            box-shadow: 0 4px 12px var(--shadow-elevated);
            transform: translateY(-1px);
        }
        
        .role-card {
            background: var(--surface-elevated);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            text-align: center;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px var(--shadow);
        }
        
        .role-card:hover {
            box-shadow: 0 4px 12px var(--shadow-elevated);
            transform: translateY(-2px);
        }
        
        .role-title {
            font-weight: 600;
            color: var(--text);
            margin-bottom: 0.5rem;
        }
        
        .role-desc {
            color: var(--text-secondary);
            font-size: 0.875rem;
            line-height: 1.4;
        }
        
        /* Form styling - FORCE WHITE BACKGROUNDS AND DARK TEXT */
        .stTextInput input, 
        .stSelectbox select, 
        .stMultiSelect,
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select,
        .stMultiSelect > div > div,
        input, 
        select,
        textarea {
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            background: #FFFFFF !important;
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Force text color in form inputs */
        input::placeholder,
        select option,
        .stTextInput input::placeholder {
            color: #9CA3AF !important;
            opacity: 1 !important;
        }
        
        /* Dropdown options */
        option {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        
        /* Multi-select styling */
        .stMultiSelect > div > div {
            background-color: #FFFFFF !important;
            color: #1A1A1A !important;
        }
        
        .stMultiSelect span {
            color: #1A1A1A !important;
        }
        
        .stTextInput input:focus, .stSelectbox select:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(45, 24, 16, 0.1) !important;
        }
        
        .stButton button {
            background: var(--primary) !important;
            color: white !important;
            border: none !important;
            border-radius: var(--radius) !important;
            font-weight: 500 !important;
            padding: 0.75rem 2rem !important;
            font-family: 'Inter', sans-serif !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton button:hover {
            background: var(--primary-light) !important;
            transform: translateY(-1px) !important;
        }
        
        /* Form labels - ensure they're visible */
        label, 
        .stTextInput label,
        .stSelectbox label,
        .stMultiSelect label,
        [data-testid="stWidgetLabel"] {
            color: #1A1A1A !important;
            font-weight: 500 !important;
        }
        
        /* FAQ styling */
        .stExpander {
            border: 1px solid var(--border) !important;
            border-radius: var(--radius) !important;
            margin-bottom: 0.5rem !important;
            background: var(--surface-elevated) !important;
        }
        
        /* Success/Warning styling */
        .stSuccess {
            background: linear-gradient(90deg, #10B981, #059669) !important;
            border-radius: var(--radius) !important;
        }
        
        .stWarning {
            background: linear-gradient(90deg, #F59E0B, #D97706) !important;
            border-radius: var(--radius) !important;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem 0;
            color: var(--text-muted);
            font-size: 0.875rem;
            border-top: 1px solid var(--border-light);
            margin-top: 4rem;
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .hero {
                padding: 2rem 1rem;
            }
            .hero-title {
                font-size: 2rem;
            }
            .cd-number {
                font-size: 2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Hero Section
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">MVP Pilot</div>
            <h1 class="hero-title">☕ What's BROing 🤛 </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Live Countdown Section
    st.markdown('<div class="countdown-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title" style="text-align: center; margin-bottom: 2rem;">⏳ Countdown to Launch</h2>', unsafe_allow_html=True)

    # Countdown placeholder container
    ph = st.empty()

    # Show countdown for a few seconds, then continue with rest of app
    countdown_duration = 2  # Show countdown for 2 seconds
    started = time.time()

    while time.time() - started < countdown_duration:
        now = datetime.now(MADRID_TZ)
        remaining = compute_remaining(now, LAUNCH_TIME)
        d, h, m, s = breakdown_timedelta(remaining)

        with ph.container():
            c1, c2, c3, c4 = st.columns(4)
            with c1: _countdown_box(st, d, "Days")
            with c2: _countdown_box(st, h, "Hours")
            with c3: _countdown_box(st, m, "Minutes")
            with c4: _countdown_box(st, s, "Seconds")

        if d == h == m == s == 0:
            st.balloons()
            st.success("🎉 We're live! Time to grab coffee with someone new ☕")
            break
        time.sleep(1)
    
    # Final countdown display (static)
    now = datetime.now(MADRID_TZ)
    remaining = compute_remaining(now, LAUNCH_TIME)
    d, h, m, s = breakdown_timedelta(remaining)
    
    with ph.container():
        c1, c2, c3, c4 = st.columns(4)
        with c1: _countdown_box(st, d, "Days")
        with c2: _countdown_box(st, h, "Hours")
        with c3: _countdown_box(st, m, "Minutes")
        with c4: _countdown_box(st, s, "Seconds")

    st.markdown('</div>', unsafe_allow_html=True)

    # Early Access Section
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">📬 Join the Early Access List</h2>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Be among the first to experience meaningful coffee connections in Madrid.</p>', unsafe_allow_html=True)

    with st.form("signup", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name", placeholder="Enter your name")
        with col2:
            email = st.text_input("Email Address", placeholder="your.email@example.com")
        
        col3, col4, col5 = st.columns(3)
        with col3:
            role = st.selectbox("I am…", ["", "Student", "Young professional", "Digital nomad", "Tourist", "Other"])
        with col4:
            intent = st.multiselect("Looking for…", ["Make friends", "Professional networking", "Language exchange", "Explore cafés"])
        with col5:
            area = st.selectbox("Preferred area", ["", "Centro/Sol", "Chamberí", "Malasaña", "Salamanca", "Lavapiés", "Retiro", "Anywhere"])
        
        submitted = st.form_submit_button("Join the List 🚀", use_container_width=True)

        if submitted:
            if name.strip() and email.strip():
                row = [
                    datetime.now(MADRID_TZ).isoformat(timespec="seconds"),
                    name.strip(),
                    email.strip(),
                    role,
                    "|".join(intent),
                    area
                ]
                header = ["timestamp", "name", "email", "role", "intent", "area"]
                
                # Try Google Sheets first, fallback to CSV if it fails
                success = False
                if GSHEETS_AVAILABLE:
                    success = append_to_gsheet("Signups", row, header)
                    if success:
                        st.success("✨ Welcome aboard! We'll email you when we launch.")
                    else:
                        st.error("⚠️ Google Sheets connection failed. Saving locally...")
                
                if not success:
                    # Fallback to CSV if Google Sheets fails or unavailable
                    try:
                        path = Path("signups.csv")
                        is_new = not path.exists()
                        with path.open("a", newline="", encoding="utf-8") as f:
                            writer = csv.writer(f)
                            if is_new:
                                writer.writerow(header)
                            writer.writerow(row)
                        st.success("✨ Welcome aboard! We'll email you when we launch.")
                        st.info("ℹ️ Data saved locally. Google Sheets integration unavailable.")
                    except Exception as e:
                        st.error(f"❌ Failed to save signup: {str(e)}")
            else:
                st.warning("Please provide both your name and email address.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Crew Section
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">🛠️ Join Our Founding Crew</h2>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Help us build something meaningful. Flexible, part-time opportunities for passionate individuals.</p>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            '''
            <div class="role-card">
                <div class="role-title">UI/UX Design</div>
                <div class="role-desc">Onboarding flows, mobile prototypes, user experience optimization</div>
            </div>
            ''', 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            '''
            <div class="role-card">
                <div class="role-title">Development</div>
                <div class="role-desc">React Native, APIs, notifications, payment integration</div>
            </div>
            ''', 
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            '''
            <div class="role-card">
                <div class="role-title">Operations</div>
                <div class="role-desc">Café partnerships, event coordination, community management</div>
            </div>
            ''', 
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            '''
            <div class="role-card">
                <div class="role-title">Creative</div>
                <div class="role-desc">Brand assets, social content, marketing materials</div>
            </div>
            ''', 
            unsafe_allow_html=True
        )

    with st.expander("🙋‍♀️ Express Interest in Joining the Team"):
        with st.form("crew", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                your_name = st.text_input("Your Name", placeholder="Enter your name")
            with col2:
                your_email = st.text_input("Your Email", placeholder="your.email@example.com")
            
            skills = st.multiselect(
                "Your Skills & Interests",
                ["UI/UX Design", "React Native", "Web Development", "Backend/APIs", "Event Operations", "Design/Canva", "Growth/Community"]
            )
            hours = st.slider("Weekly Availability (hours)", 2, 20, 6)
            
            submit_crew = st.form_submit_button("Join the Crew ✋", use_container_width=True)
            
            if submit_crew:
                if your_name and your_email and skills:
                    row = [
                        datetime.now(MADRID_TZ).isoformat(timespec="seconds"),
                        your_name.strip(),
                        your_email.strip(),
                        "|".join(skills),
                        str(hours)
                    ]
                    header = ["timestamp", "name", "email", "skills", "hours"]
                    
                    # Try Google Sheets first, fallback to CSV if it fails
                    success = False
                    if GSHEETS_AVAILABLE:
                        success = append_to_gsheet("Crew Interest", row, header)
                        if success:
                            st.success("🎯 Thanks for your interest! We'll be in touch soon.")
                        else:
                            st.error("⚠️ Google Sheets connection failed. Saving locally...")
                    
                    if not success:
                        # Fallback to CSV
                        try:
                            path = Path("crew_interest.csv")
                            is_new = not path.exists()
                            with path.open("a", newline="", encoding="utf-8") as f:
                                w = csv.writer(f)
                                if is_new:
                                    w.writerow(header)
                                w.writerow(row)
                            st.success("🎯 Thanks for your interest! We'll be in touch soon.")
                            st.info("ℹ️ Data saved locally. Google Sheets integration unavailable.")
                        except Exception as e:
                            st.error(f"❌ Failed to save crew interest: {str(e)}")
                else:
                    st.warning("Please provide your name, email, and at least one skill area.")

    st.markdown('</div>', unsafe_allow_html=True)

    # FAQ Section
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">❓ Frequently Asked Questions</h2>', unsafe_allow_html=True)
    st.markdown('<p class="section-subtitle">Find answers to common questions or search for specific topics.</p>', unsafe_allow_html=True)

    query = st.text_input("🔍 Search FAQs", placeholder="e.g., fees, matching, safety, refunds...").strip().lower()

    faqs = [
        ("Is this a dating app?", "No — What's BROing is designed for friendly, professional, and social connections over coffee, not romantic dating."),
        ("How do the meetups work?", "Complete a short questionnaire → get matched by interests and preferences → confirm your attendance → meet at a partner café."),
        ("What does the event fee cover?", "Platform maintenance, coordination costs, café partnerships, and keeping no-shows to a minimum."),
        ("How big are the groups?", "We keep groups intimate — typically 3–5 people for better conversations."),
        ("Who can participate?", "Students, young professionals, digital nomads, tourists — anyone in Madrid looking for genuine connections."),
        ("Where do events happen?", "At carefully selected partner cafés across Madrid's best neighborhoods."),
        ("Can I choose my preferred area and time?", "Absolutely! You can specify your preferences in the questionnaire."),
        ("How does the matching algorithm work?", "We consider your interests, preferred location, available times, and group dynamics for optimal matches."),
        ("What if events are full?", "You'll be added to a waitlist and notified if spots become available."),
        ("What languages are supported?", "Primarily English and Spanish, with options for language exchange groups."),
        ("What's the cancellation policy?", "Full refund if you cancel at least 24 hours before the event."),
        ("What happens if someone doesn't show up?", "Repeated no-shows may result in suspended access to maintain group integrity."),
        ("Is it safe?", "Yes — we meet in public cafés, verify all RSVPs, and maintain small group sizes for comfort and security."),
        ("Do you accommodate accessibility needs?", "We prioritize accessible venues when accessibility requirements are noted during registration."),
        ("Do I have to buy something at the café?", "We encourage supporting our café partners with at least one purchase, but it's not mandatory."),
        ("Can I bring a friend?", "Friends are welcome, but each person must register separately to ensure proper matching."),
        ("How often are meetups held?", "We're starting with weekly events and will scale based on community demand."),
        ("How can cafés partner with you?", "Café owners can reach out through our crew interest form or contact us directly."),
        ("Is my personal data secure?", "Absolutely. We never sell your data and follow strict privacy guidelines."),
        ("How do payments work?", "Simple, secure payments through Stripe during our MVP phase."),
        ("What if I don't get matched for an event?", "You'll automatically be considered for the next suitable event that matches your preferences.")
    ]

    shown = 0
    for q, a in faqs:
        if not query or (query in q.lower() or query in a.lower()):
            with st.expander(q, expanded=False):
                st.write(a)
            shown += 1

    if shown == 0:
        st.info("🤔 No results found. Try a different keyword or clear your search.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown(
        f'''
        <div class="footer">
            © {datetime.now(MADRID_TZ).year} What's BROing — CoffeeConnect Madrid
        </div>
        ''',
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------------------
# CLI fallback (no Streamlit). Keeps the file runnable and testable in sandbox.
# --------------------------------------------------------------------------------------

def run_cli_fallback() -> None:
    print("Streamlit is not installed in this environment.\n")
    print("👉 To launch the full web app locally:")
    print("   pip install streamlit gspread google-auth\n   streamlit run app.py\n")

    now = datetime.now(MADRID_TZ)
    remaining = compute_remaining(now, LAUNCH_TIME)
    d, h, m, s = breakdown_timedelta(remaining)
    print("Countdown to launch (Madrid): {:02d} days {:02d}h {:02d}m {:02d}s".format(d, h, m, s))


# --------------------------------------------------------------------------------------
# Tests (unit tests for core countdown logic)
# --------------------------------------------------------------------------------------

class TestCountdownLogic(unittest.TestCase):
    def test_future_remaining_positive(self):
        tz = MADRID_TZ
        now = datetime(2025, 10, 1, 12, 0, 0, tzinfo=tz)
        launch = datetime(2025, 11, 1, 12, 0, 0, tzinfo=tz)
        td = compute_remaining(now, launch)
        # 31 days in October 2025; exactly 31 days diff
        self.assertEqual(td.days, 31)
        self.assertEqual(td.seconds, 0)

    def test_past_returns_zero(self):
        tz = MADRID_TZ
        now = datetime(2025, 11, 2, 12, 0, 0, tzinfo=tz)
        launch = datetime(2025, 11, 1, 12, 0, 0, tzinfo=tz)
        td = compute_remaining(now, launch)
        self.assertEqual(td, timedelta(0))

    def test_breakdown(self):
        td = timedelta(days=2, hours=5, minutes=7, seconds=9)
        d, h, m, s = breakdown_timedelta(td)
        self.assertEqual((d, h, m, s), (2, 5, 7, 9))


# Additional tests
class TestCountdownLogicAdditional(unittest.TestCase):
    def test_equal_returns_zero(self):
        tz = MADRID_TZ
        now = datetime(2025, 11, 1, 12, 0, 0, tzinfo=tz)
        launch = datetime(2025, 11, 1, 12, 0, 0, tzinfo=tz)
        td = compute_remaining(now, launch)
        self.assertEqual(td, timedelta(0))

    def test_naive_aware_mismatch(self):
        tz = MADRID_TZ
        # now naive, launch aware
        now = datetime(2025, 10, 1, 12, 0, 0)
        launch = datetime(2025, 11, 1, 12, 0, 0, tzinfo=tz)
        td = compute_remaining(now, launch)
        self.assertGreater(td.total_seconds(), 0)

    def test_breakdown_zero(self):
        td = timedelta(0)
        self.assertEqual(breakdown_timedelta(td), (0, 0, 0, 0))


# --------------------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------------------

if __name__ == "__main__":
    if "--test" in sys.argv:
        # Run tests only
        unittest.main(argv=[''], exit=False, verbosity=2)
    elif STREAMLIT_AVAILABLE:
        run_streamlit_app()
    else:
        run_cli_fallback()