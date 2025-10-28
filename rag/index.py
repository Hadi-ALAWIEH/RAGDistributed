import argparse, numpy as np, faiss
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient

def build():
    mongo = MongoClient("mongodb://localhost:27017/")
    clean_col = mongo["rag_scraper"]["clean_text"]
    docs = list(clean_col.find({}, {"_id":0, "_id_str":1, "text":1}))
    texts = [d["text"] for d in docs if d.get("text")]
    ids = [d["_id_str"] for d in docs if d.get("text")]
    if not texts:
        print("No cleaned texts found.")
        return
    model = SentenceTransformer("all-MiniLM-L6-v2")
    X = model.encode(texts, normalize_embeddings=True)
    dim = X.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(np.asarray(X, dtype="float32"))
    np.save("rag/faiss.npy", X.astype("float32"))
    # Persist meta in Mongo
    mongo["rag_scraper"]["faiss_meta"].replace_one(
        {"_id":"meta"}, {"_id":"meta", "dim": dim, "id_map": ids}, upsert=True
    )
    print(f"Built FAISS index with {len(ids)} vectors.")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()
    build()
