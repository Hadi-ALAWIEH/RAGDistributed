from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

app = FastAPI(title="Distributed RAG Scraper API")

# --- Storage ---
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["rag_scraper"]
raw_col = db["raw_html"]
clean_col = db["clean_text"]

# --- Embeddings + FAISS ---
model = SentenceTransformer("all-MiniLM-L6-v2")
index = None
id_map = []

def _load_index():
    global index, id_map
    meta = db["faiss_meta"].find_one({})
    if not meta:
        return
    id_map = meta.get("id_map", [])
    dim = meta.get("dim")
    xb = np.load("rag/faiss.npy")
    index = faiss.IndexFlatIP(dim)
    index.add(xb)

_load_index()

class RagQuery(BaseModel):
    q: str
    k: int = 5

@app.get("/raw")
def get_raw(limit: int = 10):
    docs = list(raw_col.find({}, {"_id": 0}).limit(limit))
    return {"count": len(docs), "items": docs}

@app.get("/search")
def search(q: str = Query(..., min_length=2), k: int = 5):
    qv = model.encode([q], normalize_embeddings=True)
    if index is None or index.ntotal == 0:
        raise HTTPException(400, "Vector index is empty. Build it first with rag/index.py")
    D, I = index.search(qv, k)
    results = []
    for idx in I[0]:
        doc = clean_col.find_one({"_id_str": id_map[idx]}, {"_id":0})
        if doc:
            results.append(doc)
    return {"query": q, "k": k, "results": results}

@app.post("/rag")
def rag(query: RagQuery):
    # Simple RAG: retrieve top-k, then concatenate as context (LLM call omitted for offline demo)
    qv = model.encode([query.q], normalize_embeddings=True)
    if index is None or index.ntotal == 0:
        raise HTTPException(400, "Vector index is empty. Build it first with rag/index.py")
    D, I = index.search(qv, query.k)
    contexts = []
    for idx in I[0]:
        doc = clean_col.find_one({"_id_str": id_map[idx]}, {"_id":0})
        if doc and "text" in doc:
            contexts.append(doc["text"][:500])
    # Placeholder "generation"
    answer = f"Based on {len(contexts)} retrieved chunks, here's a synthesized answer.

" + "\n---\n".join(contexts)
    return {"answer": answer, "ctx_count": len(contexts)}
