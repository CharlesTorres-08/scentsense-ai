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

# Initialize Session State Memory for History
if "scent_history" not in st.session_state:
    st.session_state.scent_history = []

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

# 3. BACKGROUND FUNCTION WITH BALANCED CSS (Frosted Light Cards + Dark Expander Context)
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
        
        /* RETURN THE GORGEOUS EXPANDER STYLE FROM IMAGE 6F4A4F */
        .stExpander {
            background-color: #1E1E24 !important; /* Dark container title framework */
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
            margin-bottom: 10px;
        }
        .stExpander summary, .stExpander summary span, .stExpander summary p {
            color: #FFFFFF !important; /* Crisp white titles for the perfume headers */
            font-weight: 600 !important;
        }
        
        /* Inner body block segments inside expander drawer */
        div[data-testid="stExpanderDetails"] {
            background-color: #121214 !important;
            padding: 15px !important;
        }
        /* Sub-cards inside the expander drawer */
        div[data-testid="stExpanderDetails"] .stMarkdown {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
        }
        div[data-testid="stExpanderDetails"] p, div[data-testid="stExpanderDetails"] strong {
            color: #FFFFFF !important; /* Forces complete internal content readability */
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

# 4. WEATHER TOOL (FIXED UNTERMINATED F-STRING ERROR)
def get_weather(city_name):
    # Safe multi-line assembly to prevent syntax breaks on line 143
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

                    # Safely structured prompt variable without string breaking
                    base_prompt = "Current Weather: {} C, {}. Target Occasion: {}. Scent Reference Map: {}. "
                    rules_prompt = "Identify and evaluate each perfume image block. For EVERY perfume bottle detected, you must output details exactly using this layout schema: ---PERFUME--- NAME: [Name] VERDICT: [GOOD CHOICE or NOT RECOMMENDED] PROFILE: [Scent notes] REASON: [Short explanation factoring in the weather and setting] ---END---"
                    
                    full_prompt = base_prompt.format(temp, desc, occasion, str(PH_SCENT_MAP)) + rules_prompt

                    response = client.models.generate_content(
                        model="gemini-2.5-flash-lite",
                        contents=image_parts + [full_prompt],
                        config=types.GenerateContentConfig(
                            tools=[types.Tool(google_search=types.GoogleSearchRetrieval())]
                        )
                    )
                    
                    st.success(f"Weather in {city}: {temp}°C, {desc.capitalize()}")
                    st.markdown("<h3 style='color: #FFFFFF; margin-top: 20px; font-weight: 700;'>🔮 Your Fragrance Analysis Breakdown</h3>", unsafe_allow_html=True)
                    
                    raw_text = response.text
                    raw_blocks = raw_text.split("---PERFUME---")
                    
                    detected_any = False
                    for block in raw_blocks:
                        if "---END---" in block:
                            detected_any = True
                            clean_block = block.split("---END---")[0].strip()
                            
                            name, verdict, profile, reason = "Unknown Scent", "N/A", "N/A", "N/A"
                            for line in clean_block.split("\n"):
                                if "NAME:" in line:
                                    name = line.replace("NAME:", "").strip()
                                elif "VERDICT:" in line:
                                    verdict = line.replace("VERDICT:", "").strip()
                                elif "PROFILE:" in line:
                                    profile = line.replace("PROFILE:", "").strip()
                                elif "REASON:" in line:
                                    reason = line.replace("REASON:", "").strip()
                            
                            status_badge = "🟢" if "GOOD" in verdict.upper() else "🚨"
                            
                            with st.expander(f"{status_badge} {name} — {verdict}"):
                                st.markdown(f"**Scent Profile:** {profile}")
                                st.markdown(f"**Weather Assessment:** {reason}")
                            
                            if "GOOD" in verdict.upper():
                                timestamp = datetime.now().strftime("%b %d, %I:%M %p")
                                if not any(h['perfume'] == name and h['occasion'] == occasion for h in st.session_state.scent_history):
                                    st.session_state.scent_history.append({
                                        "perfume": name,
                                        "date": timestamp,
                                        "occasion": occasion,
                                        "verdict": reason
                                    })
                    
                    if not detected_any:
                        st.markdown(raw_text)
                    else:
                        st.rerun()
                            
                except Exception as e:
                    st.error(f"An error occurred while cleaning the layout: {e}")

st.info("💡 Tip: Selecting the exact occasion helps Gemini pick the perfect compliment magnet for your vibe.")
