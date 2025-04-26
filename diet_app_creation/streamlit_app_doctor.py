import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import base64
import datetime
import json
import bcrypt
import pyotp
import qrcode
from io import BytesIO

# ========== PAGE CONFIG ==========
st.set_page_config(layout="wide")

# ========== CONSTANTS ==========
SESSION_TIMEOUT_MINUTES = 30

# ========== LOAD USERS ==========
def load_doctor_users():
    return dict(st.secrets["users_doctor"])

# ========== SESSION TIMEOUT ==========
def check_doctor_session_timeout():
    if "doctor_logged_in" in st.session_state:
        login_time = st.session_state.get("login_time")
        if login_time and (datetime.datetime.now() - login_time).seconds > SESSION_TIMEOUT_MINUTES * 60:
            st.session_state["doctor_logged_in"] = False
            st.session_state["login_time"] = None
            st.warning("Your session has expired. Please log in again.")
            st.stop()

# ========== OTP VERIFICATION ==========
def verify_otp(secret, otp):
    totp = pyotp.TOTP(secret)
    return totp.verify(otp)

# ========== SET BACKGROUND ==========
# def set_bg_from_local(image_file):
#     try:
#         with open(image_file, "rb") as img_file:
#             encoded_string = base64.b64encode(img_file.read()).decode()
#         st.markdown(
#             f"""
#             <style>
#             .stApp {{
#                 background-image: url("data:image/png;base64,{encoded_string}");
#                 background-size: cover;
#                 background-position: center;
#             }}
#             </style>
#             """,
#             unsafe_allow_html=True
#         )
#     except FileNotFoundError:
#         st.error(f"Background image '{image_file}' not found. Please ensure it is in the same directory as the app.")

def set_bg_from_local(image_file):
    try:
        with open(image_file, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                background-color: #333333 !important; /* Fallback */
            }}
            /* Headers and markdown text */
            h1, h2, h3, h4, h5, h6, .stMarkdown p, .stMarkdown div {{
                color: white !important;
            }}
            /* Input fields */
            div.stTextInput > div > input {{
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 1px solid #cccccc !important;
                border-radius: 4px !important;
                padding: 8px !important;
            }}
            /* Input labels */
            div.stTextInput > label, div.stSelectbox > label {{
                color: white !important;
                font-weight: bold !important;
            }}
            /* Primary buttons (e.g., Login, Verify OTP) */
            div.stButton > button[kind="primary"] {{
                background-color: #1f77b4 !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 10px 20px !important;
                font-size: 16px !important;
                font-weight: bold !important;
            }}
            div.stButton > button[kind="primary"]:hover {{
                background-color: #0056b3 !important;
                color: #ffffff !important;
            }}
            /* Secondary buttons (e.g., Sidebar Logout) */
            div.stButton > button:not([kind="primary"]) {{
                background-color: #d9d9d9 !important;
                color: #333333 !important;
                border: none !important;
                border-radius: 8px !important;
                padding: 10px 20px !important;
                font-size: 16px !important;
                font-weight: bold !important;
            }}
            div.stButton > button:not([kind="primary"]):hover {{
                background-color: #bfbfbf !important;
                color: #333333 !important;
            }}
            /* Selectbox (dropdown) */
            div[data-baseweb="select"] > div {{
                background-color: #ffffff !important;
                color: #000000 !important;
                border: 1px solid #cccccc !important;
                border-radius: 4px !important;
                padding: 8px !important;
            }}
            div[data-baseweb="select"] span, div[data-baseweb="select"] div, div[data-baseweb="select"] li {{
                color: #000000 !important;
                background-color: #ffffff !important;
            }}
            /* Dropdown arrow */
            div[data-baseweb="select"] > div::after {{
                border-color: #000000 !important;
            }}
            /* Placeholder text */
            input::placeholder {{
                color: #666666 !important;
                opacity: 1 !important;
            }}
            /* Sidebar background */
            section[data-testid="stSidebar"] {{
                background-color: rgba(0, 0, 0, 0.7) !important;
            }}
            /* Mobile responsiveness */
            @media (max-width: 768px) {{
                .stApp {{
                    background-size: cover !important;
                    background-position: center top !important;
                    background-repeat: no-repeat !important;
                }}
                div.stTextInput > div > input, div.stButton > button, div[data-baseweb="select"] > div {{
                    font-size: 18px !important;
                    padding: 10px !important;
                }}
                div.stTextInput > label, div.stSelectbox > label {{
                    font-size: 16px !important;
                }}
                div.stButton > button {{
                    width: 100% !important;
                    margin-bottom: 10px !important;
                }}
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.error(f"Background image '{image_file}' not found.")

set_bg_from_local("diet_app_creation/vegetables-set-left-black-slate.jpg")

# ========== DOCTOR LOGIN ==========
def doctor_login(users):
    if st.session_state.get("doctor_logged_in", False):
        return True

    st.subheader("Doctor Login")

    doctor_username = st.text_input("Username")
    doctor_password = st.text_input("Password", type="password")

    if st.button("Login"):
        if doctor_username in users:
            user = users[doctor_username]
            if user['role'] == 'doctor' and bcrypt.checkpw(doctor_password.encode('utf-8'), user['password'].encode('utf-8')):
                st.session_state["doctor_username"] = doctor_username
                st.session_state["otp_secret"] = user["otp_secret"]
                st.session_state["show_qr"] = False  # Already provisioned outside

                st.success("Password verified. Enter OTP to continue.")
                st.session_state["password_verified"] = True
                st.rerun()
            else:
                st.error("Invalid username or password.")
        else:
            st.error("Username does not exist.")
    st.stop()

# ========== GOOGLE SHEETS AUTH ==========
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
        "universe_domain": st.secrets["gcp_service_account"]["universe_domain"]
    }

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def get_user_data():
    client = authenticate_google_sheets()
    sheet = client.open("Diet_Tracker_Entries").worksheet("Entries")
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    return df

# ========== MAIN DOCTOR VIEW ==========
def doctor_view():
    st.sidebar.title("Menu")
    if st.sidebar.button("Logout"):
        st.session_state["doctor_logged_in"] = False
        for k in ["doctor_username", "otp_secret", "password_verified", "login_time"]:
            st.session_state.pop(k, None)
        st.rerun()

    st.title("Doctor's View - Patient Diet Summary")
    check_doctor_session_timeout()

    try:
        df = get_user_data()
        df["Date"] = pd.to_datetime(df["Date"]).dt.date
        available_dates = df["Date"].unique()
        selected_date = st.selectbox("Select a date to view patient's data:", sorted(available_dates, reverse=True))

        selected_entry = df[df["Date"] == selected_date].iloc[-1]

        st.markdown(f"<h3>Summary for {selected_date}</h3>", unsafe_allow_html=True)
        st.write(f"**Weight**: {selected_entry['Weight']} kg")
        st.write(f"**Sleep**: {int(selected_entry['Hours'])} hours and {int(selected_entry['Minutes'])} minutes")
        st.write(f"**Coffee Consumed**: {int(selected_entry['coffee_cups'])} cups")
        st.write(f"**Walking Distance**: {selected_entry['walking_distance']} km")

        st.markdown("#### Food Consumption Summary:")
        st.write(f"**Breakfast**: {selected_entry['breakfast_food']}")
        st.write(f"**Snack**: {selected_entry['snack_food']}")
        st.write(f"**Lunch**: {selected_entry['lunch_food']}")
        st.write(f"**Evening Snack**: {selected_entry['evening_food']}")
        st.write(f"**Dinner**: {selected_entry['dinner_food']}")
        st.write(f"**Before Bed**: {selected_entry['bedtime_food']}")

    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")

# ========== ENTRY POINT ==========
def app():
    users = load_doctor_users()

    if not st.session_state.get("doctor_logged_in", False):
        if not st.session_state.get("password_verified", False):
            doctor_login(users)

        st.subheader("Two-Factor Authentication (2FA)")
        otp = st.text_input("Enter OTP", type="password")

        if st.button("Verify OTP"):
            if verify_otp(st.session_state["otp_secret"], otp):
                st.success("OTP verified. Logging in...")
                st.session_state["doctor_logged_in"] = True
                st.session_state["login_time"] = datetime.datetime.now()
                st.rerun()
            else:
                st.error("Invalid OTP. Try again.")
        st.stop()

    doctor_view()

app()
