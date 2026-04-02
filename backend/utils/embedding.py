import requests

OLLAMA_URL = "http://localhost:11434/api/embeddings"
MODEL_NAME = "nomic-embed-text"


def embed_text(text: str) -> list[float]:
    payload = {
        "model": MODEL_NAME,
        "prompt": text
    }

    resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    return data["embedding"]
