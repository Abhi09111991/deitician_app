import os
import streamlit as st
import pandas as pd
import base64

# ========== Authentication ==========
st.set_page_config(layout="wide")
st.title("Doctor Login")

password_correct = False
DOCTOR_PASSWORD = os.getenv("DOCTOR_PASSWORD", "secure123")  # For production, set as env variable

with st.form("doctor_login"):
    entered_password = st.text_input("Enter doctor password:", type="password")
    login_btn = st.form_submit_button("Login")

    if login_btn:
        if entered_password == DOCTOR_PASSWORD:
            st.success("Access granted.")
            password_correct = True
        else:
            st.error("Incorrect password.")

if not password_correct:
    st.stop()

# ========== STYLING ==========
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
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const headings = document.querySelectorAll('h1, h2, h3');
        headings.forEach(heading => {
            heading.style.color = 'white';
        });
    });
    </script>
""", unsafe_allow_html=True)


#========== BACKGROUND IMAGE ==========
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

# ========== TITLE ==========
st.title("Doctor's View - Patient Diet Summary")

# ========== LOAD DATA ==========
try:
    df = pd.read_csv("user_entries.csv")
    df["Date"] = pd.to_datetime(df["Date"]).dt.date  # Ensure date format
    available_dates = df["Date"].unique()

    selected_date = st.selectbox("Select a date to view patient's data:", sorted(available_dates, reverse=True))
    selected_entry = df[df["Date"] == selected_date].iloc[-1]  # Get the latest entry for the selected date

    # ========== DISPLAY PATIENT DATA ==========
    st.markdown(f"<h3>Summary for {selected_date}</h3>", unsafe_allow_html=True)
    st.write(f"**Weight**: {selected_entry['Weight (kg)']} kg")
    st.write(
        f"**Sleep**: {int(selected_entry['Sleep Hours'])} hours and {int(selected_entry['Sleep Minutes'])} minutes")
    st.write(f"**Coffee Consumed**: {int(selected_entry['Coffee Cups'])} cups")
    st.write(f"**Walking Distance**: {selected_entry['Walking Distance (km)']} km")

    st.markdown("#### Food Consumption Summary:")
    st.write(f"**Breakfast (06:45 AM - 08:00 AM)**: {selected_entry['Breakfast']}")
    st.write(f"**Snack or Light Meals (09:30 AM - 11:30 AM)**: {selected_entry['Snack']}")
    st.write(f"**Lunch (12:30 PM - 02:30 PM)**: {selected_entry['Lunch']}")
    st.write(f"**Evening Snack (05:30 PM)**: {selected_entry['Evening Snack']}")
    st.write(f"**Dinner (07:00 PM - 08:00 PM)**: {selected_entry['Dinner']}")
    st.write(f"**Before Bed Snack (09:00 PM - 10:30 PM)**: {selected_entry['Before Bed Snack']}")

except FileNotFoundError:
    st.error("No data found. Please make sure the user has submitted at least one entry.")
except Exception as e:
    st.error(f"An error occurred while loading the data: {e}")
