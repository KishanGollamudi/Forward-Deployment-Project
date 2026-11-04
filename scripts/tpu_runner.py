# scripts/tpu_runner.py
# Run this inside the Colab/Kaggle TPU or GPU notebook cell

import os
import subprocess

# 1. Install required packages
print("Installing serving packages...")
subprocess.run(["pip", "install", "-q", "fastapi", "uvicorn", "pyngrok", "transformers", "accelerate", "torch"], check=True)

from pyngrok import ngrok
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# 2. Expose with ngrok
# Set your token here or set it via environment variable
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "YOUR_NGROK_TOKEN_HERE")
ngrok.set_auth_token(NGROK_AUTHTOKEN)

# 3. Load Model (e.g. Qwen2.5-Coder-7B or 1.5B/7B for quick tests)
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
print(f"Loading {MODEL_ID}...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"
)

# 4. Minimal OpenAI-compatible Chat API
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "device": str(model.device)}

@app.post("/v1/chat/completions")
async def chat_completions(req: Request):
    body = await req.json()
    messages = body.get("messages", [])
    
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer([prompt], return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=body.get("max_tokens", 512),
            temperature=body.get("temperature", 0.3)
        )
    
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, outputs)
    ]
    response_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return {
        "id": "chatcmpl-tpu",
        "object": "chat.completion",
        "model": body.get("model", "qwen2.5-7b"),
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": response_text},
            "finish_reason": "stop"
        }]
    }

# 5. Open tunnel and serve
tunnel = ngrok.connect(8000)
print("\n" + "="*50)
print(f"🚀 YOUR LIVE TPU ENDPOINT IS: {tunnel.public_url}/v1")
print("="*50 + "\n")

uvicorn.run(app, host="0.0.0.0", port=8000)
