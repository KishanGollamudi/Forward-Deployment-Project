from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from rag import get_relevant_context
import os

load_dotenv(Path(__file__).parent.parent / ".env.openai")

api_key = os.getenv("OPEN_AI_KEY") or os.getenv("OPEN_API_KEY")
client = OpenAI(api_key=api_key)

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
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    try:
        context = get_relevant_context(request.message)
        augmented_prompt = f"{SYSTEM_PROMPT}\n\nRelevant product information:\n{context}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": augmented_prompt},
                {"role": "user", "content": request.message},
            ],
        )
        return AskResponse(reply=response.choices[0].message.content)
    except Exception as e:
        return JSONResponse(status_code=502, content={"detail": f"OpenAI call failed: {str(e)}"})
