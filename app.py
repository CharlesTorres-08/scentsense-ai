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
    "Prime Monkeys - Poseidon": "LV Pacific Chill",
    "Elite Fragrances - Azure": "Bleu De Chanel EDP",
    "Fragrance World - Suits" : "YSL Tuxedo",
    "AHMED - KAAF" : "PDM Percival",
    "Enzo Scents - BIRI" : "Valentino Born in Roma Intense",
    "Enzo Scents - Blue Talisman" : "Ex Nihilo Blue Talisman",
    "D'Matteos - DREAMCHASER" : "LV Imagination"
}

# 3. BACKGROUND FUNCTION WITH BALANCED CSS CONTRAST OVERRIDES
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
        
        /* Glassmorphism card wrappers */
        .stMarkdown, .stTextInput, .stCaption, .stExpander, div[data-testid="stFileUploader"] {{
            background-color: rgba(255, 255, 255, 0.92) !important;
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 12px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        }}
        
        /* 1. Target general structural texts */
        .stApp label, .stApp p, .stApp span {{
            color: #1A1A1A !important;
        }}
        
        /* 2. Target specific widget titles */
        div[data-testid="stWidgetLabel"] p {{
            color: #000000 !important;
            font-weight: 600 !important;
        }}
        
        /* 3. PROTECT FILE UPLOADER BUTTONS AND INTERNAL BLOCKS */
        div[data-testid="stFileUploaderDropzone"] {{
            background-color: #1E1E24 !important; /* Forces a stable dark background */
            border-radius: 8px;
        }}
        /* Keep all texts inside the drag-and-drop zone a light, bright grey */
        div[data-testid="stFileUploaderDropzone"] * {{
            color: #E0E0E0 !important;
        }}
        /* Ensure button icon explicitly uses light styling */
        div[data-testid="stFileUploaderDropzone"] svg {{
            fill: #FFFFFF !important;
        }}
        
        /* 4. Expander headers and layout blocks */
        .stExpander summary, .stExpander summary span, .stExpander summary p {{
            color: #000000 !important;
            font-weight: bold !important;
        }}
        
        div[data-testid="stExpanderDetails"] p, div[data-testid="stExpanderDetails"] {{
            color: #222222 !important;
            background-color: #FFFFFF !important;
        }}
        
        /* 5. Input text normalization */
        .stTextInput input {{
            color: #000000 !important;
            background-color: #FFFFFF !important;
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
st.set_page_config(
    page_title="ScentSense AI",
    page_icon=":material/air:" 
)
set_bg_from_url()

# Custom Header Section
st.markdown(
    """
    <div style='background-color: rgba(255, 255, 255, 0.95); padding: 20px; border-radius: 12px; margin-bottom: 20px; border-left: 5px solid #1A1A1A;'>
        <h1 style='color: #000000; margin: 0; font-size: 2.2rem; font-weight: 700;'>💨 ScentSense AI</h1>
        <p style='color: #444444; margin: 6px 0 0 0; font-size: 1.05rem; font-weight: 500;'>A Context-Aware Fragrance Selection Agent</p>
    </div>
    """, 
    unsafe_allow_html=True
)

city = st.text_input("📍 Where are you right now?", placeholder="e.g., Lipa City, PH")
uploaded_files = st.file_uploader("📸 Upload photos of your perfumes", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

if st.button("🚀 Find My Scent", use_container_width=True):
    if not uploaded_files or not city:
        st.warning("Please provide both your city and at least one perfume photo!")
    else:
        with st.spinner("Analyzing your fragrance collection..."):
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
                    Current Weather in {city}: {temp}°C, {desc}.
                    Local Scent Map: {PH_SCENT_MAP}

                    Analyze the uploaded perfume bottles. Identify all of them.
                    For PH local brands, reference the Map. Use Google Search grounding to verify notes.

                    For EVERY perfume bottle detected, you must output its details exactly using this block format:
                    ---PERFUME---
                    NAME: [Perfume Name]
                    VERDICT: [GOOD CHOICE or NOT RECOMMENDED]
                    PROFILE: [Scent notes or what it is inspired by]
                    REASON: [Short explanation why it fits or doesn't fit {temp}°C weather]
                    ---END---
                    """

                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=image_parts + [prompt],
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearchRetrieval())]
                        )
                    )
                    
                    st.success(f"Weather in {city}: {temp}°C, {desc.capitalize()}")
                    
                    st.markdown(f"<h3 style='color: #000000; margin-top: 15px; font-weight: 700;'>🔮 Your Fragrance Analysis Breakdown</h3>", unsafe_allow_html=True)
                    
                    # 6. LAYOUT BREAKDOWN PARSER
                    raw_text = response.text
                    raw_blocks = raw_text.split("---PERFUME---")
                    
                    detected_any = False
                    for block in raw_blocks:
                        if "---END---" in block:
                            detected_any = True
                            clean_block = block.split("---END---")[0].strip()
                            
                            name, verdict, profile, reason = "Unknown Scent", "N/A", "N/A", "N/A"
                            for line in clean_block.split("\n"):
                                if line.startswith("NAME:"):
                                    name = line.replace("NAME:", "").strip()
                                elif line.startswith("VERDICT:"):
                                    verdict = line.replace("VERDICT:", "").strip()
                                elif line.startswith("PROFILE:"):
                                    profile = line.replace("PROFILE:", "").strip()
                                elif line.startswith("REASON:"):
                                    reason = line.replace("REASON:", "").strip()
                            
                            status_badge = "🟢" if "GOOD" in verdict.upper() else "🚨"
                            
                            with st.expander(f"{status_badge} **{name}** — *{verdict}*"):
                                st.markdown(f"**Scent Profile:** {profile}")
                                st.markdown(f"**Weather Assessment:** {reason}")
                                
                    if not detected_any:
                        st.markdown(raw_text)
                            
                except Exception as e:
                    st.error(f"An error occurred while building the layout: {e}")

st.info("💡 Tip: Clear labels help the AI separate your collection into clean blocks faster.")
