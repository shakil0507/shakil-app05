import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import difflib
import os
from datetime import datetime, timedelta, timezone
import openpyxl
import json



HISTORY_FILE = "history.json"

# Load chat history
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        try:
            all_histories = json.load(f)
            if isinstance(all_histories, list):
                all_histories = {}  # reset if old format
        except:
            all_histories = {}
else:
    all_histories = {}

IST = timezone(timedelta(hours=5, minutes=30))

def get_current_ist_time():
    return datetime.now(IST).strftime("%I:%M %p")


if "messages" not in st.session_state:
    st.session_state.messages = []

if "username" not in st.session_state:
    st.session_state.username = ""

if "chat_title" not in st.session_state:
    st.session_state.chat_title = ""

if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# Page config
st.set_page_config(page_title="Chennai Risk Chatbot", page_icon="🌆")
st.markdown("""
    <style>
        .big-font { font-size:24px !important; }
        .highlight { color: #FF4B4B; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🤖 Chennai AI Risk Chatbot")

st.markdown("""
<p class='big-font'>
    Ask about <span class='highlight'>accidents, pollution, crime, heat, flood, population, or risk factors</span>.
</p>
""", unsafe_allow_html=True)

st.markdown("#### 🔍 You can ask about these areas:")

places = [
    "Thiruvottiyur", "Egmore", "Madhavaram", "Tondiarpet", "Royapuram",
    "Perambur", "Purasaiwakkam", "Anna Nagar", "Koyambedu", "T Nagar",
    "Velachery", "Guindy", "Adyar", "Vadapalani", "Sholinganallur"
]

cols = st.columns(3)
for idx, place in enumerate(places):
    with cols[idx % 3]:
        st.markdown(f"- {place}")


with st.sidebar:
    # Sidebar: Show Profile if user exists
    # Sidebar: Collapsible User Profile
    if st.session_state.username:
        with st.expander("👤 User Profile", expanded=False):
            st.markdown(f"- Name: {st.session_state.username}")
            st.markdown(f"- Age: {st.session_state.get('user_age', '-')}")
            st.markdown(f"- Gender: {st.session_state.get('user_gender', '-')}")
            st.markdown(f"- Email: {st.session_state.get('user_email', '-')}")
        st.markdown("---")


    st.markdown("## ➕ New Chat")
    if st.button("🔄 Start New Chat"):
        st.session_state.username = ""
        st.session_state.chat_title = ""
        st.session_state.messages = []
        st.rerun()


    st.markdown("## 📜 Your Chat History")

    current_user = st.session_state.username
    if current_user and current_user in all_histories:
        user_chats = all_histories[current_user]

        # ✅ Fix: Ensure user_chats is a dictionary before accessing .keys()
        if not isinstance(user_chats, dict):
            user_chats = {}

        if not user_chats:
            st.info("No previous chats found.")
        else:
            for title in list(user_chats.keys()):
                col1, col2 = st.columns([6, 1])
                with col1:
                    if st.button(f"📁 {title}", key=f"{current_user}_{title}"):
                        st.session_state.chat_title = title
                        st.session_state.messages = user_chats.get(title, [])
                        st.rerun()

                with col2:
                    if st.button("🗑", key=f"delete_{current_user}_{title}", help="Delete this chat", use_container_width=True):
                        del all_histories[current_user][title]
                        with open(HISTORY_FILE, "w") as f:
                            json.dump(all_histories, f, indent=2)
                        st.rerun()
    else:
        st.info("Start a chat to see your history.")

# Load data
accident_df = pd.read_excel("accident.xlsx")
flood_df = pd.read_excel("flood.xlsx")
crime_df = pd.read_excel("crime_details.xlsx")
air_df = pd.read_excel("air_pollution.xlsx")
heat_df = pd.read_excel("heat.xlsx")
population_df = pd.read_excel("population.xlsx")
risk_df = pd.read_excel("riskanalysis.xlsx")

# Clean column headers
for df in [accident_df, flood_df, crime_df, air_df, heat_df, population_df, risk_df]:
    df.columns = df.columns.str.strip()

# Initialize session state
# Ask for user's name only once
# Ask for user's name, age, gender only once
if st.session_state.username == "" and st.session_state.chat_title == "":
    with st.form("user_info_form", clear_on_submit=False):
        name = st.text_input("👤 Enter your name:")
        age = st.text_input("🎂 Enter your age:")
        gender = st.selectbox("⚧ Select your gender:", ["Male", "Female", "Other"])
        email = st.text_input("📧 Enter your email:")
        submitted = st.form_submit_button("Start Chat")

        if submitted and name and age and gender and email:
            st.session_state.username = name
            st.session_state.user_age = age
            st.session_state.user_gender = gender
            st.session_state.user_email = email
            st.session_state.messages = [{
                "role": "assistant",
                "content": f"Hi {name}, welcome to Chennai AI Assistant Chatbot! 😊",
                "time": get_current_ist_time()
            }]
            st.rerun()
        st.stop()



def email_to_filename(email):
    return email.replace('@', 'at').replace('.', '_') + '.json'

# Directory to store chat history
os.makedirs("history_data", exist_ok=True)
user_file = os.path.join("history_data", email_to_filename(st.session_state.user_email))

# Load chat history
if os.path.exists(user_file):
    with open(user_file, 'r') as f:
        st.session_state.messages = json.load(f)
else:
    st.session_state.messages = st.session_state.get("messages", [])




# Fuzzy zone matcher
def find_zone(query_text, zone_list):
    query_text = query_text.lower()
    for zone in zone_list:
        if zone.lower() in query_text:
            return zone
    for word in query_text.split():
        match = difflib.get_close_matches(word, zone_list, n=1, cutoff=0.6)
        if match:
            return match[0]
    return difflib.get_close_matches(query_text, zone_list, n=1, cutoff=0.6)[0] if difflib.get_close_matches(query_text, zone_list, n=1, cutoff=0.6) else None

# Plotting
def plot_bar(df, xcol, ycol, title, color='blue'):
    df = df[[xcol, ycol]].dropna()
    df[ycol] = pd.to_numeric(df[ycol], errors='coerce')
    df = df.groupby(xcol).sum().sort_values(ycol, ascending=False)
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(df.index, df[ycol], color=color)
    ax.set_title(title)
    ax.set_ylabel(ycol)
    plt.xticks(rotation=45, ha='right')
    for bar in bars:
        ax.annotate(f"{int(bar.get_height())}", xy=(bar.get_x()+bar.get_width()/2, bar.get_height()),
                    ha='center', va='bottom', fontsize=8)
    st.pyplot(fig)

# Display previous messages with visual responses
# Display previous messages with visual responses
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        timestamp = msg.get("time", "")
        role_icon = "🧑" if msg["role"] == "user" else "🤖"
        role_name = "You" if msg["role"] == "user" else "AI"
        st.markdown(f"{role_icon} {role_name} {timestamp}")
        st.markdown(msg["content"])


    if msg["role"] == "assistant":
        zone = msg.get("zone", "")
        mtype = msg.get("type", "")
        
        def show_precaution(title, tips):
            st.markdown(f"### ⚠ Precaution for {title}")
            for tip in tips:
                st.markdown(f"- {tip}")

        if mtype == "flood":
            st.dataframe(flood_df[flood_df["Zone"] == zone])
            plot_bar(flood_df, "Zone", "People Affected", "Flood Impact", "blue")
            show_precaution("Flood", [
                "Avoid walking or driving through flood waters.",
                "Relocate to higher ground in case of warnings.",
                "Stay updated through official alerts.",
                "Boil drinking water to avoid infections.",
                "Keep emergency contacts and supplies ready."
            ])

        elif mtype == "accident":
            st.dataframe(accident_df[accident_df["Zone"] == zone])
            plot_bar(accident_df, "Zone", "No. of Cases", "Accident Cases", "red")
            show_precaution("Road Accidents", [
                f"Drive carefully near {zone}.",
                "Follow all traffic signals and speed limits.",
                "Wear helmet/seatbelt at all times.",
                "Avoid using mobile phones while driving.",
                "Stay alert in crowded intersections."
            ])

        elif mtype == "crime":
            st.dataframe(crime_df[crime_df["Zone"] == zone])
            plot_bar(crime_df, "Zone", "Total Crimes", "Crime by Zone", "orange")
            show_precaution("Crime", [
                f"Avoid isolated areas in {zone}, especially at night.",
                "Always lock your doors and windows.",
                "Report any suspicious activity to police.",
                "Avoid sharing personal info with strangers.",
                "Install safety apps or devices."
            ])

        elif mtype == "pollution":
            st.dataframe(air_df[air_df["Zone"] == zone])
            plot_bar(air_df, "Zone", "Avg. Value (µg/m³) or AQI", "Air Pollution", "grey")
            show_precaution("Air Pollution", [
                f"Wear a mask when outdoors in {zone}.",
                "Avoid outdoor exercise during peak hours.",
                "Use air purifiers at home.",
                "Stay indoors if you have respiratory issues.",
                "Check AQI levels before planning activities."
            ])

        elif mtype == "heat":
            st.dataframe(heat_df[heat_df["Zone"] == zone])
            plot_bar(heat_df, "Zone", "Heatstroke Cases", "Heatstroke Cases", "green")
            show_precaution("Heat", [
                f"Use an umbrella or cap in {zone}.",
                "Stay hydrated – drink plenty of water.",
                "Avoid outdoor activities during noon.",
                "Wear light and breathable clothes.",
                "Apply sunscreen to protect from sunburn."
            ])

        elif mtype == "population":
            st.dataframe(population_df[population_df["Zone"] == zone])
            plot_bar(population_df, "Zone", "Population", "Population by Zone", "purple")
            show_precaution("Crowded Areas", [
                f"Plan your commute to avoid traffic in {zone}.",
                "Stay aware of your surroundings in crowded places.",
                "Avoid peak hours when possible.",
                "Keep belongings safe to avoid theft.",
                "Use masks in crowded areas for hygiene."
            ])

        elif mtype in ["risk_all", "risk_detail", "risk"]:
            factor = msg.get("factor", None)
        
            if mtype == "risk_all":
                st.markdown("### 📋 Complete Risk Table")
                st.dataframe(risk_df)
                # Bar chart of total for each factor
                risk_cols = ["Accident", "Air Pollution", "Flood", "Heat", "Crime", "Population"]
                mean_vals = risk_df[risk_cols].mean()
                fig, ax = plt.subplots()
                bars = ax.bar(mean_vals.index, mean_vals.values, color='teal')
                ax.set_ylabel("Average Risk (1=Low, 2=Med, 3=High)")
                ax.set_title("Average Risk Levels Across Zones")
                plt.xticks(rotation=45)
                for bar in bars:
                    ax.annotate(f"{bar.get_height():.1f}", (bar.get_x() + bar.get_width()/2, bar.get_height()), ha='center', va='bottom')
                st.pyplot(fig)
                show_precaution("Overall Risk", [
                    "Stay informed using official sources.",
                    "Avoid high-risk areas during alerts.",
                    "Follow safety protocols.",
                    "Ensure emergency contacts are accessible."
                ])

            elif mtype == "risk_detail" and factor:
                st.markdown(f"### 📊 Risk Factor: {factor}")
                st.dataframe(risk_df[["Zone", factor]])
                plot_bar(risk_df, "Zone", factor, f"{factor} Risk Levels", "crimson")
                precaution_map = {
                    "Accident": [
                        "Follow traffic rules strictly.",
                        "Avoid rash driving.",
                        "Be alert in accident-prone zones."
                    ],
                    "Air Pollution": [
                        "Use masks when pollution is high.",
                        "Avoid peak traffic hours.",
                        "Use air purifiers indoors."
                    ],
                    "Flood": [
                        "Do not walk through flood water.",
                        "Shift to safer zones during heavy rain.",
                        "Boil drinking water."
                    ],
                    "Heat": [
                        "Stay hydrated and avoid direct sunlight.",
                        "Use sunscreen and wear cotton clothes.",
                        "Avoid outdoor activities at noon."
                    ],
                    "Crime": [
                        "Avoid lonely roads at night.",
                        "Be alert and avoid confrontation.",
                        "Use safety apps for emergencies."
                    ],
                    "Population": [
                        "Avoid crowded public transport.",
                        "Travel during off-peak hours.",
                        "Be aware of theft in crowds."
                    ]
                }
                show_precaution(factor, precaution_map.get(factor, ["Stay alert."]))


            

# Chat input
# Chat input
reply_type = None  # Prevent NameError on first check
query = st.chat_input("Type your query here...")
if query:
    timestamp = get_current_ist_time()
    if st.session_state.chat_title == "":
        if reply_type:
            st.session_state.chat_title = reply_type.capitalize()
        else:
            st.session_state.chat_title = f"Chat - {datetime.now(IST).strftime('%b %d, %I:%M %p')}"

    st.session_state.messages.append({
        "role": "user", "content": query, "time": timestamp
    })


    # 💬 Greeting check logic here
    greetings = [
        "hi", "hello", "hey", "hai", "yo", "sup", "heya", "hiya", "wassup", "what's up",
        "good morning", "good afternoon", "good evening", "morning", "evening", "afternoon",
        "hi bro", "hello bro", "hey bro", "yo bro", "hi dude", "hello dude",
        "hey man", "hi man", "hello man", "hi friend", "hello friend", "hey friend",
        "hi chennai", "hello chennai", "hey chennai",
        "hi ai", "hello ai", "hey ai", "hi assistant", "hello assistant",
        "hi risk bot", "hello risk bot", "hey risk bot", "hi chennai ai", "hello chennai ai", "hey chennai ai",
        "hi chennai ai chatbot", "hello chennai ai chatbot", "hey chennai ai chatbot",
        "hi chennai chatbot", "hello chennai chatbot", "hey chennai chatbot",
        "hi system", "hello system", "hi bot", "hello bot", "hey bot",
        "hey there", "hello there", "hey you", "hi again"
    ]

    q = query.lower()
    if any(greet in q for greet in greetings):
        bot_reply = f"Hello {st.session_state.username}! 👋 I'm Chennai AI Risk Chatbot. You can ask me about risk factors like accident, flood, pollution, etc. 😊"
        st.session_state.messages.append({
            "role": "assistant",
            "content": bot_reply,
            "time": timestamp
        })
        st.rerun()

    zone, reply_type, bot_reply = None, None, ""


    if "flood" in q or "rain" in q:
        zones = flood_df["Zone"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "flood"
        bot_reply = f"🌊 Flood Data for {zone}" if zone else "❗ Mention a valid area."

    elif "accident" in q:
        zones = accident_df["Zone"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "accident"
        bot_reply = f"🚧 Accidents in {zone}" if zone else "❗ Mention a valid area."

    elif "crime" in q:
        zones = crime_df["Zone"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "crime"
        bot_reply = f"🚔 Crimes in {zone}" if zone else "❗ Mention a valid zone."

    elif "pollution" in q or "air" in q:
        zones = air_df["Zone"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "pollution"
        bot_reply = f"🌫 Air Quality in {zone}" if zone else "❗ Mention a valid zone."

    elif "heat" in q or "temperature" in q:
        zones = heat_df["Zone"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "heat"
        bot_reply = f"🥵 Heat Impact in {zone}" if zone else "❗ Mention a valid zone."

    elif "population" in q:
        zones = population_df["Zone"].dropna().unique()
        zone = find_zone(q, zones)
        reply_type = "population"
        bot_reply = f"👥 Population in {zone}" if zone else "❗ Mention a valid zone."

    elif "risk" in q:
        zone = None
        reply_type = "risk"
        
        specific_factors = {
            "accident": "Accident",
            "pollution": "Air Pollution",
            "air pollution": "Air Pollution",
            "flood": "Flood",
            "heat": "Heat",
            "crime": "Crime",
            "population": "Population"
        }
        
        factor_found = None
        for keyword, column in specific_factors.items():
            if keyword in q:
                factor_found = column
                break
        
        if factor_found:
            bot_reply = f"📊 Risk Factor: {factor_found}"
        else:
            bot_reply = "📊 Overall Risk Factors for All Zones"
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": bot_reply,
            "time": timestamp,
            "type": "risk_detail" if factor_found else "risk_all",
            "factor": factor_found  # save factor for display section
        })
        st.rerun()


    else:
        bot_reply = "❓ Try asking about accidents, air pollution, crime, heat, flood, population, or risk."

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_reply,
        "time": timestamp,
        "type": reply_type,
        "zone": zone
    })
    if st.session_state.username not in all_histories:
        all_histories[st.session_state.username] = {}

    all_histories[st.session_state.username][st.session_state.chat_title] = st.session_state.messages

    with open(HISTORY_FILE, "w") as f:
        json.dump(all_histories, f, indent=2)


    st.rerun()
