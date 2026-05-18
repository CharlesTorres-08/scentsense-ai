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
    """Fetches real-time weather using wttr.in (No API Key Required)"""
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

# --- 6. USER INTERFACE LAYOUT (UI) & CSS BACKGROUND INJECTION ---
st.title("🔮 ScentSense AI")
st.caption("A Context-Aware Fragrance Selection Agent & Olfactory Intelligence Platform")

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.82), rgba(0, 0, 0, 0.88)), 
                    url('https://images.unsplash.com/photo-1615655096345-61a54750068d?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .stMarkdown, h1, h2, h3, p, span, label {
        color: #f0f2f6 !important;
    }
    div[data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
                justify-content
