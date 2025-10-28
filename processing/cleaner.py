import argparse, pika, time
from bs4 import BeautifulSoup
from pymongo import MongoClient
from bson import ObjectId
import re


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue-url", default="amqp://guest:guest@localhost//")
    ap.add_argument("--queue-name", default="clean_tasks")
    ap.add_argument("--embed-queue-name", default="rag_vectors")
    args = ap.parse_args()

    # MongoDB connection
    mongo = MongoClient("mongodb://localhost:27017/")
    db = mongo["rag_scraper"]
    raw_col = db["raw_html"]
    clean_col = db["clean_text"]

    # RabbitMQ connection
    params = pika.URLParameters(args.queue_url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=args.queue_name, durable=True)
    ch.queue_declare(queue=args.embed_queue_name, durable=True)

    def callback(chx, method, properties, body):
        doc_id_str = body.decode()
        print(f"[cleaner] Received cleaning task for: {doc_id_str}")

        try:
            doc_id = ObjectId(doc_id_str)
            # Find the raw document
            doc = raw_col.find_one({"_id": doc_id})

            if doc:
                # Clean the HTML
                text = clean_html(doc.get("html", ""))

                # Store cleaned text
                clean_col.update_one(
                    {"_id_str": doc_id_str},
                    {
                        "$set": {
                            "_id_str": doc_id_str,
                            "url": doc.get("url"),
                            "text": text,
                            "cleaned_at": time.time(),
                        }
                    },
                    upsert=True,
                )
                print(f"[cleaner] Successfully cleaned document: {doc_id_str}")

                # Send to embedding queue
                embed_task = {"doc_id": doc_id_str, "text": text, "url": doc.get("url")}
                chx.basic_publish(
                    exchange="",
                    routing_key=args.embed_queue_name,
                    body=json.dumps(embed_task),
                )
                print(f"[cleaner] Sent to embedding queue: {doc_id_str}")

            else:
                print(f"[cleaner] Document not found: {doc_id_str}")

        except Exception as e:
            print(f"[cleaner] Error processing {doc_id_str}: {e}")

        chx.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=args.queue_name, on_message_callback=callback)
    print("[cleaner] Waiting for cleaning tasks. Ctrl+C to exit")
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        ch.stop_consuming()


if __name__ == "__main__":
    import json

    main()
