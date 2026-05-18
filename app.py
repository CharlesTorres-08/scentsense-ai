import streamlit as st
import os
import requests
import base64
import json
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
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

# Helper function para i-convert ang local image mo patungong safe HTML data stream
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return ""

# I-convert ang mga local files mo
jpg_base64 = get_base64_image("jpg_elixir.png")
bdc_base64 = get_base64_image("bdc.png")

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

# 3. STRUCTURED DATA SCHEMAS FOR GEMINI (Pydantic Engine)
class PerfumeAnalysis(BaseModel):
    name: str = Field(description="The full brand and scent name of the identified bottle.")
    inspired_by: str = Field(description="The original luxury designer perfume this clone is inspired by based on the dictionary. Example: 'JPG Le Male Elixir'. If original designer, write 'Original Release'.")
    notes: str = Field(description="Detailed breakdown of Top Notes, Heart Notes, and Base Notes for the scent profile.")
    verdict: str = Field(description="Strictly write either 'GOOD CHOICE' or 'NOT RECOMMENDED'.")
    profile: str = Field(description="Summary of the scent's character, vibe, and longevity.")
    reason: str = Field(description="Contextual explanation on why it fits or conflicts with the current weather temperature and occasion.")

class FragranceResponse(BaseModel):
    perfumes: List[PerfumeAnalysis]

# 4. BACKGROUND FUNCTION WITH UI OVERRIDES
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
        div[data-testid="stExpanderDetails"] p, div[data-testid="stExpanderDetails"] strong, div[data-testid="stExpanderDetails"] span {
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

# 5. WEATHER TOOL
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

# 6. APP UI LAYOUT SETUP
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
main_col, perfume_col = st.columns([2.8, 1.6], gap="large")

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
                        
                        system_instruction = f"""
                        You are an expert fragrance sommelier agent. Your core job is to inspect the uploaded perfume bottle images and cross-reference them with the local brand dictionary.
                        
                        LOCAL BRAND INSPIRED-BY DICTIONARY:
                        {PH_SCENT_MAP}

                        MANDATORY INSTRUCTIONS:
                        1. Identify the perfume brand and bottle line name from the image.
                        2. If the bottle matches a clone brand listed in the dictionary above (e.g., Cotidiano, Symmetry Labs, Father and Son, Enzo Scents, D'Matteos), you MUST look up its matching luxury inspiration from the dictionary and save it in the 'inspired_by' field.
                        3. Based on that identified luxury fragrance, extract or recall its specific Top, Middle, and Base perfume notes and fill out the 'notes' field comprehensively.
                        4. Determine if the perfume is appropriate for {temp}°C weather conditions and a '{occasion}' vibe.
                        """

                        # Dito natin binago ang prompt para maging sapilitan ang pagkuha ng notes at luxury map!
                        execution_prompt = f"Identify and extract all details for the uploaded perfumes. Cross-reference with the dictionary. The current weather condition is {temp}°C ({desc}) and the target lifestyle occasion is '{occasion}'."

                        response = client.models.generate_content(
                            model="gemini-2.5-flash-lite",
                            contents=image_parts + [execution_prompt],
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                response_mime_type="application/json",
                                response_schema=FragranceResponse,
                                temperature=0.2
                            )
                        )
                        
                        raw_data = json.loads(response.text)
                        parsed_perfumes = raw_data.get("perfumes", [])
                        
                        st.session_state.weather_info = f"Weather in {city}: {temp}°C, {desc.capitalize()}"
                        st.session_state.active_analysis = parsed_perfumes
                        
                        for p in parsed_perfumes:
                            if "GOOD" in p['verdict'].upper():
                                st.session_state.scent_history.append({
                                    "perfume": p['name'], 
                                    "date": datetime.now().strftime("%b %d, %I:%M %p"), 
                                    "occasion": occasion, 
                                    "verdict": f"Inspired by: {p['inspired_by']} | {p['reason']}"
                                })
                        st.rerun()
                    except Exception as e:
                        st.error(f"An error occurred during raw compilation: {e}")

    # Display Engine
    if st.session_state.active_analysis:
        st.success(st.session_state.weather_info)
        for p in st.session_state.active_analysis:
            status_badge = "🟢" if "GOOD" in p['verdict'].upper() else "🚨"
            with st.expander(f"{status_badge} {p['name']} — {p['verdict']}"):
                st.markdown(f"✨ **Inspired By:** `{p['inspired_by']}`")
                st.markdown(f"🌿 **Fragrance Notes Breakdown:**\n{p['notes']}")
                st.markdown(f"🧪 **Scent Profile Character:**\n{p['profile']}")
                st.markdown(f"📊 **Weather Assessment:**\n{p['reason']}")

with perfume_col:
    # --- PHOTOREALISTIC BASE64 LOCAL VAULT FRAME WITH ANTI-CRASH AUDIO ENGINE ---
    if jpg_base64 and bdc_base64:
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
            }
            .container-vault {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 45vh;
                position: relative;
                padding-right: 20px;
            }
            .label-status {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
                letter-spacing: 0.5px;
                text-shadow: 0px 2px 5px rgba(0,0,0,0.9);
                opacity: 0.9;
            }
            .shelf-row {
                display: flex;
                flex-direction: row;
                align-items: flex-end;
                justify-content: center;
                gap: 25px;
                position: relative;
                margin-top: 20px;
            }
            .perfume-item {
                position: relative;
                cursor: pointer;
            }
            .real-bottle {
                object-fit: contain;
                filter: drop-shadow(0px 12px 24px rgba(0,0,0,0.85));
                transition: transform 0.08s ease-in-out;
                -webkit-user-drag: none;
                user-select: none;
            }
            .img-jpg { height: 230px; }
            .img-bdc { height: 205px; }

            .perfume-item:active .real-bottle {
                transform: scale(0.94) translateY(4px);
            }
            
            .mist-particle {
                position: absolute;
                border-radius: 50%;
                pointer-events: none;
                filter: blur(3px);
                animation: blowOut 0.45s cubic-bezier(0.1, 0.8, 0.25, 1) forwards;
            }
            @keyframes blowOut {
                0% {
                    width: 2px;
                    height: 2px;
                    left: var(--start-x);
                    top: var(--start-y);
                    opacity: 1;
                }
                100% {
                    width: 130px;
                    height: 95px;
                    left: calc(var(--start-x) + var(--move-x) - 65px);
                    top: calc(var(--start-y) + var(--move-y) - 45px);
                    opacity: 0;
                }
            }
            </style>
        </head>
        <body>
            <div class="container-vault">
                <div id="status-text" class="label-status">Active Spray: Le Male Elixir</div>
                
                <div class="shelf-row">
                    <div class="perfume-item" onclick="triggerSpray(event, 'jpg')">
                        <img class="real-bottle img-jpg" src="REPLACE_JPG_VAL" alt="Le Male Elixir">
                    </div>

                    <div class="perfume-item" onclick="triggerSpray(event, 'bdc')">
                        <img class="real-bottle img-bdc" src="REPLACE_BDC_VAL" alt="Bleu De Chanel">
                    </div>
                </div>
            </div>

            <script>
            let audioCtx = null;
            let noiseBuffer = null;

            function initAudioEngine() {
                try {
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (!AudioContext) return;
                    audioCtx = new AudioContext();
                    
                    const bufSize = audioCtx.sampleRate * 0.45; 
                    noiseBuffer = audioCtx.createBuffer(1, bufSize, audioCtx.sampleRate);
                    const data = noiseBuffer.getChannelData(0);
                    for (let i = 0; i < bufSize; i++) {
                        data[i] = Math.random() * 2 - 1;
                    }
                } catch (e) {
                    console.log("AudioContext pending trigger", e);
                }
            }

            function playSpritzSound() {
                if (!audioCtx) initAudioEngine();
                if (!audioCtx || !noiseBuffer) return;

                if (audioCtx.state === 'suspended') {
                    audioCtx.resume();
                }

                try {
                    const noiseSource = audioCtx.createBufferSource();
                    noiseSource.buffer = noiseBuffer;
                    
                    const filter = audioCtx.createBiquadFilter();
                    filter.type = 'highpass';
                    filter.frequency.value = 6000; 
                    
                    const gain = audioCtx.createGain();
                    gain.gain.setValueAtTime(0, audioCtx.currentTime);
                    gain.gain.linearRampToValueAtTime(0.3, audioCtx.currentTime + 0.02);
                    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.42);
                    
                    noiseSource.connect(filter);
                    filter.connect(gain);
                    gain.connect(audioCtx.destination);
                    
                    noiseSource.start();
                } catch (err) {
                    console.log("Audio pipeline locked", err);
                }
            }

            function triggerSpray(event, type) {
                const container = event.currentTarget;
                const statusLabel = document.getElementById('status-text');
                
                if (type === 'jpg') {
                    statusLabel.innerText = "Active Spray: Le Male Elixir";
                } else {
                    statusLabel.innerText = "Active Spray: Bleu de Chanel";
                }
                
                playSpritzSound();
                
                const startX = "50%";
                const startY = type === 'jpg' ? "10px" : "15px";
                
                const colorGrad = type === 'jpg' 
                    ? 'radial-gradient(circle, rgba(212,175,55,0.65) 0%, rgba(139,107,14,0) 75%)'
                    : 'radial-gradient(circle, rgba(235,245,255,0.55) 0%, rgba(160,190,240,0) 75%)';

                for (let i = 0; i < 10; i++) {
                    const p = document.createElement('div');
                    p.classList.add('mist-particle');
                    p.style.background = colorGrad;
                    p.style.setProperty('--start-x', startX);
                    p.style.setProperty('--start-y', startY);
                    
                    const angle = (Math.random() * 40 - 75) * (Math.PI / 180); 
                    const dist = Math.random() * 90 + 75;
                    
                    p.style.setProperty('--move-x', Math.cos(angle) * dist + 'px');
                    p.style.setProperty('--move-y', Math.sin(angle) * dist + 'px');
                    p.style.animationDuration = (Math.random() * 0.12 + 0.38) + 's';
                    
                    container.appendChild(p);
                    setTimeout(() => { p.remove(); }, 450);
                }
            }
            </script>
        </body>
        </html>
        """
        html_code = html_code.replace("REPLACE_JPG_VAL", jpg_base64).replace("REPLACE_BDC_VAL", bdc_base64)
        components.html(html_code, height=360, scrolling=False)
