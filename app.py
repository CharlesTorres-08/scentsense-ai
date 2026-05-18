import streamlit as st
import os
import requests
from datetime import datetime
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

# Initialize Session State Memory for History and Active Screen Results
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

# 3. BACKGROUND FUNCTION WITH BALANCED CSS
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
        
        /* White Frosted Glass Card Shields (For Inputs and File Upload Frame) */
        .stTextInput, .stSelectbox, div[data-testid="stFileUploader"] {
            background-color: rgba(255, 255, 255, 0.9) !important;
            padding: 14px;
            border-radius: 12px;
            margin-bottom: 12px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.15);
        }
        
        /* Force Form Headers and Labels to be deep Black on White Glass */
        div[data-testid="stWidgetLabel"] p, label p {
            color: #000000 !important;
            font-weight: bold !important;
        }
        
        /* Normalize text inputs typing visibility */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }

        /* FIX FILE UPLOADER DROPZONE INVISIBILITY */
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
        
        /* EXPANDER STYLE FROM IMAGE 6F4A4F */
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
        
        /* Inner body block segments inside expander drawer */
        div[data-testid="stExpanderDetails"] {
            background-color: #121214 !important;
            padding: 15px !important;
        }
        div[data-testid="stExpanderDetails"] .stMarkdown {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        }
        div[data-testid="stExpanderDetails"] p, div[data-testid="stExpanderDetails"] strong {
            color: #FFFFFF !important;
        }
        
        /* Sidebar Styling (Scent History Panel) */
        section[data-testid="stSidebar"] {
            background-color: rgba(20, 20, 25, 0.95) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }
        section[data-testid="stSidebar"] * {
            color: #FFFFFF !important;
        }
        
        /* Fix action launch button text */
        .stButton button {
            background-color: #1E1E24 !important;
            color: #FFFFFF !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
        }
        .stButton button p {
            color: #FFFFFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# 4. WEATHER TOOL
def get_weather(city_name):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": WEATHER_KEY,
        "units": "metric"
    }
    try:
        response = requests.get(base_url, params=params)
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

# --- SIDEBAR: RECENT HISTORY ---
with st.sidebar:
    st.markdown("### 📜 Scent History")
    st.caption("Your saved and recommended picks:")
    
    if not st.session_state.scent_history:
        st.info("No recommendations saved yet.")
    else:
        for idx, item in enumerate(reversed(st.session_state.scent_history)):
            with st.container():
                st.markdown(f"**🌟 {item['perfume']}**")
                st.caption(f"📅 {item['date']} | 🎯 {item['occasion']}")
                st.markdown(f"*{item['verdict']}*")
                st.markdown("---")
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.scent_history = []
            st.session_state.active_analysis = None
            st.session_state.weather_info = None
            st.rerun()

# --- MAIN PAGE CONTENT ---
st.markdown(
    """
    <div style='background-color: rgba(15, 15, 20, 0.85); backdrop-filter: blur(10px); padding: 22px; border-radius: 12px; margin-bottom: 25px; border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: 0px 4px 15px rgba(0,0,0,0.3);'>
        <h1 style='color: #FFFFFF; margin: 0; font-size: 2.3rem; font-weight: 700;'>💨 ScentSense AI</h1>
        <p style='color: #CCCCCC; margin: 6px 0 0 0; font-size: 1.05rem;'>A Context-Aware Fragrance Selection Agent</p>
    </div>
    """, 
    unsafe_allow_html=True
)

city = st.text_input("📍 Where are you right now?", placeholder="e.g., Lipa City, PH")

occasion = st.selectbox(
    "🎯 What is the occasion/vibe for today?",
    ["Casual / Daily Wear", "Office / School / Professional", "Date Night / Romantic", "Gym / Sports / Activewear", "Formal Event / Wedding"]
)

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

                    prompt_lines = [
                        f"Current Weather: {temp}C, {desc}.",
                        f"Target Occasion: {occasion}.",
                        f"Local Brand Dictionary Map: {PH_SCENT_MAP}",
                        "Identify all perfume bottles in the images. Reference the dictionary for local clones/inspirations.",
                        "Evaluate if the perfume matches BOTH the current weather temperature AND the selected lifestyle occasion context.",
                        "CRITICAL: For every single perfume bottle detected, you MUST output its result split exactly into this format:",
                        "---PERFUME---",
                        "NAME: [Write Perfume Brand and Name here]",
                        "VERDICT: [Write GOOD CHOICE or NOT RECOMMENDED here]",
                        "PROFILE: [Write short details about its scent profile/vibe here]",
                        "REASON: [Explain why it fits or does not fit the weather and the chosen occasion context here]",
                        "---END---"
                    ]
                    full_prompt = "\n".join(prompt_lines)

                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=image_parts + [full_prompt],
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearchRetrieval())]
                        )
                    )
                    
                    # Store variables globally inside session memory to safe-keep past a manual UI reload trigger
                    st.session_state.weather_info = f"Weather in {city}: {temp}°C, {desc.capitalize()}"
                    
                    parsed_perfumes = []
                    raw_text = response.text
                    raw_blocks = raw_text.split("---PERFUME---")
                    
                    for block in raw_blocks:
                        if "---END---" in block:
                            clean_block = block.split("---END---")[0].strip()
                            name, verdict, profile, reason = "Unknown Scent", "N/A", "N/A", "N/A"
                            
                            for line in clean_block.split("\n"):
                                if line.strip().startswith("NAME:"):
                                    name = line.replace("NAME:", "").strip()
                                elif line.strip().startswith("VERDICT:"):
                                    verdict = line.replace("VERDICT:", "").strip()
                                elif line.strip().startswith("PROFILE:"):
                                    profile = line.replace("PROFILE:", "").strip()
                                elif line.strip().startswith("REASON:"):
                                    reason = line.replace("REASON:", "").strip()
                            
                            parsed_perfumes.append({
                                "name": name,
                                "verdict": verdict,
                                "profile": profile,
                                "reason": reason
                            })
                            
                            # Append to modern sidebar logs if highly recommended
                            if "GOOD" in verdict.upper():
                                timestamp = datetime.now().strftime("%b %d, %I:%M %p")
                                if not any(h['perfume'] == name and h['occasion'] == occasion for h in st.session_state.scent_history):
                                    st.session_state.scent_history.append({
                                        "perfume": name,
                                        "date": timestamp,
                                        "occasion": occasion,
                                        "verdict": reason
                                    })
                    
                    # Safe keeping screen lists active 
                    st.session_state.active_analysis = parsed_perfumes if parsed_perfumes else raw_text
                    st.rerun()
                            
                except Exception as e:
                    st.error(f"An error occurred while cleaning the layout: {e}")

# --- PERSISTENT OUTPUT ZONE RIGHT UNDER THE BUTTON ---
if st.session_state.active_analysis:
    st.success(st.session_state.weather_info)
    st.markdown("<h3 style='color: #FFFFFF; margin-top: 20px; font-weight: 700;'>🔮 Your Fragrance Analysis Breakdown</h3>", unsafe_allow_html=True)
    
    # Check if we have parsed structured expander objects or raw strings
    if isinstance(st.session_state.active_analysis, list):
        for p in st.session_state.active_analysis:
            status_badge = "🟢" if "GOOD" in p['verdict'].upper() else "🚨"
            
            with st.expander(f"{status_badge} {p['name']} — {p['verdict']}"):
                st.markdown(f"**Scent Profile:** {p['profile']}")
                st.markdown(f"**Weather Assessment:** {p['reason']}")
    else:
        st.markdown(st.session_state.active_analysis)

st.info("💡 Tip: Selecting the exact occasion helps Gemini pick the perfect compliment magnet for your vibe.")
