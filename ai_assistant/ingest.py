"""
Run once to load product data from config/default.yml into ChromaDB.
Usage: python ingest.py
"""
import re
import time
import yaml
import chromadb
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent / ".env.openai")

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))


def clean(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def build_documents(products: list) -> tuple[list[str], list[str], list[dict]]:
    docs, ids, metas = [], [], []
    for i, p in enumerate(products):
        name = p.get("name", "")
        desc = clean(p.get("description", ""))
        price = p.get("price", "N/A")
        deluxe = p.get("deluxePrice")
        limit = p.get("limitPerUser")

        text = f"Product: {name}\nDescription: {desc}\nPrice: ${price}"
        if deluxe:
            text += f"\nDeluxe Price: ${deluxe}"
        if limit:
            text += f"\nLimit per user: {limit}"

        docs.append(text)
        ids.append(f"product_{i}")
        metas.append({"name": name, "price": float(price) if price != "N/A" else 0.0})

    return docs, ids, metas


def wait_for_chroma(retries: int = 20, delay: int = 3) -> chromadb.HttpClient:
    for attempt in range(1, retries + 1):
        try:
            client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
            client.heartbeat()
            print(f"ChromaDB ready after {attempt} attempt(s).")
            return client
        except Exception as e:
            print(f"Waiting for ChromaDB ({attempt}/{retries}): {e}")
            time.sleep(delay)
    raise RuntimeError("ChromaDB did not become ready in time.")


def main():
    config_path = Path(os.getenv("CONFIG_PATH", str(Path(__file__).parent.parent / "config" / "default.yml")))
    with open(config_path) as f:
        config = yaml.safe_load(f)

    products = config.get("products", [])
    docs, ids, metas = build_documents(products)

    chroma = wait_for_chroma()
    # Use ChromaDB's default embedding function - no external model needed
    collection = chroma.get_or_create_collection("products")
    collection.upsert(documents=docs, ids=ids, metadatas=metas)
    print(f"Ingested {len(docs)} products into ChromaDB.")


if __name__ == "__main__":
    main()
