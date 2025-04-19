import streamlit as st
import pandas as pd
import base64
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# Example username and password (you can make this more secure later)
USERNAME = "diet09111991"
PASSWORD = "test123"

# Function for Login
def login():
    # Add login form
    st.subheader("Please log in to continue")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.success("Login successful!")
            return True  # Return True if login is successful
        else:
            st.error("Invalid username or password")
            return False  # Return False if login fails

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

def main_app():
    # Consolidated CSS and JavaScript for styling
    st.markdown("""
        <style>
        /* Broad selectors for headings */
        h1, h2, h3 {
            color: white !important;
        }
        /* Streamlit-specific markdown containers */
        div[data-testid="stMarkdownContainer"] h1,
        div[data-testid="stMarkdownContainer"] h2,
        div[data-testid="stMarkdownContainer"] h3 {
            color: white !important;
        }
        /* Main app container */
        .stApp h1, .stApp h2, .stApp h3 {
            color: white !important;
        }
        /* Date input styling */
        input[type="date"] {
            color: white !important;
            background-color: black !important;
            -webkit-text-fill-color: white !important;
        }
        .stDateInput > div > div {
            color: white !important;
        }
        /* Optional: Semi-transparent overlay for better text contrast */
        .stApp::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.3); /* Adjust opacity as needed */
            z-index: -1;
        }
        /* Debug: Red border to confirm CSS injection */
        .stApp {
            border: 2px solid red !important;
        }
        </style>
        <script>
        // JavaScript fallback for headings
        document.addEventListener('DOMContentLoaded', function() {
            const headings = document.querySelectorAll('h1, h2, h3');
            headings.forEach(heading => {
                heading.style.color = 'white';
            });
        });
        </script>
    """, unsafe_allow_html=True)

    # Set background image with error handling
    set_bg_from_local("diet_app_creation/vegetables-set-left-black-slate.jpg")

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

    # Function to store data in a CSV file
    # def store_data(selected_date, weight, sleep_hours, sleep_minutes, coffee_cups, walking_distance, breakfast_food,
    #                snack_food, lunch_food, evening_food, dinner_food, bedtime_food):
    #     data = {
    #         "Date": [selected_date],
    #         "Weight (kg)": [weight],
    #         "Sleep Hours": [sleep_hours],
    #         "Sleep Minutes": [sleep_minutes],
    #         "Coffee Cups": [coffee_cups],
    #         "Walking Distance (km)": [walking_distance],
    #         "Breakfast": [breakfast_food],
    #         "Snack": [snack_food],
    #         "Lunch": [lunch_food],
    #         "Evening Snack": [evening_food],
    #         "Dinner": [dinner_food],
    #         "Before Bed Snack": [bedtime_food]
    #     }
    #     df = pd.DataFrame(data)
    #     try:
    #         existing_df = pd.read_csv("user_entries.csv")
    #         updated_df = pd.concat([existing_df, df], ignore_index=True)
    #         updated_df.to_csv("user_entries.csv", index=False)
    #     except FileNotFoundError:
    #         df.to_csv("user_entries.csv", index=False)

    # # Submit Button
    # if st.button("Submit"):
    #     st.write(f"### Summary for {selected_date}")
    #     st.write(f"**Weight**: {weight} kg")
    #     st.write(f"**Sleep**: {sleep_hours} hours and {sleep_minutes} minutes")
    #     st.write(f"**Coffee Consumed**: {coffee_cups} cups")
    #     st.write(f"**Walking Distance**: {walking_distance} km")
    #     st.write(f"#### Food Consumption Summary:")
    #     st.write(f"**Breakfast**: {breakfast_food}")
    #     st.write(f"**Snack/Light Meals**: {snack_food}")
    #     st.write(f"**Lunch**: {lunch_food}")
    #     st.write(f"**Evening Snack**: {evening_food}")
    #     st.write(f"**Dinner**: {dinner_food}")
    #     st.write(f"**Before Bed Snack**: {bedtime_food}")
    #     store_data(selected_date, weight, sleep_hours, sleep_minutes, coffee_cups, walking_distance, breakfast_food,
    #                snack_food, lunch_food, evening_food, dinner_food, bedtime_food)
    #

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
            str(datetime.date.today()),
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