from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import time

app = FastAPI(
    title="Distributed RAG Scraper API",
    description="API for searching and querying scraped and processed documents",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Storage ---
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["rag_scraper"]
raw_col = db["raw_html"]
clean_col = db["clean_text"]
meta_col = db["faiss_meta"]

# --- Embeddings + FAISS ---
model = SentenceTransformer("all-MiniLM-L6-v2")
index = None
id_map = []
dim = None


def _load_index():
    global index, id_map, dim
    try:
        meta = meta_col.find_one({"_id": "meta"})
        if not meta:
            print("No FAISS metadata found in database")
            return

        id_map = meta.get("id_map", [])
        dim = meta.get("dim")

        if not os.path.exists("rag/faiss.npy"):
            print("FAISS vector file not found at 'rag/faiss.npy'")
            return

        xb = np.load("rag/faiss.npy")
        if xb.shape[0] != len(id_map):
            print(
                f"Warning: Vector count ({xb.shape[0]}) doesn't match ID count ({len(id_map)})"
            )

        index = faiss.IndexFlatIP(dim)
        index.add(xb.astype("float32"))
        print(f"Loaded FAISS index with {len(id_map)} vectors")

    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        index = None
        id_map = []


# Load index on startup
_load_index()


class RagQuery(BaseModel):
    q: str
    k: int = 5


class HealthResponse(BaseModel):
    status: str
    vector_index_loaded: bool
    vector_count: int
    raw_documents: int
    clean_documents: int


class SearchResult(BaseModel):
    url: Optional[str] = None
    text: str
    score: Optional[float] = None


class RagResponse(BaseModel):
    answer: str
    ctx_count: int
    query: str
    processing_time: float


@app.get("/")
async def root():
    return {"message": "Distributed RAG Scraper API", "status": "running"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        vector_index_loaded=index is not None,
        vector_count=index.ntotal if index else 0,
        raw_documents=raw_col.count_documents({}),
        clean_documents=clean_col.count_documents({}),
    )


@app.get("/raw")
def get_raw(limit: int = Query(10, ge=1, le=100)):
    """Get raw HTML documents"""
    docs = list(raw_col.find({}, {"_id": 0, "html": 0}).limit(limit))
    return {"count": len(docs), "items": docs}


@app.get("/clean")
def get_clean(limit: int = Query(10, ge=1, le=100)):
    """Get cleaned text documents"""
    docs = list(clean_col.find({}, {"_id": 0}).limit(limit))
    return {"count": len(docs), "items": docs}


@app.get("/search")
def search(
    q: str = Query(..., min_length=2, description="Search query"),
    k: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """Semantic search using vector embeddings"""
    start_time = time.time()

    if index is None or index.ntotal == 0:
        raise HTTPException(
            400,
            "Vector index is empty. Build it first or check if embeddings are being processed.",
        )

    # Encode query
    qv = model.encode([q], normalize_embeddings=True).astype("float32")

    # Search
    D, I = index.search(qv, min(k, index.ntotal))

    results = []
    for i, idx in enumerate(I[0]):
        if idx < len(id_map):  # Safety check
            doc = clean_col.find_one({"_id_str": id_map[idx]}, {"_id": 0})
            if doc:
                doc["score"] = float(D[0][i])  # Add similarity score
                results.append(doc)

    processing_time = time.time() - start_time
    return {
        "query": q,
        "k": k,
        "results": results,
        "processing_time": processing_time,
        "total_matches": len(results),
    }


@app.post("/rag", response_model=RagResponse)
def rag(query: RagQuery):
    """Retrieve and generate response using RAG"""
    start_time = time.time()

    if index is None or index.ntotal == 0:
        raise HTTPException(
            400,
            "Vector index is empty. Build it first or check if embeddings are being processed.",
        )

    # Encode query
    qv = model.encode([query.q], normalize_embeddings=True).astype("float32")

    # Search for relevant contexts
    k = min(query.k, index.ntotal)
    D, I = index.search(qv, k)

    contexts = []
    for idx in I[0]:
        if idx < len(id_map):  # Safety check
            doc = clean_col.find_one({"_id_str": id_map[idx]}, {"_id": 0})
            if doc and "text" in doc:
                # Limit context length and add similarity info
                truncated_text = doc["text"][
                    :1000
                ]  # Increased limit for better context
                contexts.append(truncated_text)

    # Simple generation (replace with actual LLM in production)
    if contexts:
        answer = f"Based on {len(contexts)} relevant sources:\n\n" + "\n\n---\n\n".join(
            contexts
        )
    else:
        answer = "No relevant information found in the knowledge base."

    processing_time = time.time() - start_time

    return RagResponse(
        answer=answer,
        ctx_count=len(contexts),
        query=query.q,
        processing_time=processing_time,
    )


@app.post("/reload-index")
def reload_index():
    """Force reload the FAISS index (useful after adding new documents)"""
    try:
        _load_index()
        return {
            "status": "success",
            "vector_count": index.ntotal if index else 0,
            "message": (
                f"Index reloaded with {len(id_map)} vectors"
                if index
                else "Index not loaded"
            ),
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to reload index: {str(e)}")


# Error handlers
@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error - check if vector index is properly loaded"
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
