import streamlit as st
import pandas as pd
import time
import threading
import requests
from fb_utils import FacebookManager
from datetime import datetime
import plotly.express as px
import sqlite3
import os
from textblob import TextBlob

# --- PAGE CONFIG ---
st.set_page_config(page_title="RUSI Hub | FB Auto-Manager", page_icon="🏍️", layout="wide")

# --- CUSTOM CSS FOR STYLING ---
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stApp {
        color: #ffffff;
    }
    .stMetric {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    .comment-card {
        background-color: #262730;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        border: 1px solid #3e4451;
        transition: transform 0.2s;
    }
    .comment-card:hover {
        transform: scale(1.01);
        border-color: #ff4b4b;
    }
    .bike-header {
        color: #ff4b4b;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        letter-spacing: 2px;
    }
    .sentiment-pos { color: #10b981; }
    .sentiment-neg { color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# --- CONFIG & INITIALIZATION ---
ACCESS_TOKEN = "EAF2xZBKUAR7oBQpwCYzKNv3lcN1jXtKtLWo9yhkSHVfYdcZBiYHs9qVFVUXc2145pfj2h3OUDO8XeTqBPocP7KMGf2N0dcUVWmedJDEEYLVUIyGhfcYyCEGEPcPSo3a4X7DqN2RUmBK5V7PBpgRvHDrcIGrmBjw3GYDI1nn8oihEIKCc79LOphEIEg2OIYybZBd"
PAGE_ID = "831829270014292"
fb = FacebookManager(ACCESS_TOKEN, PAGE_ID)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('rusi_records.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS comments 
                 (id TEXT PRIMARY KEY, from_name TEXT, message TEXT, post_id TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id TEXT PRIMARY KEY, sender TEXT, message TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

def save_comment(c_id, name, msg, p_id, date):
    conn = sqlite3.connect('rusi_records.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO comments VALUES (?,?,?,?,?)", (c_id, name, msg, p_id, date))
    conn.commit()
    conn.close()

init_db()

# --- RENDER STAY-AWAKE (KEEP-ALIVE) ---
def keep_alive():
    # Ping itself every 10 minutes to prevent Render sleep (if URL is set)
    app_url = os.getenv("RENDER_EXTERNAL_URL")
    if app_url:
        while True:
            try:
                requests.get(app_url)
                print(f"Keep-alive ping sent to {app_url}")
            except Exception as e:
                print(f"Keep-alive error: {e}")
            time.sleep(600) # 10 mins

if "keep_alive_started" not in st.session_state:
    threading.Thread(target=keep_alive, daemon=True).start()
    st.session_state.keep_alive_started = True

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 class='bike-header'>🏍️ RUSI HUB</h1>", unsafe_allow_html=True)
    st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_mR3Rk1-E8eOsh5tKj2R1V2H1z8w_m6x-Vw&s", caption="Rusi Motorcycle Hub") # Placeholder for Rusi logo
    
    try:
        page_info = fb.get_page_info()
        st.write(f"**Page:** {page_info.get('name')}")
        st.write(f"**Fans:** 📈 {page_info.get('fan_count'):,}")
        st.markdown(f"[Go to Page]({page_info.get('link')})")
    except:
        st.warning("Failed to fetch page info. Check token.")

    st.divider()
    app_mode = st.radio("Navigation", ["📊 Dashboard", "💬 Comments Hub", "✉️ Inbox", "📓 Recorded Data", "🏍️ Rusi Inventory"])
    
    if st.button("🔄 Sync Now"):
        st.cache_data.clear()
        st.rerun()

# --- HELPER FUNCTIONS ---
def get_sentiment(text):
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    if score > 0.1: return "Positive 😊", "sentiment-pos"
    if score < -0.1: return "Negative 😠", "sentiment-neg"
    return "Neutral 😐", ""

# --- DASHBOARD ---
if app_mode == "📊 Dashboard":
    st.title("Business Overview")
    
    col1, col2, col3 = st.columns(3)
    posts = fb.get_posts(limit=10)
    
    with col1:
        st.metric("Recent Posts", len(posts))
    with col2:
        # Simple engagement metric
        st.metric("Engagement Status", "High 🔥" if len(posts) > 5 else "Moderate")
    with col3:
        st.metric("Status", "🟢 Active", delta="Live Sync")

    st.subheader("Engagement Analytics")
    if posts:
        df_posts = pd.DataFrame(posts)
        # Using post 'created_time' for a simple trend
        df_posts['date'] = pd.to_datetime(df_posts['created_time']).dt.date
        trend = df_posts.groupby('date').size().reset_index(name='Post Count')
        fig = px.area(trend, x='date', y='Post Count', title="Post Frequency", color_discrete_sequence=['#ff4b4b'])
        st.plotly_chart(fig, use_container_width=True)

# --- COMMENTS HUB ---
elif app_mode == "💬 Comments Hub":
    st.title("Real-time Engagement")
    st.write("Fetching latest comments from recent posts...")
    
    with st.spinner("Synching comments..."):
        all_comments = fb.get_all_recent_comments(post_limit=5)
    
    if all_comments:
        for c in all_comments:
            # Record it automatically
            save_comment(c['id'], c.get('from', {}).get('name', 'Anonymous'), c['message'], c['post_id'], c['created_time'])
            
            sentiment_text, sentiment_class = get_sentiment(c['message'])
            
            with st.container():
                st.markdown(f"""
                <div class="comment-card">
                    <div style="display: flex; justify-content: space-between;">
                        <b>👤 {c.get('from', {}).get('name', 'User')}</b>
                        <span class="{sentiment_class}">{sentiment_text}</span>
                    </div>
                    <p style="font-size: 1.1em; color: #ffd700; margin: 10px 0;">"{c['message']}"</p>
                    <small>🕒 {c['created_time']} | On Post: {c['post_message'][:40]}...</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Auto-reply suggestions
                msg_lower = c['message'].lower()
                auto_reply = ""
                if "how much" in msg_lower or "price" in msg_lower:
                    auto_reply = "Hello! For pricing, please visit our nearest branch or DM us for a quote based on your location. 🏍️"
                elif "location" in msg_lower or "where" in msg_lower:
                    auto_reply = "We have branches nationwide! Please check our page's 'About' section for the one nearest to you."
                
                # Reply UI
                cols = st.columns([4, 1])
                with cols[0]:
                    reply_msg = st.text_input("Quick Reply", value=auto_reply, key=c['id'])
                with cols[1]:
                    if st.button("🚀 Send", key=f"btn_{c['id']}"):
                        if reply_msg:
                            res = fb.reply_to_comment(c['id'], reply_msg)
                            st.toast("Reply sent!" if "id" in res else f"Error: {res}")
                        else:
                            st.warning("Message empty")
    else:
        st.info("No comments found on the last 5 posts.")

# --- INBOX ---
elif app_mode == "✉️ Inbox":
    st.title("Messenger Hub")
    st.warning("Messages require specific Page Permissions (pages_messaging). Ensure your token has them.")
    
    conversations = fb.get_messages()
    
    if isinstance(conversations, list):
        if not conversations:
            st.info("No recent conversations found.")
        for conv in conversations:
            sender = conv.get('senders', {}).get('data', [{}])[0].get('name', 'Unknown')
            last_msg = conv.get('messages', {}).get('data', [{}])[0].get('message', 'No message')
            
            with st.expander(f"✉️ {sender} (Last updated: {conv['updated_time']})"):
                st.write(f"**Last Message:** {last_msg}")
                # More message history can be expanded here
    else:
        st.error("Could not fetch messages. Likely permission related.")

# --- RECORDED DATA ---
elif app_mode == "📓 Recorded Data":
    st.title("Recorded Activity History")
    
    st.subheader("Archived Comments")
    conn = sqlite3.connect('rusi_records.db')
    try:
        df_c = pd.read_sql_query("SELECT * FROM comments ORDER BY created_at DESC", conn)
        if not df_c.empty:
            st.dataframe(df_c, use_container_width=True)
            st.download_button("Download CSV", df_c.to_csv(index=False), "rusi_comments.csv", "text/csv")
        else:
            st.info("No records saved yet. Visit the Comments Hub to sync data.")
    except Exception as e:
        st.error(f"DB Error: {e}")
    finally:
        conn.close()

# --- RUSI INVENTORY ---
elif app_mode == "🏍️ Rusi Inventory":
    st.title("🏍️ Rusi Model Showcase")
    st.write("Current line-up management (Static Placeholder for demo)")
    
    models = [
        {"name": "Rusi Classic 250", "type": "Classic", "price": "₱75,000", "img": "https://img.youtube.com/vi/q_G6vGf4EKE/sddefault.jpg"},
        {"name": "Rusi RFI 175", "type": "Scooter", "price": "₱62,000", "img": "https://i.ytimg.com/vi/3P9xat20_0g/maxresdefault.jpg"},
        {"name": "Rusi Titan 250", "type": "Sport", "price": "₱85,000", "img": "https://i.ytimg.com/vi/R2O4_2X_NfE/maxresdefault.jpg"}
    ]
    
    cols = st.columns(3)
    for i, model in enumerate(models):
        with cols[i % 3]:
            st.image(model['img'], use_container_width=True)
            st.subheader(model['name'])
            st.write(f"**Type:** {model['type']}")
            st.write(f"**Starting at:** {model['price']}")
            st.button("Edit Specs", key=f"edit_{i}")

# --- FOOTER ---
st.divider()
st.markdown("<center><small>Powered by Gemini 3 Flash | RUSI Motorcycle Management System v1.0</small></center>", unsafe_allow_html=True)
