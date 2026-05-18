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
        section[data-testid="stSidebar"] * {
            color: #FFFFFF !important;
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

# 5. UI LAYOUT
st.set_page_config(page_title="ScentSense AI", page_icon=":material/air:", layout="wide")
set_bg_from_url()

with st.sidebar:
    st.markdown("### 📜 Scent History")
    if not st.session_state.scent_history:
        st.info("No picks yet.")
    else:
        for item in reversed(st.session_state.scent_history):
            st.markdown(f"**🌟 {item['perfume']}**")
            st.caption(f"{item['date']} | {item['occasion']}")
            st.markdown("---")
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.scent_history, st.session_state.active_analysis, st.session_state.weather_info = [], None, None
        st.rerun()

main_col, perfume_col = st.columns([3.2, 1.2], gap="large")

with main_col:
    st.markdown("""
        <div style='background-color: rgba(15, 15, 20, 0.85); backdrop-filter: blur(10px); padding: 22px; border-radius: 12px; margin-bottom: 25px; border: 1px solid rgba(255, 255, 255, 0.1);'>
            <h1 style='color: #FFFFFF; margin: 0; font-size: 2.3rem; font-weight: 700;'>💨 ScentSense AI</h1>
            <p style='color: #CCCCCC; margin: 6px 0 0 0; font-size: 1.05rem;'>Context-Aware Fragrance Agent</p>
        </div>
    """, unsafe_allow_html=True)

    city = st.text_input("📍 Location", placeholder="e.g., Lipa City, PH")
    occasion = st.selectbox("🎯 Occasion", ["Casual", "Office", "Date Night", "Gym", "Formal"])
    uploaded_files = st.file_uploader("📸 Collection Photos", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

    if st.button("🚀 Find My Scent", use_container_width=True):
        if not uploaded_files or not city:
            st.warning("Needs city and photos!")
        else:
            with st.spinner("Analyzing..."):
                temp, desc = get_weather(city)
                if temp:
                    try:
                        image_parts = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in uploaded_files]
                        prompt = f"Weather: {temp}C, {desc}. Occasion: {occasion}. Reference: {PH_SCENT_MAP}. Evaluate each perfume. Format: ---PERFUME--- NAME: [Name] VERDICT: [GOOD CHOICE or NOT RECOMMENDED] PROFILE: [Scent] REASON: [Why] ---END---"
                        response = client.models.generate_content(model="gemini-2.5-flash-lite", contents=image_parts + [prompt], config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearchRetrieval())]))
                        
                        st.session_state.weather_info = f"Weather: {temp}°C, {desc.capitalize()}"
                        parsed = []
                        for block in response.text.split("---PERFUME---"):
                            if "---END---" in block:
                                clean = block.split("---END---")[0].strip()
                                p = {"name": "Unknown", "verdict": "N/A", "profile": "N/A", "reason": "N/A"}
                                for line in clean.split("\n"):
                                    if "NAME:" in line: p["name"] = line.replace("NAME:", "").strip()
                                    elif "VERDICT:" in line: p["verdict"] = line.replace("VERDICT:", "").strip()
                                    elif "PROFILE:" in line: p["profile"] = line.replace("PROFILE:", "").strip()
                                    elif "REASON:" in line: p["reason"] = line.replace("REASON:", "").strip()
                                parsed.append(p)
                                if "GOOD" in p["verdict"].upper():
                                    st.session_state.scent_history.append({"perfume": p["name"], "date": datetime.now().strftime("%b %d, %I:%M %p"), "occasion": occasion})
                        st.session_state.active_analysis = parsed
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

    if st.session_state.active_analysis:
        st.success(st.session_state.weather_info)
        for p in st.session_state.active_analysis:
            with st.expander(f"{'🟢' if 'GOOD' in p['verdict'].upper() else '🚨'} {p['name']} — {p['verdict']}"):
                st.write(f"**Profile:** {p['profile']}\n\n**Reason:** {p['reason']}")

with perfume_col:
    # --- DUAL INTERACTIVE BOTTLE FRAME (BDC + JPG ELIXIR) ---
    html_code = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
        body { background-color: transparent; margin: 0; padding: 0; overflow: hidden; text-align: center; }
        .vault { display: flex; flex-direction: column; align-items: center; gap: 60px; padding-top: 40px; }
        
        .bottle-wrapper { position: relative; cursor: pointer; transition: transform 0.1s; }
        .bottle-wrapper:active { transform: scale(0.95) translateY(4px); }
        
        /* BDC Bottle CSS */
        .bdc {
            width: 150px; height: 160px; background: linear-gradient(135deg, #0d162d, #050814);
            border-radius: 12px; border: 2px solid #1a294a; position: relative;
            box-shadow: 0 10px 25px rgba(0,0,0,0.8); display: flex; flex-direction: column; justify-content: center;
        }
        .bdc::before { content: ''; position: absolute; top: -35px; left: 50%; transform: translateX(-50%); width: 45px; height: 35px; background: #050811; border-radius: 4px; }
        .bdc-txt { color: white; font-family: sans-serif; letter-spacing: 3px; font-weight: bold; font-size: 11px; }

        /* JPG Le Male Elixir CSS */
        .jpg {
            width: 100px; height: 170px; background: linear-gradient(to bottom, #d4af37, #8b6b0e);
            border-radius: 30% 30% 40% 40% / 10% 10% 30% 30%; position: relative;
            box-shadow: 0 10px 25px rgba(0,0,0,0.8);
            /* Sailor Stripes */
            background-image: repeating-linear-gradient(0deg, transparent, transparent 15px, rgba(0,0,0,0.3) 15px, rgba(0,0,0,0.3) 20px);
        }
        .jpg::before { 
            content: ''; position: absolute; top: -25px; left: 50%; transform: translateX(-50%); 
            width: 30px; height: 25px; background: gold; border-radius: 50% 50% 0 0; 
            box-shadow: inset 0 -2px 5px rgba(0,0,0,0.5);
        }
        .jpg-txt { color: #5c4a00; font-family: sans-serif; font-size: 9px; font-weight: bold; margin-top: 80px; display: block; }

        /* Spray Animation */
        .mist {
            position: absolute; background: radial-gradient(circle, rgba(235,245,255,0.6), rgba(200,225,255,0) 70%);
            border-radius: 50%; pointer-events: none; filter: blur(3px);
            animation: spray 0.45s ease-out forwards;
        }
        @keyframes spray {
            0% { width: 5px; height: 5px; opacity: 1; top: var(--y); left: var(--x); }
            100% { width: 100px; height: 80px; opacity: 0; top: calc(var(--y) - 80px); left: calc(var(--x) - 45px); }
        }
        </style>
    </head>
    <body>
        <div class="vault">
            <div class="bottle-wrapper" onclick="spray(event, 0)">
                <div class="bdc">
                    <div class="bdc-txt">BLEU</div>
                    <div style="color:white; font-size:7px; opacity:0.6;">DE</div>
                    <div class="bdc-txt">CHANEL</div>
                </div>
            </div>

            <div class="bottle-wrapper" onclick="spray(event, -20)">
                <div class="jpg">
                    <span class="jpg-txt">ELIXIR</span>
                </div>
            </div>
        </div>

        <script>
        function spray(e, offset) {
            const wrapper = e.currentTarget;
            for(let i=0; i<8; i++) {
                const m = document.createElement('div');
                m.className = 'mist';
                m.style.setProperty('--x', '50%');
                m.style.setProperty('--y', offset + 'px');
                m.style.animationDelay = (Math.random()*0.1) + 's';
                wrapper.appendChild(m);
                setTimeout(() => m.remove(), 500);
            }
        }
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=650)
