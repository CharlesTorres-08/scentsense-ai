import streamlit as st
from google import genai
from google.genai import types
import requests
import time

# --- 1. CONFIGURATION ---
# Replace these with your actual keys
GEMINI_KEY = "AIzaSyDXUKGDJTg0ToxhZ4R43zCts26weRlBR_0"
WEATHER_KEY = "0be015512b85b38a0369449f9a143c99"

# Initialize the Gemini Client
client = genai.Client(api_key=GEMINI_KEY)

# --- 2. TOOLS ---
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

# --- 3. THE APP UI ---
st.set_page_config(page_title="ScentSense AI", page_icon="🧴", layout="centered")

st.title("🧴 ScentSense AI Agent")
st.markdown("---")

# Input Section
col1, col2 = st.columns([1, 1])
with col1:
    city = st.text_input("📍 Your City", placeholder="e.g., Manila, PH")
with col2:
    uploaded_files = st.file_uploader("📸 Your Perfumes", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

st.markdown("---")

if st.button("🚀 Find My Scent", use_container_width=True):
    if not uploaded_files:
        st.warning("Please upload at least one photo of your collection!")
    elif not city:
        st.warning("Please enter a city name.")
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
                    
                    # Step C: Ask the Agent
                    prompt = f"""
                    Current Weather in {city}: {temp}°C, {desc}.
                    
                    I have uploaded {len(uploaded_files)} photos of my perfume collection. 
                    1. Identify the perfumes you see.
                    2. If the temperature is 25°C or higher, suggest the freshest, aquatic, or citrusy options. 
                    3. If it's below 25°C, suggest the warmest, sweetest, or woodiest ones.
                    
                    Format your response like this:
                    **The Daily Pick:** [Name of Perfume]
                    **Scent Profile:** [Notes found]
                    **Why Today?** [Reasoning based on weather]
                    """
                    
                    # Using the stable 2.5 Flash model
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=image_parts + [prompt]
                    )
                    
                    # Show Result
                    st.success(f"Weather in {city}: {temp}°C, {desc.capitalize()}")
                    st.markdown(response.text)
                
                except Exception as e:
                    # Handle Rate Limits (Error 429) gracefully
                    if "429" in str(e):
                        st.error("🚦 **AI Rate Limit Reached.** Please wait 60 seconds and try with just 1 or 2 photos. The free tier is currently busy!")
                    elif "404" in str(e):
                        st.error("📂 **Model Error.** Please double check if 'gemini-2.5-flash' is available in your region.")
                    else:
                        st.error(f"❌ **An Error Occurred:** {e}")

st.info("💡 Tip: Uploading clear photos of the labels helps the AI identify the scents better.")