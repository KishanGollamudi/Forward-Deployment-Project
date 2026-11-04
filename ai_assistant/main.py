from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from rag import get_relevant_context
import os

# Load .env (supports either .env or legacy .env.openai)
env_path = Path(__file__).parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent / ".env.openai"
load_dotenv(env_path)

# Dynamic LLM Configuration
LLM_BASE_URL = os.getenv("LLM_BASE_URL")  # e.g., "https://xyz.ngrok-free.app/v1" or None (defaults to OpenAI)
LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPEN_AI_KEY") or os.getenv("OPEN_API_KEY") or "dummy-token"
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Initialize OpenAI-compatible client
client = OpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY
)

app = FastAPI(title="Juice Shop AI Assistant")

SYSTEM_PROMPT = """You are a product assistant for OWASP Juice Shop.
You ONLY answer questions about products and pricing using the context provided.
If a question is unrelated to products or pricing, respond with:
"I can only help with product and pricing questions."
If the context does not contain enough information, say so honestly."""


class AskRequest(BaseModel):
    message: str


class AskResponse(BaseModel):
    reply: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm_base_url": LLM_BASE_URL or "default (api.openai.com)",
        "model": LLM_MODEL
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        context = get_relevant_context(request.message)
        augmented_prompt = f"{SYSTEM_PROMPT}\n\nRelevant product information:\n{context}"

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": augmented_prompt},
                {"role": "user", "content": request.message},
            ],
            temperature=0.2,
        )
        return AskResponse(reply=response.choices[0].message.content)
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": f"LLM inference call failed: {str(e)}"})
