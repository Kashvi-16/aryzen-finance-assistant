# app.py — refined UI based on your last working code
import streamlit as st
from bot import chatbot  # your backend
import os
import re

# Page settings
LOGO = os.path.join("assets", "logo.png")
USER_AVATAR = os.path.join("assets", "user.png")
BOT_AVATAR = os.path.join("assets", "bot.png")

st.set_page_config(page_title="Aryzen Finance Assistant", page_icon="💼", layout="centered")

# -------------------------
# CSS: navy + gold + layout
# -------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@400;600&family=Inter:wght@300;400;500&display=swap');

:root{
  --navy: #0B2F58;
  --dark: #333333;
  --emerald: #2E7D32;
  --gold: #FFD700;
  --bg: #ffffff;
  --card: #F5F5F5;
}

/* Page */
section.main {
  background: var(--bg);
}

/* Headings */
h1 { font-family: 'Lora', serif; color: var(--navy); font-size:32px; }
p, label, input, textarea { font-family: 'Inter', sans-serif; color: var(--dark); }

/* Input box */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
  border-radius: 10px !important;
  border: 1px solid rgba(11,47,88,0.12) !important;
  padding: 12px !important;
  background: #666;
}

/* Buttons: gold */
.stButton>button {
  background-color: var(--gold) !important;
  color: #000 !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  padding: 8px 18px !important;
  border: none !important;
  box-shadow: 0 2px 6px rgba(0,0,0,0.12);
}

/* Chat bubbles */
.user-msg {
  background-color: var(--navy);
  color: #ffffff;
  padding: 12px 16px;
  border-radius: 14px;
  display: inline-block;
  max-width: 80%;
  line-height: 1.5;
}
.bot-msg {
  background-color: var(--card);
  color: var(--dark);
  padding: 12px 16px;
  border-left: 4px solid var(--emerald);
  border-radius: 10px;
  display: inline-block;
  max-width: 80%;
  line-height: 1.5;
}

/* Avatar */
.avatar {
  width:48px; height:48px; border-radius:50%; object-fit:cover;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

/* small spacing tweaks */
.chat-row { margin-bottom: 12px; padding-top:6px; padding-bottom:6px; }
</style>
""",
    unsafe_allow_html=True,
)

# -------------------------
# Header
# -------------------------
cols = st.columns([0.12, 0.88])
with cols[0]:
    if os.path.exists(LOGO):
        st.image(LOGO, width=96)
with cols[1]:
    st.markdown("<h1>Aryzen Finance Assistant</h1>", unsafe_allow_html=True)
    st.write("Trusted answers on **Aryzen Capital Advisors** and **financial terminology**.")

# -------------------------
# Chat history session
# -------------------------
if "history" not in st.session_state:
    st.session_state["history"] = []  # list of tuples: (role, text)

# -------------------------
# Helper: safely show avatar image (no PIL errors)
# -------------------------
def safe_image(path, width=48):
    """
    Show image if path exists and is a file readable by Streamlit.
    Avoid calling PIL on invalid bytes.
    """
    try:
        if path and os.path.exists(path) and os.path.isfile(path):
            st.image(path, width=width)
            return True
    except Exception:
        # do nothing (avoid crashing UI)
        pass
    return False

# -------------------------
# Render function: left avatar + right bubble for bot/user
# -------------------------
def render_message(role, text):
    # Use two columns: avatar (small) + bubble (large)
    col_avatar, col_bubble = st.columns([0.08, 0.92])
    with col_avatar:
        if role == "You":
            safe_image(USER_AVATAR, width=48)
        else:
            safe_image(BOT_AVATAR, width=48)
    with col_bubble:
        # Decide bubble class
        bubble_class = "user-msg" if role == "You" else "bot-msg"
        # Render markdown safely (we assume bot returns markdown/plain text)
        st.markdown(f"<div class='chat-row'><div class='{bubble_class}'>{text}</div></div>", unsafe_allow_html=True)

# render history
for r, m in st.session_state["history"]:
    render_message(r, m)

# -------------------------
# Input area
# -------------------------
query = st.text_input("Ask your question:")

# send logic: append to history and call backend; do NOT call experimental_rerun
if st.button("Send"):
    if not query.strip():
        st.warning("Please enter a question.")
    else:
        # show user message locally
        st.session_state["history"].append(("You", query))
        # call your backend synchronously
        try:
            answer = chatbot(query)
        except Exception as e:
            answer = f"Error from backend: {e}"
        st.session_state["history"].append(("Bot", answer))
        # Do NOT attempt to programmatically rerun; the button click already triggers re-run.

# ----------------------------------
# Small hint + footer
# ----------------------------------
st.markdown("---")
st.markdown("**Note:** This assistant answers Aryzen-related and basic finance questions only. It does not provide investment advice.")




