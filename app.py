# app.py — UI for Aryzen Finance Assistant (Streamlit + RAG)

import streamlit as st
from bot import chatbot
import os

# Page settings
LOGO = os.path.join("assets", "logo.png")
USER_AVATAR = os.path.join("assets", "user.png")
BOT_AVATAR = os.path.join("assets", "bot.png")

st.set_page_config(page_title="Aryzen Finance Assistant", layout="centered")


# -------------------------------------
# CSS
# -------------------------------------
st.markdown("""
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
section.main { background: var(--bg); }

/* Headings */
h1 { font-family: 'Lora', serif; color: var(--navy); font-size:32px; }
p, label, input, textarea { font-family: 'Inter', sans-serif; color: var(--dark); }

/* Input box */
.stTextInput>div>div>input {
  border-radius: 10px !important;
  border: 1px solid rgba(11,47,88,0.15) !important;
  padding: 12px !important;
}
.stTextArea>div>div>textarea {
  border-radius: 10px !important;
  border: 1px solid rgba(11,47,88,0.15) !important;
  padding: 12px !important;
}

/* Button */
.stButton>button {
  background-color: var(--gold) !important;
  color: black !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  padding: 8px 18px !important;
  border: none !important;
  box-shadow: 0 2px 6px rgba(0,0,0,0.12);
}

/* Chat bubbles */
.user-msg {
  background-color: var(--navy);
  color: white;
  padding: 12px 16px;
  border-radius: 14px;
  max-width: 80%;
  display: inline-block;
}
.bot-msg {
  background-color: var(--card);
  color: var(--dark);
  padding: 12px 16px;
  border-left: 4px solid var(--emerald);
  border-radius: 10px;
  max-width: 80%;
  display: inline-block;
}

.avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
}

.chat-row { margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)


# -------------------------------------
# Header
# -------------------------------------
col1, col2 = st.columns([0.18, 0.82])
with col1:
    if os.path.exists(LOGO):
        st.image(LOGO, width=90)
with col2:
    st.markdown("<h1>Aryzen Finance Assistant</h1>", unsafe_allow_html=True)
    st.write("Trusted answers on **Aryzen Capital Advisors** and basic financial terminology.")


# -------------------------------------
# Chat history
# -------------------------------------
if "history" not in st.session_state:
    st.session_state["history"] = []     # (role, text)


def safe_image(path):
    try:
        if os.path.exists(path):
            st.image(path, width=48)
            return True
    except:
        pass
    return False


def render_message(role, text):
    avatar_col, bubble_col = st.columns([0.12, 0.88])

    with avatar_col:
        if role == "You":
            safe_image(USER_AVATAR)
        else:
            safe_image(BOT_AVATAR)

    with bubble_col:
        bubble_class = "user-msg" if role == "You" else "bot-msg"
        st.markdown(
            f"<div class='chat-row'><div class='{bubble_class}'>{text}</div></div>",
            unsafe_allow_html=True
        )


# Render existing chat
for role, msg in st.session_state["history"]:
    render_message(role, msg)


# -------------------------------------
# Input box
# -------------------------------------
query = st.text_input("Ask your question:")

if st.button("Send"):
    if query.strip():
        st.session_state["history"].append(("You", query))

        try:
            response = chatbot(query)
        except Exception as e:
            response = f"Backend error: {e}"

        st.session_state["history"].append(("Bot", response))
    else:
        st.warning("Please enter a question.")


# -------------------------------------
# Footer
# -------------------------------------
st.markdown("---")
st.markdown(
    "This assistant only answers Aryzen-related questions and basic finance terms. "
    "**No investment advice is provided.**"
)








