import json
import os

import faiss
import numpy as np
from django.conf import settings
from django.core.cache import cache
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)


FALLBACK_MODELS = [
    "meta-llama/Llama-3.3-70B-Instruct:cheapest",
    "Qwen/Qwen2.5-72B-Instruct:cheapest",
    "Qwen/Qwen2.5-7B-Instruct:cheapest",
]
MODEL_ID = FALLBACK_MODELS[0]

TTL = getattr(settings, "EMBEDDING_CACHE_TTL", 86400)


def get_embedding(note_id: int, text: str) -> list:
    """Get embedding from Redis cache, compute if not cached."""
    cache_key = f"embedding:note:{note_id}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)
    embedding = embedding_model.encode([text])[0].tolist()
    cache.set(cache_key, json.dumps(embedding), timeout=TTL)
    return embedding


def invalidate_embedding(note_id: int):
    """Call when note is edited or deleted."""
    cache.delete(f"embedding:note:{note_id}")


def encode_text(text: str) -> list:
    """Encode query text — no caching needed for queries."""
    return embedding_model.encode([text])[0].tolist()


def build_index(notes):
    """Build in-memory FAISS index from notes, using Redis cached embeddings."""
    if not notes:
        return None, []

    embeddings, texts = [], []
    for note in notes:
        text = f"{note.title} {note.content}"
        embedding = get_embedding(note.id, text)
        embeddings.append(embedding)
        texts.append(text)

    embeddings_np = np.array(embeddings, dtype=np.float32)
    index = faiss.IndexFlatL2(embeddings_np.shape[1])
    index.add(embeddings_np)
    return index, texts


def retrieve(query: str, user, k: int = 3) -> list:
    """Find top-k relevant notes for this user."""
    from .models import Note

    notes = Note.objects.filter(user=user)
    if not notes.exists():
        return []

    index, texts = build_index(notes)
    if index is None:
        return []

    query_vec = np.array([encode_text(query)], dtype=np.float32)
    distances, indices = index.search(query_vec, k)
    return [texts[i] for i in indices[0] if i < len(texts)]


def generate(context: str, query: str, history: list) -> str:
    """Call HuggingFace LLM with context and chat history."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant. "
                "Answer questions using ONLY the notes provided. "
                "If the answer is not found, say 'I could not find that in your notes.'"
            ),
        }
    ]

    for msg in history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append(
        {"role": "user", "content": f"Notes:\n{context}\n\nQuestion: {query}"}
    )

    # Try each model in fallback list
    for model in FALLBACK_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,
                temperature=0.5,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            error = str(e)
            if "410" in error or "deprecated" in error.lower() or "404" in error:
                continue  # try next model
            elif "402" in error:
                return "Out of free credits. Visit huggingface.co/settings/billing."
            elif "403" in error:
                return "Token missing 'Make calls to Inference Providers' permission."
            else:
                return f"Error: {error}"

    return "All models failed or are deprecated. Please check huggingface.co for available models."


def ask(query: str, user, history: list) -> str:
    docs = retrieve(query, user)
    if not docs:
        return "No relevant notes found. Please add some notes first."
    context = "\n".join(f"- {d}" for d in docs)
    return generate(context, query, history)
