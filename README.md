Aryzen AI Assistant
Your trusted AI for smart financial clarity — strictly scoped, safely guardrailed, and live on AWS.
🎯 Problem Statement
Financial services companies need AI assistants that are helpful but strictly controlled — a general-purpose LLM will happily give investment advice, discuss competitors, or go completely off-topic, creating legal and reputational risk.
Aryzen AI Assistant solves this by combining a RAG (Retrieval-Augmented Generation) pipeline with a tightly scoped knowledge base, so the assistant:

✅ Answers questions about Aryzen's products and services
✅ Explains basic financial terms (SIPs, mutual funds, etc.)
❌ Never gives personalized financial advice
❌ Never answers anything outside its defined scope

It's a production-deployed, guardrailed financial chatbot — not a demo.

🚀 Features
FeatureDescription💬 Scoped RAG ChatbotAnswers only from the Aryzen knowledge base — no hallucination outside scope🔒 Strict GuardrailsLLM prompt-engineered to refuse off-topic, advisory, or harmful queries🧠 Financial Term ExplainerExplains SIPs, mutual funds, ELSS, NAV, and other common terms clearly📜 Chat HistoryPersistent per-session conversation history with delete support🔐 User AuthLogin / Signup flow with session management☁️ Live DeploymentHosted on AWS EC2, accessible via browser

🛠️ Tech Stack
LayerTechnologyRoleUI / FrontendStreamlitChat interface, auth pages, session stateLLMDeepSeek V3 via OpenRouterChat model powering all financial Q&A responsesEmbeddingsOpenRouter EmbeddingsConverts knowledge base docs to vectorsVector StoreChromaDBLocal vector DB for RAG retrieval (knowledge_base/)RAG PipelineCustom (bot.py)Retrieves relevant context, injects into LLM promptDeploymentAWS EC2Live server — HTTP on port 8501LanguagePython 3.10+Core runtime

🧠 How RAG Works Here
User Query
    │
    ▼
Embed Query (OpenRouter Embeddings)
    │
    ▼
ChromaDB Similarity Search  ──►  Top-K Relevant Chunks from Knowledge Base
    │
    ▼
Inject Context into LLM Prompt  +  Guardrail System Prompt
    │
    ▼
OpenRouter → DeepSeek V3 Chat  ──►  Scoped, Safe Response
    │
    ▼
Streamlit Chat UI
The key insight: the LLM never answers from its general training data alone — it is forced to ground every response in the retrieved Aryzen knowledge base chunks, making it factually reliable and scope-controlled.

🏗️ Project Structure
aryzen-finance-assistant/
│
├── app.py               ← Streamlit UI: login, signup, chat interface, session state
├── bot.py               ← RAG pipeline: embedding, ChromaDB retrieval, LLM call
├── requirements.txt     ← Python dependencies
│
├── knowledge_base/      ← ChromaDB vector store (Aryzen docs + financial terms)
│   └── chroma.sqlite3   ← Vector index (gitignored in production)
│
└── assets/              ← Static assets (logos, images)
Guardrail Design
The assistant is prompt-engineered at the system level to enforce these rules:
✅  ALLOWED                          ❌  BLOCKED
─────────────────────────────────    ──────────────────────────────────
Aryzen product & service info        Personalized financial advice
Basic financial term definitions     Stock tips or market predictions
How SIPs / mutual funds work         Competitor comparisons
General investing concepts           Off-topic queries (weather, coding…)
If a user asks something outside scope, the assistant politely declines and redirects — it does not attempt to answer from general knowledge.

☁️ Deployment
The app is deployed on an AWS EC2 instance and served on port 8501 via Streamlit's built-in server.
AWS EC2 (Ubuntu)
└── Streamlit app running on :8501
    └── Accessible at http://<ec2-public-ip>:8501

📦 Dependencies
txtstreamlit
chromadb
openai          # OpenRouter-compatible client (used with DeepSeek V3: deepseek/deepseek-chat)
python-dotenv

🛣️ Roadmap

 Add HTTPS via Nginx reverse proxy + SSL certificate
 Expand knowledge base with more Aryzen product documents
 Add user feedback / thumbs up-down on responses
 Admin panel to update knowledge base without redeployment
 Switch to streaming responses for better UX


⚠️ Disclaimer

Aryzen AI Assistant is designed to provide general financial information only.
It does not provide personalized financial advice, investment recommendations,
or any guidance that should be acted upon without consulting a qualified financial advisor.


📄 License
This project is licensed under the MIT License.
