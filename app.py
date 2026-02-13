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
from streamlit_option_menu import option_menu

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
    /* Clean Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    section[data-testid="stSidebar"] .stRadio > label {
        color: #9ca3af;
        font-weight: 600;
        text-transform: uppercase;
        font-size: 0.8rem;
        margin-bottom: 10px;
    }
    .stMetric {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5);
    }
    .post-card {
        background-color: #1a1c23;
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #3e4451;
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
    .stat-badge {
        background: #374151;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        margin-right: 10px;
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
    st.markdown("""
        <div style="padding: 10px 0px;">
            <h2 style="color: #ff4b4b; text-align: center;">🏍️ RUSI HUB</h2>
            <p style="text-align: center; color: #8a8d91; font-size: 0.8em;">Business Management v1.2</p>
        </div>
    """, unsafe_allow_html=True)
    
    app_mode = option_menu(
        menu_title=None,
        options=["Dashboard", "Comments Hub", "Inbox", "Recorded Data", "Rusi Inventory"],
        icons=["speedometer2", "chat-dots", "envelope", "archive", "bicycle"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#ff4b4b", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "16px", 
                "text-align": "left", 
                "margin": "5px", 
                "color": "#ffffff",
                "--hover-color": "#262730"
            },
            "nav-link-selected": {"background-color": "#ff4b4b", "font-weight": "normal"},
        }
    )
    
    # Map the menu names back to the app_mode logic if needed
    mode_map = {
        "Dashboard": "📊 Dashboard",
        "Comments Hub": "💬 Comments Hub",
        "Inbox": "✉️ Inbox",
        "Recorded Data": "📓 Recorded Data",
        "Rusi Inventory": "🏍️ Rusi Inventory"
    }
    app_mode = mode_map[app_mode]

    st.spacer = st.container()
    with st.spacer:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh System", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # Move Page Info to the bottom for a cleaner look
    try:
        page_info = fb.get_page_info()
        with st.expander("📡 LIVE STATUS", expanded=False):
            st.write(f"**{page_info.get('name')}**")
            st.write(f"👥 Fans: **{page_info.get('fan_count'):,}**")
            st.markdown(f"[View Page ↗️]({page_info.get('link')})")
    except:
        pass

# --- HELPER FUNCTIONS ---
def get_sentiment(text):
    blob = TextBlob(text)
    score = blob.sentiment.polarity
    if score > 0.1: return "Positive 😊", "sentiment-pos"
    if score < -0.1: return "Negative 😠", "sentiment-neg"
    return "Neutral 😐", ""

# --- DASHBOARD ---
if app_mode == "📊 Dashboard":
    st.title("Business Social Feed")
    
    posts = fb.get_posts(limit=10)
    
    if not posts:
        st.info("No recent posts found.")
    else:
        for p in posts:
            with st.container():
                st.markdown(f'<div class="post-card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if 'full_picture' in p:
                        st.image(p['full_picture'], use_container_width=True)
                
                with col2:
                    st.write(f"**Posted on:** {p['created_time'][:16]}")
                    msg = p.get('message', '*No text content*')
                    st.markdown(f'<p style="font-size: 1.1em; color: #ffd700;">{msg[:200]}...</p>', unsafe_allow_html=True)
                    
                    # Reactions and Comments Summary
                    reacts = p.get('reactions', {}).get('summary', {}).get('total_count', 0)
                    comm_count = p.get('comments', {}).get('summary', {}).get('total_count', 0)
                    
                    st.markdown(f"""
                    <span class="stat-badge">👍 {reacts} Reactions</span>
                    <span class="stat-badge">💬 {comm_count} Comments</span>
                    """, unsafe_allow_html=True)
                    
                    # Interaction Buttons
                    if st.button(f"View Comments ({comm_count})", key=f"post_{p['id']}"):
                        st.session_state.selected_post = p['id']
                        st.session_state.selected_post_msg = p.get('message', 'Post')
                        # Note: We'll show these below or redirect
                        st.toast("Opening comments...")

                st.markdown('</div>', unsafe_allow_html=True)

        if "selected_post" in st.session_state:
            st.divider()
            st.subheader(f"Comments for: {st.session_state.selected_post_msg[:50]}...")
            if st.button("Close Comments"):
                del st.session_state.selected_post
                st.rerun()
                
            post_comments = fb.get_comments(st.session_state.selected_post)
            if post_comments:
                for c in post_comments:
                    with st.chat_message("user"):
                        st.write(f"**{c.get('from', {}).get('name', 'User')}**")
                        st.write(c['message'])
                        st.caption(f"Likes: {c.get('like_count', 0)} | {c['created_time'][:16]}")
                        
                        # Reply within Dashboard
                        with st.expander("Reply"):
                            rep_val = st.text_input("Message", key=f"dash_rep_{c['id']}")
                            if st.button("Send", key=f"dash_btn_{c['id']}"):
                                fb.reply_to_comment(c['id'], rep_val)
                                st.success("Reply sent!")
            else:
                st.info("No comments yet on this post.")

# --- COMMENTS HUB ---
elif app_mode == "💬 Comments Hub":
    st.title("Activity Feed & Interactions")
    st.write("Track and respond to all recent engagement across your page.")
    
    with st.spinner("Synching all recent comments..."):
        all_comments = fb.get_all_recent_comments(post_limit=5)
    
    if all_comments:
        for c in all_comments:
            # Record it automatically in Local DB
            save_comment(c['id'], c.get('from', {}).get('name', 'Anonymous'), c['message'], c['post_id'], c['created_time'])
            
            sentiment_text, sentiment_class = get_sentiment(c['message'])
            
            with st.container():
                st.markdown(f"""
                <div class="comment-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div style="display: flex; align-items: center;">
                            <img src="{c.get('from', {}).get('picture', {}).get('data', {}).get('url', 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y')}" 
                                 style="width: 40px; height: 40px; border-radius: 50%; margin-right: 12px; border: 2px solid #ff4b4b;">
                            <b>{c.get('from', {}).get('name', 'User')}</b>
                        </div>
                        <span class="{sentiment_class}" style="font-weight: bold;">{sentiment_text}</span>
                    </div>
                    <div style="background: #1a1c23; padding: 15px; border-radius: 8px; border-left: 4px solid #ff4b4b;">
                        <p style="font-size: 1.15em; color: #ffffff; margin: 0;">"{c['message']}"</p>
                    </div>
                    <div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <small style="color: #8a8d91;">🕒 {c['created_time'][:16]} | On Post: {c['post_message'][:30]}...</small>
                        <span style="color: #ff4b4b; font-size: 0.9em;">❤️ {c.get('like_count', 0)} Likes</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Auto-reply suggestions
                msg_lower = c['message'].lower()
                auto_reply = ""
                if any(word in msg_lower for word in ["price", "how much", "hm", "magkano"]):
                    auto_reply = "Hi! Thank you for your interest in RUSI. For the best pricing and downpayment options, please visit our nearest branch! 🏍️"
                elif any(word in msg_lower for word in ["loc", "where", "saan"]):
                    auto_reply = "Hello! We have branches nationwide. Let us know your city so we can find the nearest one for you! 📍"
                
                # Enhanced Reply UI
                with st.expander("🗨️ Click to Respond"):
                    reply_msg = st.text_area("Your response", value=auto_reply, key=f"feed_rep_{c['id']}", height=80)
                    if st.button("🚀 Post Reply", key=f"feed_btn_{c['id']}"):
                        if reply_msg:
                            res = fb.reply_to_comment(c['id'], reply_msg)
                            if "id" in res:
                                st.success("Reply successfully posted to Facebook!")
                            else:
                                st.error(f"Error: {res}")
                        else:
                            st.warning("Please type a message first.")
    else:
        st.info("No recent comments found to display.")

# --- INBOX ---
elif app_mode == "✉️ Inbox":
    st.title("📭 Messenger Hub")
    
    with st.spinner("Loading conversations..."):
        conversations = fb.get_messages()

    if not conversations:
        st.info("No recent conversations found.")
    else:
        # Create a layout with a sidebar-like list of chats and a main view for messages
        chat_col, msg_col = st.columns([1, 2])

        # Prepare chat list
        chat_options = {}
        for conv in conversations:
            # Get the participant who is not the page
            participants = conv.get('participants', {}).get('data', [])
            sender_name = "Unknown"
            sender_id = ""
            for p in participants:
                if p.get('id') != PAGE_ID:
                    sender_name = p.get('name', 'Anonymous')
                    sender_id = p.get('id')
                    break
            
            label = f"{sender_name} (Updated: {conv['updated_time'][:16]})"
            chat_options[label] = {"id": conv['id'], "sender_name": sender_name, "sender_id": sender_id}

        with chat_col:
            st.subheader("Chats")
            selected_chat_label = st.radio("Select a conversation", list(chat_options.keys()), label_visibility="collapsed")
            selected_chat = chat_options[selected_chat_label]

        with msg_col:
            st.subheader(f"Chat with {selected_chat['sender_name']}")
            
            # Fetch and display history
            history = fb.get_conversation_history(selected_chat['id'])
            if history:
                # Reverse to show newest at bottom
                for msg in reversed(history):
                    is_me = msg.get('from', {}).get('id') == PAGE_ID
                    align = "right" if is_me else "left"
                    bg_color = "#0084ff" if is_me else "#3e4042"
                    text_color = "white"
                    
                    st.markdown(f"""
                    <div style="display: flex; flex-direction: column; align-items: {'flex-end' if is_me else 'flex-start'}; margin-bottom: 10px;">
                        <div style="background-color: {bg_color}; color: {text_color}; padding: 10px 15px; border-radius: 18px; max-width: 80%; word-wrap: break-word;">
                            {msg.get('message', '')}
                        </div>
                        <small style="color: #8a8d91; margin-top: 2px;">{msg.get('created_time')[:16]}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            # Reply Input
            with st.form(key=f"msg_form_{selected_chat['id']}", clear_on_submit=True):
                reply_text = st.text_area("Type a message...", placeholder="Hello! How can we help you with your Rusi bike today?")
                submit_btn = st.form_submit_button("💨 Send Message")
                
                if submit_btn and reply_text:
                    res = fb.send_private_message(selected_chat['sender_id'], reply_text)
                    if "message_id" in res:
                        st.success("Message sent!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to send: {res}")

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
