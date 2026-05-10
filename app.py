import streamlit as st
import os
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. LOAD CONFIGURATION
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")

if not GEMINI_KEY or not WEATHER_KEY:
    st.error("🚨 API Keys are missing! Check your .env file or Streamlit Secrets.")
    st.stop()

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_KEY)

# 2. LOCAL BRAND KNOWLEDGE BASE
PH_SCENT_MAP = {
    "Cotidiano - Silver": "Gentle Fluidity Silver (Fresh, Metallic, Gin)",
    "Cotidiano - Mango Venom": "God of Fire (Mango, Tropical, Sweet)",
    "Cotidiano - D'Iconic": "Bleu de Chanel EDP",
    "Symmetry Labs - Sronger Flame": "Stronger with You Intensely",
    "Symmetry Labs - Diver": "LV Afternoon Swim (Mandarin, Orange, Bright)",
    "Father and Son - Achilles": "Stronger with You Intensely",
    "Father and Son - Debonair": "JPG Le Male Elixir (Sweet, Honey, Tobacco)",
    "HSI - Motivational": "Fresh, Uplifting, Green (Signature Blend)",
    "Prime Monkeys - Poseidon": "LV Pacific Chill",
    "Elite Fragrances - Azure": "Bleu De Chanel EDP",
    "Fragrance World - Suits" : "YSL Tuxedo",
    "AHMED - KAAF" : "PDM Percival"
}

# 3. BACKGROUND FUNCTION (Pinterest URL)
def set_bg_from_url():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("https://i.pinimg.com/736x/2c/09/04/2c0904aed6688401670f8921b29af288.jpg");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        /* Make text more readable against the image */
        .stMarkdown, .stTextInput, .stCaption {{
            background-color: rgba(255, 255, 255, 0.4);
            padding: 10px;
            border-radius: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 4. WEATHER TOOL
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

# 5. APP UI
st.set_page_config(page_title="ScentSense AI", page_icon="🏺")
set_bg_from_url()

st.title("🧴 ScentSense AI")
st.caption("A Context-Aware Fragrance Selection Agent")
st.markdown("---")

city = st.text_input("📍 Where are you right now?", placeholder="e.g., Lipa City, PH")
uploaded_files = st.file_uploader("📸 Upload photos of your perfumes", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

if st.button("🚀 Find My Scent", use_container_width=True):
    if not uploaded_files or not city:
        st.warning("Please provide both your city and at least one perfume photo!")
    else:
        with st.spinner("Analyzing your shelf..."):
            temp, desc = get_weather(city)
            if temp is None:
                st.error(f"Weather Error: {desc}")
            else:
                try:
                    image_parts = []
                    for uploaded_file in uploaded_files:
                        bytes_data = uploaded_file.getvalue()
                        image_parts.append(types.Part.from_bytes(data=bytes_data, mime_type=uploaded_file.type))

                    # Logic prompt
                    prompt = f"""
                    Current Weather in {city}: {temp}°C, {desc}.
                    Local Scent Map: {PH_SCENT_MAP}

                    1. Identify the perfumes. For PH local brands, use the Map above.
                    2. If a brand isn't in the Map, USE GOOGLE SEARCH to find notes from TikTok or Shopee.
                    3. Recommend the best one for {temp}°C weather.

                    Format:
                    - **Detected:** [Name]
                    - **Scent Profile:** [Notes]
                    - **Recommendation:** [Why it fits today]
                    """

                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=image_parts + [prompt],
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearchRetrieval())]
                        )
                    )
                    
                    st.success(f"Weather in {city}: {temp}°C, {desc.capitalize()}")
                    st.markdown(response.text)
                
                except Exception as e:
                    st.error(f"An error occurred: {e}")

st.info("💡 Tip: Clear labels help the AI identify your collection faster.")
