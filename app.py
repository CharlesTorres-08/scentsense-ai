import streamlit as st
import os
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. LOAD CONFIGURATION
load_dotenv()  # This looks for your .env file locally

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")

# 2. VALIDATION CHECK
if not GEMINI_KEY or not WEATHER_KEY:
    st.error("🚨 API Keys are missing! Check your .env file or Streamlit Secrets.")
    st.stop()

# Initialize the Gemini Client
client = genai.Client(api_key=GEMINI_KEY)

# 3. WEATHER TOOL
def get_weather(city):
    """Fetches real-time weather from OpenWeatherMap"""
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

# 4. APP UI
st.set_page_config(
    page_title="ScentSense AI",
    page_icon="🧴",
    menu_items={
        'Get Help': 'https://github.com/CharlesTorres-08/scentsense-ai',
        'About': "# ScentSense AI\nThis agent recommends perfumes based on your local weather!"
    }
)

st.title("🧴 ScentSense AI")
st.caption("A Context-Aware Fragrance Selection Agent")
st.markdown("---")

# User Inputs
city = st.text_input("📍 Where are you right now?", placeholder="e.g., Lipa City, PH")
uploaded_files = st.file_uploader("📸 Upload photos of your perfumes", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

if st.button("🚀 Find My Scent", use_container_width=True):
    if not uploaded_files or not city:
        st.warning("Please provide both your city and at least one perfume photo!")
    else:
        with st.spinner("Agent is checking the weather and analyzing your shelf..."):
            # Step A: Get Weather
            temp, desc = get_weather(city)
            
            if temp is None:
                st.error(f"Weather Error: {desc}")
            else:
                try:
                    # Step B: Prepare Images for AI
                    image_parts = []
                    for uploaded_file in uploaded_files:
                        bytes_data = uploaded_file.getvalue()
                        image_parts.append(types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type))
                    
                    # Step C: The Agent's Logic
                    prompt = f"""
                    Current Weather in {city}: {temp}°C, {desc}.
                    
                    Identify the perfumes in these photos. 
                    Based on the current temperature of {temp}°C, recommend the best one to wear.
                    
                    Format your response clearly:
                    - **The Daily Pick:** [Name]
                    - **Scent Profile:** [Top notes]
                    - **Reasoning:** [Why it fits the current weather]
                    """
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=image_parts + [prompt]
                    )
                    
                    st.success(f"Weather in {city}: {temp}°C, {desc.capitalize()}")
                    st.markdown(response.text)
                
                except Exception as e:
                    if "429" in str(e):
                        st.error("🚦 Rate limit reached. Please wait 1 minute.")
                    elif "403" in str(e):
                        st.error("🔑 Permission Denied: Your API key might be leaked or invalid.")
                    else:
                        st.error(f"An error occurred: {e}")

st.info("💡 Tip: Clear labels help the AI identify your collection faster.")
