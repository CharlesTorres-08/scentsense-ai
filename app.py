import streamlit as st
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
import streamlit.components.v1 as components

# 1. LOAD CONFIGURATION
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")

if not GEMINI_KEY or not WEATHER_KEY:
    st.error("🚨 API Keys are missing! Check your .env file or Streamlit Secrets.")
    st.stop()

# Initialize Gemini Client
client = genai.Client(api_key=GEMINI_KEY)

# Initialize Session State Memory
if "scent_history" not in st.session_state:
    st.session_state.scent_history = []
if "active_analysis" not in st.session_state:
    st.session_state.active_analysis = None
if "weather_info" not in st.session_state:
    st.session_state.weather_info = None

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

# 3. BACKGROUND FUNCTION
def set_bg_from_url():
    st.markdown(
        """
        <style>
        .stApp {
            background-image: url("https://i.pinimg.com/736x/2c/09/04/2c0904aed6688401670f8921b29af288.jpg");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }
        
        .stTextInput, .stSelectbox, div[data-testid="stFileUploader"] {
            background-color: rgba(255, 255, 255, 0.9) !important;
            padding: 14px;
            border-radius: 12px;
            margin-bottom: 12px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.15);
        }
        
        div[data-testid="stWidgetLabel"] p, label p {
            color: #000000 !important;
            font-weight: bold !important;
        }
        
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }

        div[data-testid="stFileUploaderDropzone"] {
            background-color: #1E1E24 !important;
            border-radius: 8px;
        }
        div[data-testid="stFileUploaderDropzone"] * {
            color: #E0E0E0 !important;
        }
        div[data-testid="stFileUploaderDropzone"] svg {
            fill: #FFFFFF !important;
        }
        
        .stExpander {
            background-color: #1E1E24 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            margin-bottom: 10px;
        }
        .stExpander summary, .stExpander summary span, .stExpander summary p {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }
        
        div[data-testid="stExpanderDetails"] {
            background-color: #121214 !important;
            padding: 15px !important;
        }
        div[data-testid="stExpanderDetails"] p, div[data-testid="stExpanderDetails"] strong {
            color: #FFFFFF !important;
        }
        
        section[data-testid="stSidebar"] {
            background-color: rgba(20, 20, 25, 0.95) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .stButton button {
            background-color: #1E1E24 !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# 4. WEATHER TOOL
def get_weather(city_name):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city_name, "appid": WEATHER_KEY, "units": "metric"}
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        if response.status_code == 200:
            return data['main']['temp'], data['weather'][0]['description']
        return None, data.get("message", "City not found")
    except Exception as e:
        return None, str(e)

# 5. APP UI LAYOUT SETUP
st.set_page_config(page_title="ScentSense AI", page_icon=":material/air:", layout="wide")
set_bg_from_url()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 📜 Scent History")
    if not st.session_state.scent_history:
        st.info("No recommendations saved yet.")
    else:
        for item in reversed(st.session_state.scent_history):
            st.markdown(f"**🌟 {item['perfume']}**")
            st.caption(f"📅 {item['date']} | 🎯 {item['occasion']}")
            st.markdown(f"*{item['verdict']}*")
            st.markdown("---")
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.scent_history, st.session_state.active_analysis, st.session_state.weather_info = [], None, None
            st.rerun()

# --- MAIN COLUMNS ---
main_col, perfume_col = st.columns([3.2, 1.2], gap="large")

with main_col:
    st.markdown(
        """
        <div style='background-color: rgba(15, 15, 20, 0.85); backdrop-filter: blur(10px); padding: 22px; border-radius: 12px; margin-bottom: 25px; border: 1px solid rgba(255, 255, 255, 0.1);'>
            <h1 style='color: #FFFFFF; margin: 0; font-size: 2.3rem; font-weight: 700;'>💨 ScentSense AI</h1>
            <p style='color: #CCCCCC; margin: 6px 0 0 0; font-size: 1.05rem;'>A Context-Aware Fragrance Selection Agent</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

    city = st.text_input("📍 Where are you right now?", placeholder="e.g., Lipa City, PH")
    occasion = st.selectbox("🎯 What is the occasion/vibe for today?", ["Casual / Daily Wear", "Office / School / Professional", "Date Night / Romantic", "Gym / Sports / Activewear", "Formal Event / Wedding"])
    uploaded_files = st.file_uploader("📸 Upload photos of your perfumes", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

    if st.button("🚀 Find My Scent", use_container_width=True):
        if not uploaded_files or not city:
            st.warning("Please provide both your city and at least one perfume photo!")
        else:
            with st.spinner("Analyzing your fragrance collection..."):
                temp, desc = get_weather(city)
                if temp is not None:
                    try:
                        image_parts = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in uploaded_files]
                        prompt = f"Weather: {temp}C, {desc}. Occasion: {occasion}. Dictionary: {PH_SCENT_MAP}. Identify all bottles. Format: ---PERFUME--- NAME: [Name] VERDICT: [GOOD CHOICE/NOT RECOMMENDED] PROFILE: [Profile] REASON: [Why] ---END---"
                        response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=image_parts + [prompt])
                        
                        st.session_state.weather_info = f"Weather in {city}: {temp}°C, {desc.capitalize()}"
                        parsed_perfumes = []
                        for block in response.text.split("---PERFUME---"):
                            if "---END---" in block:
                                clean_block = block.split("---END---")[0].strip()
                                name, verdict, profile, reason = "Unknown Scent", "N/A", "N/A", "N/A"
                                for line in clean_block.split("\n"):
                                    if line.strip().startswith("NAME:"): name = line.replace("NAME:", "").strip()
                                    elif line.strip().startswith("VERDICT:"): verdict = line.replace("VERDICT:", "").strip()
                                    elif line.strip().startswith("PROFILE:"): profile = line.replace("PROFILE:", "").strip()
                                    elif line.strip().startswith("REASON:"): reason = line.replace("REASON:", "").strip()
                                parsed_perfumes.append({"name": name, "verdict": verdict, "profile": profile, "reason": reason})
                                if "GOOD" in verdict.upper():
                                    st.session_state.scent_history.append({"perfume": name, "date": datetime.now().strftime("%b %d, %I:%M %p"), "occasion": occasion, "verdict": reason})
                        st.session_state.active_analysis = parsed_perfumes
                        st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

    if st.session_state.active_analysis:
        st.success(st.session_state.weather_info)
        for p in st.session_state.active_analysis:
            status_badge = "🟢" if "GOOD" in p['verdict'].upper() else "🚨"
            with st.expander(f"{status_badge} {p['name']} — {p['verdict']}"):
                st.markdown(f"**Scent Profile:** {p['profile']}\n\n**Weather Assessment:** {p['reason']}")

with perfume_col:
    # --- INTERACTIVE TRUE PHOTOREALISTIC BOTTLES VAULT ---
    # Gumagamit ng eksaktong transparent-cut studio graphics para sa BDC at Le Male Elixir.
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body {
            background-color: transparent;
            margin: 0;
            padding: 0;
            overflow: hidden;
            font-family: sans-serif;
            text-align: center;
        }
        .display-vault {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 50px;
            padding-top: 15px;
        }
        .instruction {
            color: #CCCCCC;
            font-size: 14px;
            font-style: italic;
            user-select: none;
            font-weight: bold;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.7);
        }
        .perfume-item {
            position: relative;
            display: inline-block;
            cursor: pointer;
        }
        .real-bottle {
            height: 190px;
            object-fit: contain;
            filter: drop-shadow(0px 8px 16px rgba(0,0,0,0.6));
            transition: transform 0.08s ease-in-out;
            -webkit-user-drag: none;
            user-select: none;
        }
        /* Haptic click effect */
        .perfume-item:active .real-bottle {
            transform: scale(0.93) translateY(3px);
        }
        
        /* Fine luxury mist cloud particle system */
        .mist-cloud {
            position: absolute;
            background: radial-gradient(circle, rgba(245, 250, 255, 0.55) 0%, rgba(180, 210, 255, 0) 75%);
            border-radius: 50%;
            pointer-events: none;
            filter: blur(2px);
            animation: blowSpray 0.45s cubic-bezier(0.1, 0.8, 0.25, 1) forwards;
        }
        @keyframes blowSpray {
            0% {
                width: 2px;
                height: 2px;
                left: 50%;
                top: 0px;
                transform: translateX(-50%);
                opacity: 1;
            }
            100% {
                width: 120px;
                height: 85px;
                left: calc(50% + var(--target-x));
                top: var(--target-y);
                transform: translateX(-50%);
                opacity: 0;
            }
        }
        </style>
    </head>
    <body>
        <div class="display-vault">
            <div class="instruction">Click to Spray!</div>
            
            <div class="perfume-item" onclick="triggerAtomizer(event, -10)">
                <img class="real-bottle" src="https://i.postimg.com/pXv1r0Tz/bdc-trans.png" alt="Bleu De Chanel">
            </div>

            <div class="perfume-item" onclick="triggerAtomizer(event, -5)">
                <img class="real-bottle" src="https://i.postimg.com/wM46k4Vj/jpg-elixir-trans.png" alt="Le Male Elixir">
            </div>
        </div>

        <script>
        function triggerAtomizer(event, startY) {
            const wrapper = event.currentTarget;
            
            for (let i = 0; i < 9; i++) {
                const mist = document.createElement('div');
                mist.classList.add('mist-cloud');
                
                const angle = (Math.random() * 46 - 23) * (Math.PI / 180);
                const distance = Math.random() * 85 + 70;
                
                const xOffset = Math.sin(angle) * distance;
                const yOffset = Math.cos(angle) * distance;
                
                mist.style.setProperty('--target-x', xOffset + 'px');
                mist.style.setProperty('--target-y', (startY - yOffset) + 'px');
                mist.style.animationDuration = (Math.random() * 0.12 + 0.38) + 's';
                
                wrapper.appendChild(mist);
                setTimeout(() => { mist.remove(); }, 450);
            }
        }
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=650, scrolling=False)
