# bot.py — RAG using OpenRouter Embeddings (Streamlit Cloud Safe)

import os
import json
import requests
import glob
import chromadb


# -------------------------
# Load API Key
# -------------------------
def load_openrouter_key():
    # First try Streamlit Secrets (Cloud)
    try:
        import streamlit as st
        if "OPENROUTER_API_KEY" in st.secrets:
            return st.secrets["OPENROUTER_API_KEY"].strip()
    except:
        pass

    # Fallback: environment variable
    return os.environ.get("OPENROUTER_API_KEY")


OPENROUTER_API_KEY = load_openrouter_key()


# -------------------------
# Setup Chroma (in-memory)
# -------------------------
client = chromadb.Client()
collection = client.create_collection("aryzen_finance")


# -------------------------
# OpenRouter Embeddings
# -------------------------
def embed_text(texts):
    """
    Uses OpenRouter embeddings API instead of HuggingFace.
    """
    url = "https://openrouter.ai/api/v1/embeddings"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/text-embedding-3-small",   # fast + cheap
        "input": texts
    }

    r = requests.post(url, headers=headers, json=payload, timeout=20)
    data = r.json()

    return [d["embedding"] for d in data["data"]]


# -------------------------
# Load knowledge base files
# -------------------------
def load_documents():
    docs, ids = [], []

    for pattern in ["*.txt", "*.md", "*.json"]:
        for file in glob.glob(f"knowledge_base/{pattern}"):
            try:
                content = open(file, "r", encoding="utf-8").read().strip()
                if len(content) > 5:
                    docs.append(content)
                    ids.append(file)
            except:
                pass

    return ids, docs


# -------------------------
# Ingest into Chroma
# -------------------------
def ingest_documents():
    ids, docs = load_documents()

    if not docs:
        print("No docs found.")
        return

    embeddings = embed_text(docs)

    collection.add(
        ids=ids,
        documents=docs,
        embeddings=embeddings
    )


# Run ingestion once on startup
ingest_documents()


# -------------------------
# RAG Retrieval
# -------------------------
def retrieve_context(query, k=3):
    query_emb = embed_text([query])[0]

    results = collection.query(
        query_embeddings=[query_emb],
        n_results=k
    )

    docs = results.get("documents", [[]])[0]
    return "\n\n".join(docs)


# -------------------------
# Format Response
# -------------------------
def format_response(text):
    if not text:
        return "No response."

    return text.strip()


# -------------------------
# Main Chatbot
# -------------------------
def chatbot(query: str) -> str:

    if not query.strip():
        return "Please ask something."

    if OPENROUTER_API_KEY is None:
        return "Missing API key."

    # RAG context
    context = retrieve_context(query)

    system_prompt = (
        "You are Aryzen Finance Assistant. "
        "Use the provided context if helpful. "
        "Do NOT give investment advice, predictions, loans, taxes, insurance guidance."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": f"Context:\n{context}"},
        {"role": "user", "content": query}
    ]

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "X-API-Key": OPENROUTER_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": messages
    }

    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=20
    )

    data = resp.json()

    try:
        output = data["choices"][0]["message"]["content"]
    except:
        return f"Unexpected response: {data}"

    return format_response(output)


# Quick test
if __name__ == "__main__":
    print(chatbot("What is NAV?"))
