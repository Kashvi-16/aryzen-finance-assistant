# bot.py
# Aryzen chatbot backend (guardrails + retrieval + OpenRouter/DeepSeek)

import os
import json
import requests
import glob
import numpy as np
from typing import List


# ============================================================
# LOAD OPENROUTER API KEY (Streamlit Secrets or env)
# ============================================================
def load_openrouter_key() -> str:
    # 1. Streamlit Cloud secrets
    try:
        import streamlit as st
        if "OPENROUTER_API_KEY" in st.secrets:
            return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        pass

    # 2. Local development (env var)
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key.strip()

    raise EnvironmentError("❌ No OpenRouter API key found.")


try:
    OPENROUTER_API_KEY = load_openrouter_key()
except Exception:
    OPENROUTER_API_KEY = None



# ============================================================
# EMBEDDING USING OPENROUTER (cloud safe)
# ============================================================
def embed_text(text: str):
    """Get embeddings from OpenRouter (no HuggingFace downloads)."""

    url = "https://openrouter.ai/api/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-API-Key": OPENROUTER_API_KEY,
        "Content-Type": "application/json",
    }
    data = {
        "model": "text-embedding-3-small",
        "input": text
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]
    except Exception as e:
        print("Embedding Error:", e)
        return None



# ============================================================
# SIMPLE IN-MEMORY VECTOR STORE (no Chroma)
# ============================================================
VECTOR_DB = {}

BASE_PATH = "knowledge_base"

def load_documents():
    docs = []
    ids = []

    for pattern in ["*.txt", "*.md", "*.json"]:
        for file in glob.glob(f"{BASE_PATH}/{pattern}"):
            try:
                text = open(file, "r", encoding="utf-8").read().strip()
                if len(text) > 5:
                    docs.append(text)
                    ids.append(file)
            except:
                pass
    return ids, docs


def ingest_documents():
    ids, docs = load_documents()

    if not docs:
        print("⚠ No documents found inside knowledge_base/")
        return

    print(f"📥 Ingesting {len(docs)} documents...")

    for file, text in zip(ids, docs):
        emb = embed_text(text)
        if emb:
            VECTOR_DB[file] = {
                "text": text,
                "embedding": emb
            }

ingest_documents()



# ============================================================
# RETRIEVAL
# ============================================================
def cosine(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def get_context(query: str, n_results=4) -> List[str]:

    if not VECTOR_DB:
        return []

    query_emb = embed_text(query)
    if query_emb is None:
        return []

    scored = []
    for file, item in VECTOR_DB.items():
        try:
            score = cosine(query_emb, item["embedding"])
            scored.append((score, item["text"]))
        except:
            pass

    scored.sort(reverse=True)
    return [doc for _, doc in scored[:n_results]]



# ============================================================
# FORMAT LLM RESPONSE
# ============================================================
def format_response(raw: str):
    if not raw:
        return "No response."

    raw = raw.strip()

    if ("###" in raw) or ("\n- " in raw):
        return raw

    parts = raw.split(". ")
    short = parts[0] + "."
    detail = ". ".join(parts[1:])

    if detail.strip():
        return f"### Answer\n\n{short}\n\n### Details\n\n{detail}"

    return f"### Answer\n\n{short}"



# ============================================================
# MAIN CHATBOT LOGIC
# ============================================================
def chatbot(query: str) -> str:

    if not query or not query.strip():
        return "Please ask a question related to Aryzen or basic finance."

    q = query.lower()

    # banned terms
    banned = [
        "buy","sell","prediction","future price","best stock",
        "crypto","bitcoin","ethereum","portfolio","advice",
        "suggest","recommend","should i","loan","tax","insurance",
        "policy","predict"
    ]

    for word in banned:
        if word in q:
            return "I’m sorry — I cannot provide investment advice or predictions."

    # allowed topics
    finance_terms = [
        "nav","inflation","deflation","assets","liabilities","aum",
        "capital","risk","return","valuation","equity","bond","fund",
        "market cap","etf","mutual fund","expense ratio"
    ]

    aryzen_terms = [
        "aryzen","aryzen capital","aryzen advisors",
        "aryzen capital advisors","aryzen services","aryzen team"
    ]

    if not any(t in q for t in finance_terms + aryzen_terms):
        return "I can only answer questions related to Aryzen and basic financial concepts."

    context = "\n\n".join(get_context(query))

    system_msg = (
        "You are a corporate assistant for Aryzen Capital Advisors LLP. "
        "ONLY answer questions about Aryzen or basic finance definitions. "
        "Never provide financial advice or predictions."
    )

    messages = [{"role": "system", "content": system_msg}]
    if context:
        messages.append({"role": "system", "content": f"Context:\n{context}"})
    messages.append({"role": "user", "content": query})

    if OPENROUTER_API_KEY is None:
        return "API key missing. Add OPENROUTER_API_KEY in Streamlit Secrets."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-API-Key": OPENROUTER_API_KEY,
        "HTTP-Referer": "http://localhost",
        "X-Title": "aryzen-finance-bot",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={"model": "deepseek/deepseek-chat", "messages": messages},
            timeout=40
        )
        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        return format_response(raw)
    except Exception as e:
        return f"Unexpected error: {e}"
