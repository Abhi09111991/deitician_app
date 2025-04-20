import pyotp
import streamlit as st
import pandas as pd
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import json
import bcrypt
import qrcode
from io import BytesIO

# ========== SESSION CONFIG ==========
st.set_page_config(layout="wide")
SESSION_TIMEOUT_MINUTES = 30

# ========== USER AUTHENTICATION ==========
def load_users():
    with open("diet_app_creation/users_app.json", "r") as f:
        return json.load(f)

st.markdown("""
     <style>
     h1, h2, h3 {
         color: white !important;
     }
     div[data-testid="stMarkdownContainer"] h1,
     div[data-testid="stMarkdownContainer"] h2,
     div[data-testid="stMarkdownContainer"] h3 {
         color: white !important;
     }
     .stApp h1, .stApp h2, .stApp h3 {
         color: white !important;
     }
     .stApp::before {
         content: '';
         position: absolute;
         top: 0;
         left: 0;
         right: 0;
         bottom: 0;
         background: rgba(0, 0, 0, 0.3);
         z-index: -1;
     }
     </style>
 """, unsafe_allow_html=True)

# Function to authenticate the username and password
def authenticate(username, password):
    users = load_users()
    if username in users:
        stored_pw = users[username]["password"]
        return bcrypt.checkpw(password.encode(), stored_pw.encode()), users[username]
    return False, None


def save_user_secret(username, secret_key):
    users = load_users()
    users[username]["secret_key"] = secret_key
    with open("diet_app_creation/users_app.json", "w") as f:
        json.dump(users, f, indent=4)

# Function to verify OTP
def verify_otp(secret_key, otp):
    totp = pyotp.TOTP(secret_key)
    return totp.verify(otp)

def login():
    # Session timeout check
    if "login_time" in st.session_state:
        now = datetime.datetime.now()
        if (now - st.session_state.login_time).seconds > SESSION_TIMEOUT_MINUTES * 60:
            st.warning("Session timed out. Please log in again.")
            for k in ["logged_in", "username", "role", "login_time", "otp_validated", "login_phase", "secret_key"]:
                st.session_state.pop(k, None)
            st.stop()

    if st.session_state.get("logged_in", False):
        return True

    st.subheader("Login")

    # Phase 1: Username + Password
    if "username" not in st.session_state:
        username = st.text_input("Username", key="username_input")
        password = st.text_input("Password", type="password", key="password_input")

        if st.button("Login"):
            valid, user_data = authenticate(username, password)
            if valid:
                st.session_state.username = username
                st.session_state.role = user_data["role"]
                st.session_state.secret_key = user_data.get("secret_key", None)

                # If no secret key exists, generate it and update user.json
                if not st.session_state.secret_key:
                    new_secret = pyotp.random_base32()
                    st.session_state.secret_key = new_secret
                    save_user_secret(username, new_secret)
                    st.session_state.show_qr = True  # flag to show QR only once
                else:
                    st.session_state.show_qr = False

                st.session_state.login_phase = "otp"
                st.rerun()
            else:
                st.error("Invalid username or password")
        st.stop()

    # Phase 2: OTP
    if st.session_state.get("login_phase") == "otp":
        if st.session_state.get("show_qr", False):
            st.info("Scan the QR code below in your authenticator app (only once).")
            totp = pyotp.TOTP(st.session_state.secret_key)
            uri = totp.provisioning_uri(name=st.session_state.username, issuer_name="DietTrackerApp")
            qr = qrcode.make(uri)
            buf = BytesIO()
            qr.save(buf)
            st.image(buf.getvalue(), caption="Scan this QR Code in Google Authenticator")

        otp = st.text_input("Enter OTP", type="password")

        if st.button("Verify OTP"):
            if verify_otp(st.session_state.secret_key, otp):
                st.success("OTP verified. Logging in...")
                st.session_state.logged_in = True
                st.session_state.login_time = datetime.datetime.now()
                st.rerun()
            else:
                st.error("Invalid OTP")
        st.stop()


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
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.error(f"Background image '{image_file}' not found. Please ensure it is in the same directory as the app.")


set_bg_from_local("diet_app_creation/vegetables-set-left-black-slate.jpg")


def main_app():
    # Consolidated CSS and JavaScript for styling
    st.sidebar.title("Menu")
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()
    # Title
    st.title("Diet Tracker App")

    # Description
    st.write("""
    Welcome to the Diet Tracker App! This app helps you track your daily activities, food consumption, and other parameters to help you meet your diet goals.
    """)

    # Calendar Selection (Date Picker)
    st.header("Select the Date")
    selected_date = st.date_input("Choose a date", datetime.date.today())
    st.write(f"You selected: {selected_date}")

    # User Input Section
    st.header("Enter Your Daily Information:")

    # Weight Input (kg)
    weight = st.number_input("Weight (kg)", min_value=30, max_value=300, value=70)

    # Sleep Hours and Minutes
    st.subheader("Sleep Hours")
    sleep_hours = st.number_input("Hours of Sleep", min_value=0, max_value=24, value=7)
    sleep_minutes = st.number_input("Minutes of Sleep", min_value=0, max_value=59, value=30)

    # Number of Cups of Coffee Consumed
    coffee_cups = st.slider("Number of cups of coffee consumed", 1, 10, 2)

    # Walking Distance in km
    walking_distance = st.number_input("Walking Distance (in km)", min_value=0.0, value=3.0)

    # Food Consumption at Different Times
    st.subheader("Breakfast (06:45 AM - 08:00 AM)")
    breakfast_food = st.text_area("Food Consumed (Breakfast)", placeholder="Enter foods consumed during breakfast")

    st.subheader("Snack or Light Meals (09:30 AM - 11:30 AM)")
    snack_food = st.text_area("Food Consumed (Snack)", placeholder="Enter foods consumed during snack or light meal")

    st.subheader("Lunch (12:30 PM - 02:30 PM)")
    lunch_food = st.text_area("Food Consumed (Lunch)", placeholder="Enter foods consumed during lunch")

    st.subheader("Evening Snack (05:30 PM)")
    evening_food = st.text_area("Food Consumed (Evening Snack)", placeholder="Enter foods consumed during evening snack")

    st.subheader("Dinner (07:00 PM - 08:00 PM)")
    dinner_food = st.text_area("Food Consumed (Dinner)", placeholder="Enter foods consumed during dinner")

    st.subheader("Before Bed Snack (09:00 PM - 10:30 PM)")
    bedtime_food = st.text_area("Food Consumed (Before Bed)", placeholder="Enter foods consumed before bed")

    # Google Sheets setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("diet_app_creation/creds.json", scope)
    client = gspread.authorize(creds)

    # Open your Google Sheet
    sheet = client.open("Diet_Tracker_Entries").worksheet("Entries")  # use .sheet1 if unnamed

    # Function to append data
    def store_data_to_gsheet(data_row):
        sheet.append_row(data_row)

    # Inside your submit logic
    if st.button("Submit"):
        st.write("Submitting your entry...")

        data_row = [
            str(selected_date),
            weight,
            sleep_hours,
            sleep_minutes,
            coffee_cups,
            walking_distance,
            breakfast_food,
            snack_food,
            lunch_food,
            evening_food,
            dinner_food,
            bedtime_food
        ]

        store_data_to_gsheet(data_row)
        st.success("Entry submitted successfully!")


def app():
    # Show login screen first
    if login():
        # Once logged in, show the main app
        main_app()

app()
