import os
from dotenv import load_dotenv

# Load the keys from the .env file
load_dotenv()

# Get the keys
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")
if not GEMINI_KEY or not WEATHER_KEY:
    st.error("🚨 Keys missing! Check if your .env file has the right variable names.")
    st.stop()

# Now use these variables in your existing code
client = genai.Client(api_key=GEMINI_KEY)

import streamlit as st
from google import genai
from google.genai import types
import requests

# --- 1. SECURE CONFIGURATION ---
# This looks for your keys in the Streamlit Cloud "Secrets" vault
try:
    GEMINI_KEY = st.secrets["GEMINI_KEY"]
    WEATHER_KEY = st.secrets["WEATHER_KEY"]
except KeyError:
    st.error("API Keys not found! If running locally, check your .streamlit/secrets.toml file.")
    st.stop()

# Initialize Gemini
client = genai.Client(api_key=GEMINI_KEY)

# --- 2. TOOLS ---
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            return data['main']['temp'], data['weather'][0]['description']
        else:
            return None, data.get("message", "City not found")
    except Exception as e:
        return None, str(e)

# --- 3. THE APP UI ---
st.set_page_config(page_title="ScentSense AI", page_icon="🧴")

st.title("🧴 ScentSense AI")
st.caption("A Context-Aware Fragrance Selection Agent")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    city = st.text_input("📍 Your City", placeholder="e.g., Lipa City, PH")
with col2:
    uploaded_files = st.file_uploader("📸 Your Perfumes", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

if st.button("🚀 Find My Scent", use_container_width=True):
    if not uploaded_files or not city:
        st.warning("Please provide both a city and at least one photo!")
    else:
        with st.spinner("Agent is analyzing..."):
            temp, desc = get_weather(city)
            
            if temp is None:
                st.error(f"Weather Error: {desc}")
            else:
                try:
                    image_parts = []
                    for uploaded_file in uploaded_files:
                        bytes_data = uploaded_file.getvalue()
                        image_parts.append(types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type))
                    
                    prompt = f"""
                    Context: The weather in {city} is {temp}°C with {desc}.
                    Task: Identify these perfumes and pick the best one for this weather.
                    Provide the name, scent notes, and a logical reason for the pick.
                    """
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=image_parts + [prompt]
                    )
                    
                    st.success(f"Weather: {temp}°C, {desc.capitalize()}")
                    st.markdown(response.text)
                
                except Exception as e:
                    if "429" in str(e):
                        st.error("🚦 AI is busy! Wait 60 seconds and try again.")
                    else:
                        st.error(f"Error: {e}")
