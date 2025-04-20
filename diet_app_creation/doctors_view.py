import os
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
import io

# ========== PAGE CONFIG ==========
st.set_page_config(layout="wide")

# ========== LOAD USER DATA ==========
def load_users():
    with open("diet_app_creation/users_doctor.json", "r") as f:
        return json.load(f)

# ========== SESSION TIMEOUT ==========
def check_doctor_session_timeout():
    if "doctor_logged_in" in st.session_state:
        login_time = st.session_state.get("login_time")
        if login_time and (datetime.datetime.now() - login_time).seconds > 1800:
            st.session_state["doctor_logged_in"] = False
            st.session_state["login_time"] = None
            st.warning("Your session has expired. Please log in again.")
            st.stop()

# ========== VERIFY OTP ==========
def verify_otp(otp, secret):
    totp = pyotp.TOTP(secret)
    return totp.verify(otp)

# ========== BACKGROUND IMAGE ==========
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
        st.error(f"Background image '{image_file}' not found.")

set_bg_from_local("diet_app_creation/vegetables-set-left-black-slate.jpg")

# ========== LOGIN FUNCTION ==========
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
                st.session_state["login_time"] = datetime.datetime.now()
                st.success("Password verified successfully. Please enter the OTP.")

                # Handle OTP secret setup
                if not user.get("otp_secret"):
                    new_secret = pyotp.random_base32()
                    st.session_state["otp_secret"] = new_secret
                    user["otp_secret"] = new_secret
                    with open("diet_app_creation/users_doctor.json", "w") as f:
                        json.dump(users, f, indent=4)
                    st.session_state["show_qr"] = True
                else:
                    st.session_state["otp_secret"] = user["otp_secret"]
                    st.session_state["show_qr"] = False

                return False
            else:
                st.error("Invalid username or password for doctor.")
        else:
            st.error("Username does not exist.")
    return False

# ========== GOOGLE SHEETS AUTH ==========
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("diet_app_creation/creds.json", scope)
    client = gspread.authorize(creds)
    return client

def get_user_data():
    client = authenticate_google_sheets()
    sheet = client.open("Diet_Tracker_Entries").sheet1
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    return df

# ========== SESSION STATE INIT ==========
if "doctor_logged_in" not in st.session_state:
    st.session_state["doctor_logged_in"] = False

# ========== LOGIN FLOW ==========
if not st.session_state["doctor_logged_in"]:
    users = load_users()
    doctor_logged_in = doctor_login(users)

    if not doctor_logged_in:
        if "otp_secret" in st.session_state:
            if st.session_state.get("show_qr", False):
                st.markdown("### Scan this QR Code in your Authenticator App (Google Auth, Authy, etc.)")
                uri = pyotp.TOTP(st.session_state["otp_secret"]).provisioning_uri(
                    name=st.session_state["doctor_username"], issuer_name="Diet Tracker App"
                )
                img = qrcode.make(uri)
                buf = io.BytesIO()
                img.save(buf)
                st.image(buf.getvalue())

            st.markdown("### Two-Factor Authentication (2FA)")
            entered_otp = st.text_input("Enter the OTP", type="password")

            if st.button("Verify OTP"):
                if verify_otp(entered_otp, st.session_state["otp_secret"]):
                    st.session_state["doctor_logged_in"] = True
                    st.session_state["login_time"] = datetime.datetime.now()
                    st.success("OTP verified successfully!")
                    st.rerun()
                else:
                    st.error("Invalid OTP. Please try again.")
    st.stop()

# ========== LOGOUT ==========
st.sidebar.title("Menu")
if st.sidebar.button("Logout"):
    st.session_state["doctor_logged_in"] = False
    st.rerun()

# ========== MAIN DOCTOR VIEW ==========
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

except FileNotFoundError:
    st.error("No data found. Please make sure the user has submitted at least one entry.")
except Exception as e:
    st.error(f"An error occurred while loading the data: {e}")
