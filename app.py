import streamlit as st
import requests
import os
import base64
from datetime import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List
import streamlit.components.v1 as components

# --- 1. INITIAL SETUP & CONFIGURATION ---
st.set_page_config(
    page_title="ScentSense AI — Smart Fragrance Selection Agent",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Gemini Client (Uses GEMINI_API_KEY from environment or .env)
# Para sa Streamlit Cloud, ilagay ito sa Settings > Secrets
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]

try:
    client = genai.Client()
except Exception as e:
    st.error("⚠️ Gemini API Key missing or misconfigured. Please check your setup.")

# --- 2. LOCAL BRANDS SCENT DICTIONARY MAP ---
PH_SCENT_MAP = {
    "Cotidiano": {
        "Debonair": "Jean Paul Gaultier Le Male Elixir",
        "Choco Carnival": "Montale Chocolate Greedy",
        "Amalfi Coast": "Tom Ford Neroli Portofino",
        "White Silk": "Maison Francis Kurkdjian 724",
        "Suede & Saffron": "Tom Ford Tuscan Leather"
    },
    "Symmetry Labs": {
        "Tiger Eye": "Bvlgari Tygar",
        "L'Homme": "Yves Saint Laurent L'Homme",
        "Elysian": "Roja Elysium",
        "Altum": "香奈儿 Bleu de Chanel"
    },
    "Father and Son": {
        "King": "Creed Aventus",
        "Suave": "Dior Sauvage",
        "Spectre": "Viktor & Rolf Spicebomb Extreme"
    }
}

# --- 3. SESSION STATE ENGINE ---
if "scent_history" not in st.session_state:
    st.session_state.scent_history = []
if "active_analysis" not in st.session_state:
    st.session_state.active_analysis = None
if "weather_info" not in st.session_state:
    st.session_state.weather_info = ""

# --- 4. STRUCTURED DATA SCHEMAS FOR GEMINI ---
class PerfumeAnalysis(BaseModel):
    name: str = Field(description="The full brand and scent name of the identified bottle.")
    inspired_by: str = Field(description="The original luxury designer perfume this clone is inspired by based on the dictionary. If original designer, write 'Original Designer Release'.")
    notes: str = Field(description="Detailed breakdown of Top Notes, Heart Notes, and Base Notes.")
    verdict: str = Field(description="Strictly write either 'GOOD CHOICE' or 'NOT RECOMMENDED'.")
    profile: str = Field(description="Summary of the scent's character, vibe, and longevity.")
    reason: str = Field(description="Contextual explanation on why it fits or conflicts with the current weather temperature and occasion.")

class FragranceResponse(BaseModel):
    perfumes: List[PerfumeAnalysis]

# --- 5. HELPER FUNCTIONS ---
def get_weather(city_name):
    """Fetches real-time weather usingwttr.in (No API Key Required)"""
    try:
        url = f"https://wttr.in/{city_name}?format=%t+%C"
        res = requests.get(url, timeout=5)
        if res.status_code == 200 and "鋪" not in res.text:
            parts = res.text.strip().split()
            if parts:
                temp_str = "".join([c for c in parts[0] if c.isdigit() or c in ['-', '+']])
                condition = " ".join(parts[1:])
                return int(temp_str), condition
        return 29, "Partly Cloudy"  # Smart default for PH weather
    except:
        return 29, "Partly Cloudy"

def load_image_as_base64(path):
    """Encodes asset PNG files into Base64 injectors for HTML frame injection"""
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return ""

# Pre-load localized background transparent spray canisters
jpg_base64 = load_image_as_base64("jpg_elixir.png")
bdc_base64 = load_image_as_base64("bdc.png")

# --- 6. USER INTERFACE LAYOUT (UI) ---
st.title("🔮 ScentSense AI")
st.caption("A Context-Aware Fragrance Selection Agent & Olfactory Intelligence Platform")

left_col, right_col = st.columns([1, 1], gap="large")

with left_col:
    st.subheader("📋 Input parameters")
    
    city = st.text_input("📍 Where are you right now?", placeholder="e.g., Lipa City, PH", help="Used to automatically calculate localized weather-to-scent ratios.")
    
    occasion = st.selectbox(
        "🎯 What is the occasion/vibe for today?",
        ["Casual / Daily Wear", "Office / School Setting", "Formal Night Gala", "Gym / High-Intensity Workout", "Intimate Date Night", "Clubbing / Nightlife Party"]
    )
    
    uploaded_files = st.file_uploader(
        "📸 Upload photos of your perfumes", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        help="Upload clear photos of your perfume bottles. AI will cross-examine local clones."
    )
    
    # --- TRIGGER AND COMPUTATION CONTROL VALVE ---
    if st.button("🚀 Find My Scent", use_container_width=True):
        if not uploaded_files or not city:
            st.warning("Please provide both your city and at least one perfume photo!")
        else:
            with st.spinner("Analyzing bottles and pulling exact olfactory profiles..."):
                temp, desc = get_weather(city)
                if temp is not None:
                    try:
                        image_parts = [types.Part.from_bytes(data=f.getvalue(), mime_type=f.type) for f in uploaded_files]
                        
                        system_instruction = f"""
                        You are an expert fragrance sommelier agent. Your task is to identify the perfume bottles from the images.
                        
                        CROSS-REFERENCE DICTIONARY:
                        {PH_SCENT_MAP}

                        CRITICAL DIRECTIONS:
                        1. Match any local clone brand found in the image to its original luxury inspiration using the dictionary provided.
                        2. Look up or recall the exact olfactory notes (Top, Middle, and Base notes) for each perfume.
                        3. Evaluate if the scent profile is appropriate for {temp}°C weather and a '{occasion}' vibe.
                        """

                        response = client.models.generate_content(
                            model="gemini-2.5-flash-lite",
                            contents=image_parts + ["Analyze the perfumes in the image."],
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                response_mime_type="application/json",
                                response_schema=FragranceResponse,
                                temperature=0.2
                            )
                        )
                        
                        import json
                        raw_data = json.loads(response.text)
                        parsed_perfumes = raw_data.get("perfumes", [])
                        
                        st.session_state.weather_info = f"Weather in {city}: {temp}°C, {desc.capitalize()}"
                        st.session_state.active_analysis = parsed_perfumes
                        
                        # Save successful recommendations to system cache log
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
                        st.error(f"Error mapping fragrance data layer: {e}")

    # --- RENDER EXPERT DISCOVERY REPORTS ---
    if st.session_state.active_analysis:
        st.write("---")
        st.subheader("📊 Your Fragrance Analysis Breakdown")
        st.success(st.session_state.weather_info)
        
        for p in st.session_state.active_analysis:
            status_badge = "🟢" if "GOOD" in p['verdict'].upper() else "🚨"
            
            with st.expander(f"{status_badge} {p['name']} — {p['verdict']}"):
                st.markdown(f"✨ **Inspired By:** `{p['inspired_by']}`")
                st.markdown(f"🌿 **Fragrance Notes Breakdown:**\n{p['notes']}")
                st.markdown(f"🧪 **Scent Profile Character:**\n{p['profile']}")
                st.markdown(f"📊 **Contextual Assessment:**\n{p['reason']}")

with right_col:
    # --- SIDE CONSOLE / INTERACTIVE LAYER ---
    st.subheader("🧪 Interactive Scent Deck")
    
    # --- PHOTOREALISTIC BASE64 LOCAL VAULT FRAME WITH ANTI-SPAM AUDIO ENGINE ---
    if jpg_base64 and bdc_base64:
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
            body {{
                background-color: transparent;
                margin: 0;
                padding: 0;
                overflow: hidden;
                font-family: sans-serif;
            }}
            .container-vault {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 45vh;
                position: relative;
                padding-right: 20px;
            }}
            .label-status {{
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 5px;
                letter-spacing: 0.5px;
                text-shadow: 0px 2px 5px rgba(0,0,0,0.9);
                opacity: 0.9;
            }}
            .shelf-row {{
                display: flex;
                flex-direction: row;
                align-items: flex-end;
                justify-content: center;
                gap: 35px;
                position: relative;
                margin-top: 20px;
            }}
            .perfume-item {{
                position: relative;
                cursor: pointer;
            }}
            .real-bottle {{
                object-fit: contain;
                background: transparent !important;
                filter: drop-shadow(0px 12px 24px rgba(0,0,0,0.85));
                transition: transform 0.08s ease-in-out;
                -webkit-user-drag: none;
                user-select: none;
            }}
            .img-jpg {{ height: 210px; }}
            .img-bdc {{ height: 185px; }}

            .perfume-item:active .real-bottle {{
                transform: scale(0.94) translateY(4px);
            }}
            
            .mist-particle {{
                position: absolute;
                border-radius: 50%;
                pointer-events: none;
                filter: blur(3px);
                animation: blowOut 0.45s cubic-bezier(0.1, 0.8, 0.25, 1) forwards;
            }}
            @keyframes blowOut {{
                0% {{
                    width: 2px;
                    height: 2px;
                    left: var(--start-x);
                    top: var(--start-y);
                    opacity: 1;
                }}
                100% {{
                    width: 130px;
                    height: 95px;
                    left: calc(var(--start-x) + var(--move-x) - 65px);
                    top: calc(var(--start-y) + var(--move-y) - 45px);
                    opacity: 0;
                }}
            }}
            </style>
        </head>
        <body>
            <div class="container-vault">
                <div id="status-text" class="label-status">Active Spray: Le Male Elixir</div>
                
                <div class="shelf-row">
                    <div class="perfume-item" onclick="triggerSpray(event, 'jpg')">
                        <img class="real-bottle img-jpg" src="{jpg_base64}" alt="Le Male Elixir">
                    </div>

                    <div class="perfume-item" onclick="triggerSpray(event, 'bdc')">
                        <img class="real-bottle img-bdc" src="{bdc_base64}" alt="Bleu De Chanel">
                    </div>
                </div>
            </div>

            <script>
            // Global Persistent Audio Engine Settings to prevent crashing on multi-clicks
            let audioCtx = null;
            let noiseBuffer = null;

            function initAudioEngine() {{
                try {{
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    if (!AudioContext) return;
                    audioCtx = new AudioContext();
                    
                    // Pre-generate White Noise Waveform Buffer once in memory
                    const bufSize = audioCtx.sampleRate * 0.45; 
                    noiseBuffer = audioCtx.createBuffer(1, bufSize, audioCtx.sampleRate);
                    const data = noiseBuffer.getChannelData(0);
                    for (let i = 0; i < bufSize; i++) {{
                        data[i] = Math.random() * 2 - 1;
                    }}
                }} catch (e) {{
                    console.log("AudioContext initialization delayed until click event", e);
                }}
            }}

            function playSpritzSound() {{
                // Initialize context on the first interactive click if not yet active
                if (!audioCtx) initAudioEngine();
                if (!audioCtx || !noiseBuffer) return;

                // Resume automatically if browser put the context to sleep
                if (audioCtx.state === 'suspended') {{
                    audioCtx.resume();
                }}

                try {{
                    const noiseSource = audioCtx.createBufferSource();
                    noiseSource.buffer = noiseBuffer;
                    
                    // Highpass Filter to lock in crisp premium air mist pressure
                    const filter = audioCtx.createBiquadFilter();
                    filter.type = 'highpass';
                    filter.frequency.value = 6500; 
                    
                    // Audio Envelope Curve (Instant punch drop down to soft release)
                    const gain = audioCtx.createGain();
                    gain.gain.setValueAtTime(0, audioCtx.currentTime);
                    gain.gain.linearRampToValueAtTime(0.25, audioCtx.currentTime + 0.01);
                    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.4);
                    
                    // Audio Pipeline Node Mapping
                    noiseSource.connect(filter);
                    filter.connect(gain);
                    gain.connect(audioCtx.destination);
                    
                    noiseSource.start();
                }} catch (err) {{
                    console.log("Audio block engine bypass error during spam click", err);
                }}
            }}

            function triggerSpray(event, type) {{
                const container = event.currentTarget;
                const statusLabel = document.getElementById('status-text');
                
                if (type === 'jpg') {{
                    statusLabel.innerText = "Active Spray: Le Male Elixir";
                }} else {{
                    statusLabel.innerText = "Active Spray: Bleu de Chanel";
                }}
                
                // Fire persistent audio engine trigger
                playSpritzSound();
                
                // Spray release point tracking
                const startX = "50%";
                const startY = type === 'jpg' ? "10px" : "15px";
                
                const colorGrad = type === 'jpg' 
                    ? 'radial-gradient(circle, rgba(212,175,55,0.65) 0%, rgba(139,107,14,0) 75%)'
                    : 'radial-gradient(circle, rgba(235,245,255,0.55) 0%, rgba(160,190,240,0) 75%)';

                for (let i = 0; i < 10; i++) {{
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
                    setTimeout(() => {{ p.remove(); }}, 450);
                }}
            }}
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=340, scrolling=False)
    else:
        st.warning("⚠️ Pakisiguradong nailagay mo na ang 'jpg_elixir.png' at 'bdc.png' sa iyong project folder para lumitaw ang mga bote nang walang white background.")

    # --- HISTORICAL SCENT TIMELINE REEL ---
    st.write("---")
    st.subheader("📜 Scent Selection History")
    if st.session_state.scent_history:
        for item in reversed(st.session_state.scent_history):
            st.info(f"✨ **{item['perfume']}** — *{item['occasion']}*\n\n📅 {item['date']} | {item['verdict']}")
    else:
        st.caption("No historical spray captures saved yet. Fire an engine discovery scan above!")
