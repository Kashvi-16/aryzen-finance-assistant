# bot.py
# Aryzen chatbot backend (guardrails + retrieval + OpenRouter/DeepSeek)

import os
import json
import requests
from typing import List
import glob
import chromadb
from sentence_transformers import SentenceTransformer


# --------------------------------------
# Embedding model (lightweight, cloud-safe)
# --------------------------------------
os.environ["SENTENCE_TRANSFORMERS_HOME"] = "/mnt/data"
embedder = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2")

COLLECTION_NAME = "aryzen_finance"

# In-memory Chroma (NO SQLite)
client = chromadb.Client()

# Create new collection each startup
try:
    collection = client.get_collection(COLLECTION_NAME)
except:
    collection = client.create_collection(name=COLLECTION_NAME)


# --------------------------------------
# Load documents from knowledge_base/
# --------------------------------------
BASE_PATH = "knowledge_base"

def load_documents():
    docs, ids = [], []
    patterns = ["*.txt", "*.md", "*.json"]

    for p in patterns:
        for file in glob.glob(f"{BASE_PATH}/{p}"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                    if len(text) > 5:
                        docs.append(text)
                        ids.append(file.replace("/", "_"))
            except:
                pass
    return ids, docs


def ingest_documents():
    ids, docs = load_documents()
    if not docs:
        print("No knowledge base documents loaded.")
        return

    print(f"Ingesting {len(docs)} docs into vector DB...")
    embeddings = embedder.encode(docs).tolist()

    collection.add(
        ids=ids,
        documents=docs,
        embeddings=embeddings
    )


# Run ingestion automatically
ingest_documents()


# --------------------------------------
# Load OpenRouter API Key (Streamlit Secrets)
# --------------------------------------
def load_openrouter_key() -> str:
    # Streamlit Cloud Secrets
    try:
        import streamlit as st
        if "OPENROUTER_API_KEY" in st.secrets:
            return st.secrets["OPENROUTER_API_KEY"]
    except:
        pass

    # Local environment variable
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key.strip()

    raise EnvironmentError("OpenRouter API key not found.")


try:
    OPENROUTER_API_KEY = load_openrouter_key()
except:
    OPENROUTER_API_KEY = None


# --------------------------------------
# Helper: clean model output formatting
# --------------------------------------
def format_response(raw_text: str) -> str:
    if not raw_text:
        return "No response from model."

    text = raw_text.strip()

    # If it's already Markdown/bullets
    if ("###" in text) or ("\n- " in text) or ("\n* " in text):
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        return text

    # Otherwise structure it
    sentences = [s.strip() for s in text.split(". ") if s.strip()]
    if not sentences:
        return text

    short = sentences[0].rstrip(".")
    remaining = ". ".join(sentences[1:]).strip()

    out = f"### Answer\n\n{short}.\n"
    if remaining:
        out += f"\n### Details\n\n{remaining}"
    return out


# --------------------------------------
# Retrieval from vector DB
# --------------------------------------
def get_context(query: str, n_results=4):
    if not query:
        return []

    q_emb = embedder.encode(query).tolist()

    try:
        results = collection.query(query_embeddings=[q_emb], n_results=n_results)
    except:
        return []

    docs = results.get("documents", [])
    if isinstance(docs, list) and len(docs) > 0 and isinstance(docs[0], list):
        docs = docs[0]

    return [d for d in docs if d]


# --------------------------------------
# CHATBOT FUNCTION
# --------------------------------------
def chatbot(query: str) -> str:
    if not query.strip():
        return "Please ask a question related to Aryzen or basic finance."

    q = query.lower()

    # Forbidden financial advice terms
    banned = [
        "buy", "sell", "stock", "prediction", "future price",
        "crypto", "bitcoin", "ethereum", "portfolio",
        "advice", "recommend", "should i", "loan",
        "tax", "insurance", "policy", "predict"
    ]
    for b in banned:
        if b in q:
            return "I’m sorry — I cannot provide investment advice or predictions."

    # Allowed categories
    finance_terms = [
        "nav", "inflation", "deflation", "assets", "liabilities", "aum",
        "capital", "risk", "valuation", "equity", "bond", "fund",
        "market cap", "etf", "mutual fund", "expense ratio"
    ]

    aryzen_terms = ["aryzen", "aryzen capital", "aryzen advisors", "aryzen team"]

    if not any(t in q for t in finance_terms) and not any(t in q for t in aryzen_terms):
        return "I answer only questions related to **Aryzen** or **basic finance concepts**."

    # Retrieve context
    context_docs = get_context(query)
    context_text = "\n\n".join(context_docs) if context_docs else ""

    system_message = (
        "You are a corporate assistant for Aryzen Capital Advisors LLP. "
        "ONLY answer questions about Aryzen or basic finance terms. "
        "NEVER provide investment advice, predictions, or recommendations."
    )

    messages = [{"role": "system", "content": system_message}]
    if context_text:
        messages.append({"role": "system", "content": f"Context:\n{context_text}"})
    messages.append({"role": "user", "content": query})

    if OPENROUTER_API_KEY is None:
        return "API key missing. Add OPENROUTER_API_KEY in Streamlit Secrets."

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-API-Key": OPENROUTER_API_KEY,
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "aryzen-finance-assistant",
        "Content-Type": "application/json",
    }

    # --- FIXED: Correct DeepSeek model + real error reporting ---
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "deepseek/deepseek-v3",
                "messages": messages
            },
            timeout=40
        )

        data = r.json()

        # If OpenRouter returns an error → show it
        if "error" in data:
            return f"API Error: {data['error']['message']}"

        return f"RAW API RESPONSE:\n\n{json.dumps(data, indent=2)}"

        

    except Exception as e:
        return f"Request failed: {e}"


# --------------------------------------
# Local test mode
# --------------------------------------
if __name__ == "__main__":
    while True:
        q = input("\nAsk: ")
        print(chatbot(q))







