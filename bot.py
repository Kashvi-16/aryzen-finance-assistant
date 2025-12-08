# bot.py
# Aryzen chatbot backend (guardrails + retrieval + OpenRouter/DeepSeek)

import os
import json
import requests
from typing import List

# --- NEW: Load dotenv ---
from dotenv import load_dotenv
load_dotenv()  # <---- loads .env automatically

# --- Embedding + Vector DB (Chroma) — Streamlit Cloud Safe (In-Memory) ---
import glob
from sentence_transformers import SentenceTransformer
import chromadb

COLLECTION_NAME = "aryzen_finance"
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Always use in-memory Chroma (persistent mode breaks on Streamlit Cloud)
client = chromadb.Client()

# Create fresh collection every startup (safe for cloud)
try:
    collection = client.get_collection(COLLECTION_NAME)
except:
    collection = client.create_collection(name=COLLECTION_NAME)

# -----------------------------
# AUTOMATIC INGESTION from knowledge_base/
# -----------------------------
BASE_PATH = "knowledge_base"

def load_documents():
    docs = []
    ids = []

    patterns = ["*.txt", "*.md", "*.json"]

    for pattern in patterns:
        for file in glob.glob(f"{BASE_PATH}/{pattern}"):
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
        print("No documents found inside knowledge_base/.")
        return

    print(f"Ingesting {len(docs)} documents from knowledge_base/...")

    embeddings = embedder.encode(docs).tolist()
    collection.add(
        ids=ids,
        documents=docs,
        embeddings=embeddings
    )

# Run ingestion automatically when bot.py loads
ingest_documents()



# -------------------------
# Load OpenRouter API key (Now includes dotenv!!!)
# -------------------------
def load_openrouter_key() -> str:
    """
    Priority for loading API key:
    1. .env → OPENROUTER_API_KEY
    2. Environment variable
    3. AWS Secrets Manager (optional)
    """

    # LOAD FROM .env (dotenv) — NEW
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key.strip()

    # LOAD FROM AWS Secrets Manager if configured
    secret_name = os.environ.get("OPENROUTER_SECRET_NAME")
    if secret_name:
        try:
            import boto3
            sm = boto3.client("secretsmanager")
            resp = sm.get_secret_value(SecretId=secret_name)
            secret = json.loads(resp["SecretString"])
            for k in ("api_key", "openrouter_api_key", "OPENROUTER_API_KEY", "key"):
                if k in secret:
                    return secret[k].strip()
        except Exception:
            pass

    raise EnvironmentError(
        "OpenRouter API key not found.\n"
        "Create a .env file containing:\n"
        "OPENROUTER_API_KEY=yourkeyhere\n"
    )


# Load key now
try:
    OPENROUTER_API_KEY = load_openrouter_key()
except Exception:
    OPENROUTER_API_KEY = None


# -------------------------
# Format responses
# -------------------------
def format_response(raw_text: str) -> str:
    if not raw_text:
        return "No response from model."

    text = raw_text.strip()

    if ("###" in text) or ("\n- " in text) or ("\n* " in text):
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        return text

    sentences = [s.strip() for s in text.split(". ") if s.strip()]

    if not sentences:
        return text

    short = sentences[0].rstrip(".")
    remaining = ". ".join(sentences[1:]).strip()

    md = f"### Answer\n\n{short}.\n"
    if remaining:
        md += f"\n### Details\n\n{remaining}"
    return md


# -------------------------
# Retrieval
# -------------------------
def get_context(query: str, n_results=4) -> List[str]:
    if not query or not collection:
        return []

    query_emb = embedder.encode(query).tolist()

    try:
        results = collection.query(query_embeddings=[query_emb], n_results=n_results)
    except TypeError:
        results = collection.query(query_embeddings=[query_emb], n_results=n_results)

    docs = results.get("documents", [])
    if isinstance(docs, list) and len(docs) > 0 and isinstance(docs[0], list):
        docs = docs[0]

    docs = [str(d).strip() for d in docs if d and str(d).strip()]
    return docs


# -------------------------
# CHATBOT FUNCTION
# -------------------------
def chatbot(query: str) -> str:

    if not query or not query.strip():
        return "Please ask a question related to Aryzen or basic finance."

    q = query.lower()

    # Banned terms
    banned = [
        "buy", "sell", "which stock", "prediction", "future price", "best stock",
        "crypto", "bitcoin", "ethereum", "portfolio", "advice", "suggest",
        "recommend", "should i", "loan", "tax", "insurance", "policy", "predict"
    ]
    for b in banned:
        if b in q:
            return (
                "I’m sorry — I cannot provide investment advice or predictions."
            )

    # Allowed finance terms
    finance_terms = [
        "nav", "inflation", "deflation", "assets", "liabilities", "aum", "capital",
        "risk", "return", "valuation", "equity", "bond", "fund", "market cap",
        "etf", "mutual fund", "expense ratio"
    ]

    # Allowed Aryzen terms
    aryzen_terms = [
        "aryzen", "aryzen capital", "aryzen advisors",
        "aryzen capital advisors", "aryzen services", "aryzen team"
    ]

    if not any(t in q for t in finance_terms) and not any(t in q for t in aryzen_terms):
        return (
            "I can only answer questions related to **Aryzen Capital Advisors** "
            "and basic financial concepts."
        )

    context_docs = get_context(query, 4)
    context_text = "\n\n".join(context_docs) if context_docs else ""

    system_msg = (
        "You are a corporate assistant for Aryzen Capital Advisors LLP. "
        "ONLY answer questions about Aryzen or basic financial terminology. "
        "Do NOT give investment advice or predictions."
    )

    messages = [
        {"role": "system", "content": system_msg},
    ]
    if context_text:
        messages.append({"role": "system", "content": f"Context:\n{context_text}"})

    messages.append({"role": "user", "content": query})

    if OPENROUTER_API_KEY is None:
        return "API key missing. Create `.env` with OPENROUTER_API_KEY=... "

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-API-Key": OPENROUTER_API_KEY,
        "HTTP-Referer": "http://localhost",
        "X-Title": "aryzen-finance-bot",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={"model": "deepseek/deepseek-chat", "messages": messages},
            timeout=20
        )
    except Exception as e:
        return f"Network error: {e}"

    try:
        data = resp.json()
    except:
        return resp.text

    try:
        raw = data["choices"][0]["message"]["content"]
        return format_response(raw)
    except:
        return f"Unexpected response: {data}"


# Quick test
if __name__ == "__main__":
    print("Bot ready. Ask:")
    q = input("> ")
    print(chatbot(q))
