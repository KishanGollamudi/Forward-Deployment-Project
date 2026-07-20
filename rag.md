# RAG Architecture — Juice Shop AI Assistant

## What is RAG?

RAG stands for **Retrieval-Augmented Generation**. It is a technique that improves AI responses by first **retrieving relevant information** from a knowledge base before sending anything to the language model.

Without RAG, a language model only knows what it was trained on. With RAG, you give it fresh, specific, accurate data at query time — making it far more reliable for domain-specific questions like product catalogues and pricing.

---

## Why RAG for this project?

The Juice Shop has 50+ products with specific names, descriptions and prices. Without RAG:

- The LLM would hallucinate prices
- It would not know about products added after its training cutoff
- Sending all 50 products in every prompt would be expensive and slow

With RAG, only the **top 5 most relevant products** are retrieved and sent to the LLM per query — keeping costs low and answers accurate.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INGESTION PHASE                          │
│                     (runs once at startup)                      │
│                                                                 │
│   config/default.yml                                            │
│          │                                                      │
│          ▼                                                      │
│   ingest.py                                                     │
│   ├── Parse all products (name, description, price)             │
│   ├── Build plain-text document per product                     │
│   ├── Send documents to ChromaDB                                │
│   └── ChromaDB embeds + stores them internally                  │
│          │                                                      │
│          ▼                                                      │
│   ChromaDB Vector Store                                         │
│   [ doc_0: "Apple Juice..."  → [0.12, -0.34, 0.87, ...] ]      │
│   [ doc_1: "Orange Juice..." → [0.09, -0.41, 0.76, ...] ]      │
│   [ doc_2: "Banana Juice..." → [0.21, -0.28, 0.91, ...] ]      │
│   [ ...50+ products stored as vectors... ]                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        QUERY PHASE                              │
│                  (runs on every /ask request)                   │
│                                                                 │
│   User: "what is the cheapest juice?"                           │
│          │                                                      │
│          ▼                                                      │
│   rag.py                                                        │
│   ├── Send query text to ChromaDB                               │
│   ├── ChromaDB embeds the query internally                      │
│   ├── Cosine similarity search across all stored vectors        │
│   └── Returns top 5 most relevant product documents             │
│          │                                                      │
│          ▼                                                      │
│   main.py                                                       │
│   ├── Inject retrieved products into system prompt              │
│   ├── Send augmented prompt + user question to OpenAI           │
│   └── Return answer to user                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1 — Ingestion (`ingest.py`)

This runs **once** when the stack starts via the `ingest` Docker container.

### What it does

Reads every product from `config/default.yml` and converts each one into a plain-text document:

```
Product: Apple Juice (1000ml)
Description: The all-time classic.
Price: $1.99
Deluxe Price: $0.99
Limit per user: 5
```

### Code

```python
# ingest.py — build_documents()
text = f"Product: {name}\nDescription: {desc}\nPrice: ${price}"
if deluxe:
    text += f"\nDeluxe Price: ${deluxe}"
if limit:
    text += f"\nLimit per user: {limit}"
```

These documents are then upserted into ChromaDB:

```python
collection.upsert(documents=docs, ids=ids, metadatas=metas)
```

ChromaDB automatically embeds each document using its built-in embedding model (`all-MiniLM-L6-v2` via ONNX runtime) and stores the resulting vectors.

### What a vector looks like

Each document becomes a list of 384 floating-point numbers representing its **semantic meaning** in mathematical space:

```
"Apple Juice (1000ml) — $1.99"  →  [0.023, -0.187, 0.541, 0.002, ...]
"Orange Juice (1000ml) — $2.99" →  [0.019, -0.201, 0.498, 0.011, ...]
"Melon Bike — $2999"            →  [0.412,  0.334, 0.021, 0.198, ...]
```

Products with similar meaning end up with vectors that are mathematically close to each other.

---

## Phase 2 — Retrieval (`rag.py`)

This runs on **every `/ask` request**.

### What it does

Takes the user's question, sends it to ChromaDB as a text query, and gets back the top 5 most relevant product documents.

### Code

```python
# rag.py — get_relevant_context()
results = collection.query(query_texts=[query], n_results=5)
docs = results.get("documents", [[]])[0]
return "\n\n".join(docs)
```

ChromaDB internally:
1. Embeds the query text using the same model used during ingestion
2. Computes **cosine similarity** between the query vector and all stored product vectors
3. Returns the top 5 closest matches

### What is cosine similarity?

It measures the angle between two vectors. A smaller angle = more similar meaning.

```
Query: "cheapest juice"
                    ↓ embed
Query vector: [0.031, -0.190, 0.512, ...]

Compare against all stored vectors:
  Apple Juice    similarity: 0.91  ✅ top match
  Banana Juice   similarity: 0.89  ✅ top match
  Apple Pomace   similarity: 0.87  ✅ top match
  Melon Bike     similarity: 0.12  ❌ not relevant
  T-Shirt        similarity: 0.08  ❌ not relevant
```

The key insight is that **meaning is captured, not just keywords**. A query like *"something healthy to drink"* will retrieve Green Smoothie and Carrot Juice even if the word "healthy" does not appear in the product name.

---

## Phase 3 — Augmentation & Generation (`main.py`)

The retrieved product documents are injected into the system prompt before calling OpenAI:

```python
# main.py — ask()
context = get_relevant_context(request.message)
augmented_prompt = f"{SYSTEM_PROMPT}\n\nRelevant product information:\n{context}"

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": augmented_prompt},
        {"role": "user",   "content": request.message},
    ],
)
```

### What the LLM actually receives

```
SYSTEM:
  You are a product assistant for OWASP Juice Shop.
  You ONLY answer questions about products and pricing...

  Relevant product information:
  Product: Apple Pomace
  Description: Finest pressings of apples.
  Price: $0.89
  Limit per user: 5

  Product: Apple Juice (1000ml)
  Description: The all-time classic.
  Price: $1.99
  Deluxe Price: $0.99

  Product: Banana Juice (1000ml)
  Description: Monkeys love it the most.
  Price: $1.99

  ... (2 more products)

USER:
  what is the cheapest juice?
```

The LLM answers **only from the retrieved context**, not from its general training knowledge. This prevents hallucination of prices or products that don't exist.

---

## Data Flow Summary

```
User question
     │
     ▼
POST /ask  (FastAPI — main.py)
     │
     ▼
get_relevant_context(question)  (rag.py)
     │
     ├── ChromaDB embeds question internally
     ├── Cosine similarity search
     └── Returns top 5 product documents
     │
     ▼
Build augmented prompt
= SYSTEM_PROMPT + retrieved products + user question
     │
     ▼
OpenAI gpt-4o-mini
     │
     ▼
Answer returned to user
```

---

## Embedding Model

| Property | Value |
|---|---|
| Model | `all-MiniLM-L6-v2` |
| Runtime | ONNX (inside ChromaDB container) |
| Vector dimensions | 384 |
| Cost | Free — runs locally inside Docker |
| Used for | Both ingestion and query embedding |

ChromaDB's built-in embedding function means **no external API calls are needed for embeddings** — only the final OpenAI chat completion call costs money.

---

## Component Responsibilities

| File | Responsibility |
|---|---|
| `ingest.py` | Parse products → build documents → store in ChromaDB |
| `rag.py` | Embed query → similarity search → return context |
| `main.py` | Inject context into prompt → call OpenAI → return reply |

---

## Why ChromaDB?

| Feature | Benefit |
|---|---|
| Built-in embedding | No need for a separate embedding API |
| Persistent storage | Data survives container restarts via Docker volume |
| HTTP client | Works across Docker containers over the network |
| Lightweight | ~180MB image, minimal RAM usage |
| Simple API | `upsert()` to store, `query()` to search |

---

## RAG vs No RAG

| | Without RAG | With RAG |
|---|---|---|
| Data source | LLM training data (stale) | Live product catalogue |
| Price accuracy | Hallucinated | Exact from `default.yml` |
| Tokens per request | All 50+ products every time | Only top 5 relevant products |
| Cost | High | Low |
| Hallucination risk | High | Low |
