# Forward Deployment Project

An AI-powered product assistant built on top of [OWASP Juice Shop](https://owasp-juice.shop), featuring a RAG (Retrieval-Augmented Generation) pipeline backed by ChromaDB and OpenAI.

## Architecture

```
Browser → nginx:3000
            ├── /api/assistant/ask  →  assistant:8000  (RAG + OpenAI)
            └── /*                  →  juiceshop:3000  (official image)

assistant → chromadb:8000  (vector search)
ingest    → chromadb:8000  (one-time product data load)
```

## Features

- 🤖 AI Assistant widget injected into every page via nginx
- 🔍 RAG pipeline — retrieves relevant products from ChromaDB before answering
- 💬 Only answers product and pricing questions (refuses unrelated queries)
- 🐳 Fully containerised — runs with a single command

## Stack

| Component | Technology |
|---|---|
| Frontend widget | Vanilla JS injected via nginx `sub_filter` |
| AI Assistant API | Python FastAPI |
| LLM | OpenAI `gpt-4o-mini` |
| Vector DB | ChromaDB |
| Embeddings | ChromaDB built-in |
| Reverse Proxy | nginx |
| App | OWASP Juice Shop (official image) |

## Quick Start

### Prerequisites
- Docker + Docker Compose
- OpenAI API key with credits

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/Forward-Deployment-Project.git
cd Forward-Deployment-Project
```

### 2. Set up your API key
```bash
cp .env.openai.example .env.openai
# Edit .env.openai and add your OpenAI key
```

### 3. Run
```bash
docker compose up --build
```

### 4. Open
```
http://localhost:3000
```

Click the 🤖 button in the bottom-right corner to chat with the AI assistant.

## AI Assistant Files

```
ai_assistant/
├── main.py        # FastAPI app — GET /health, POST /ask
├── rag.py         # Retrieves relevant products from ChromaDB
├── ingest.py      # One-time: loads products from config/default.yml into ChromaDB
├── Dockerfile
└── requirements.txt
```

## RAG Pipeline

```
config/default.yml
      │
      ▼
  ingest.py ──── ChromaDB built-in embeddings ──── ChromaDB
                                                       │
                                                       ▼
User Question ──── ChromaDB similarity search ──── Top 5 products
                                                       │
                                                       ▼
                                              Inject into prompt
                                                       │
                                                       ▼
                                           OpenAI gpt-4o-mini
                                                       │
                                                       ▼
                                                   Answer
```

## Deploying on AWS EC2

See [EC2.docx](EC2.docx) for the full step-by-step guide to deploy on an Ubuntu EC2 instance.

**Quick summary:**
- Instance: `t3.medium`, Ubuntu 24.04, 25GB storage
- Open ports: `22` (SSH), `3000` (app)
- Install Docker, copy project, run `docker compose up --build -d`

## Environment Variables

| Variable | Description |
|---|---|
| `OPEN_AI_KEY` | OpenAI API key |
| `OPEN_API_KEY` | Fallback OpenAI API key |
| `CHROMA_HOST` | ChromaDB hostname (default: `chromadb`) |
| `CHROMA_PORT` | ChromaDB port (default: `8000`) |
| `AI_ASSISTANT_URL` | Assistant URL for proxy (default: `http://assistant:8000`) |
| `CONFIG_PATH` | Path to `default.yml` (default: `config/default.yml`) |

## License

MIT — see [LICENSE](LICENSE)
