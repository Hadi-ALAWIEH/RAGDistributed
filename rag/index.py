import argparse, json, numpy as np, pika
import faiss
from sentence_transformers import SentenceTransformer
from pymongo import MongoClient
import os


class VectorStore:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.mongo = MongoClient("mongodb://localhost:27017/")
        self.db = self.mongo["rag_scraper"]
        self.clean_col = self.db["clean_text"]
        self.meta_col = self.db["faiss_meta"]

        # Initialize or load FAISS index
        self.index = None
        self.id_map = []
        self.dim = None
        self.load_or_create_index()

    def load_or_create_index(self):
        """Load existing index or create new one"""
        meta = self.meta_col.find_one({"_id": "meta"})

        if meta and os.path.exists("rag/faiss.npy"):
            try:
                # Load existing vectors
                vectors = np.load("rag/faiss.npy")
                self.dim = vectors.shape[1]
                self.index = faiss.IndexFlatIP(self.dim)
                self.index.add(vectors.astype("float32"))
                self.id_map = meta.get("id_map", [])
                print(f"Loaded existing index with {len(self.id_map)} vectors")
            except Exception as e:
                print(f"Error loading existing index: {e}. Creating new index.")
                self.create_new_index()
        else:
            self.create_new_index()

    def create_new_index(self):
        """Create a new empty index"""
        self.dim = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dim)
        self.id_map = []
        print("Created new empty index")

    def add_document(self, doc_id: str, text: str):
        """Add a single document to the vector store"""
        if doc_id in self.id_map:
            print(f"Document {doc_id} already in index, skipping")
            return

        # Encode the text
        vector = self.model.encode([text], normalize_embeddings=True)

        # Add to FAISS index
        self.index.add(vector.astype("float32"))
        self.id_map.append(doc_id)

        # Save updated vectors and metadata
        self.save_index()

        print(f"Added document {doc_id} to vector store")

    def save_index(self):
        """Save the current index to disk and update metadata"""
        # Get all vectors from the index
        if self.index.ntotal > 0:
            vectors = self.index.reconstruct_n(0, self.index.ntotal)
            np.save("rag/faiss.npy", vectors.astype("float32"))

        # Update metadata
        self.meta_col.replace_one(
            {"_id": "meta"},
            {"_id": "meta", "dim": self.dim, "id_map": self.id_map},
            upsert=True,
        )

    def rebuild_index(self):
        """Rebuild index from all cleaned documents"""
        print("Rebuilding index from all cleaned documents...")
        docs = list(self.clean_col.find({}, {"_id": 0, "_id_str": 1, "text": 1}))
        texts = [d["text"] for d in docs if d.get("text")]
        ids = [d["_id_str"] for d in docs if d.get("text")]

        if not texts:
            print("No cleaned texts found for rebuilding.")
            return

        # Create new index
        self.dim = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dim)
        self.id_map = []

        # Encode in batches for better performance
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            batch_ids = ids[i : i + batch_size]

            vectors = self.model.encode(batch_texts, normalize_embeddings=True)
            self.index.add(vectors.astype("float32"))
            self.id_map.extend(batch_ids)
            print(
                f"Processed batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}"
            )

        self.save_index()
        print(f"Rebuilt FAISS index with {len(ids)} vectors.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue-url", default="amqp://guest:guest@localhost//")
    ap.add_argument("--queue-name", default="rag_vectors")
    ap.add_argument(
        "--rebuild", action="store_true", help="Rebuild index from all documents"
    )
    args = ap.parse_args()

    # Initialize vector store
    vector_store = VectorStore()

    if args.rebuild:
        vector_store.rebuild_index()
        return

    # RabbitMQ connection
    params = pika.URLParameters(args.queue_url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=args.queue_name, durable=True)

    def callback(chx, method, properties, body):
        try:
            task = json.loads(body.decode())
            doc_id = task["doc_id"]
            text = task["text"]

            print(f"[embedder] Processing document: {doc_id}")
            vector_store.add_document(doc_id, text)
            print(f"[embedder] Successfully embedded document: {doc_id}")

        except Exception as e:
            print(f"[embedder] Error processing message: {e}")

        chx.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=args.queue_name, on_message_callback=callback)
    print("[embedder] Waiting for embedding tasks. Ctrl+C to exit")
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        ch.stop_consuming()


if __name__ == "__main__":
    main()
