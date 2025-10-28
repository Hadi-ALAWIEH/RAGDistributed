import argparse, json, os, pika, ray, subprocess, tempfile, time
from pymongo import MongoClient


@ray.remote
def run_spider(url: str):
    # Run Scrapy spider for a single URL and capture output
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jl") as tmp:
        out = tmp.name
    cmd = [
        "scrapy",
        "runspider",
        "scraper/spider.py",
        "-a",
        f"start_url={url}",
        "-o",
        out,
        "-s",
        "LOG_LEVEL=ERROR",
    ]
    subprocess.run(cmd, check=True)
    # Read results
    items = []
    with open(out, "r", encoding="utf-8") as f:
        for line in f:
            items.append(json.loads(line))
    os.remove(out)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue-url", default="amqp://guest:guest@localhost//")
    ap.add_argument("--queue-name", default="urls")
    ap.add_argument("--sites-file", default="infra/sites.txt")
    ap.add_argument("--clean-queue-name", default="clean_tasks")
    args = ap.parse_args()

    # Seed queue with sites
    params = pika.URLParameters(args.queue_url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=args.queue_name, durable=True)
    ch.queue_declare(queue=args.clean_queue_name, durable=True)

    with open(args.sites_file, "r") as f:
        for line in f:
            url = line.strip()
            if url:
                ch.basic_publish(exchange="", routing_key=args.queue_name, body=url)

    # Mongo for storage
    mongo = MongoClient("mongodb://localhost:27017/")
    raw_col = mongo["rag_scraper"]["raw_html"]

    ray.init(ignore_reinit_error=True)

    def callback(chx, method, properties, body):
        url = body.decode()
        print(f"[worker] Received: {url}")
        fut = run_spider.remote(url)
        items = ray.get(fut)
        if items:
            result = raw_col.insert_many(items)
            print(f"[worker] Stored {len(items)} pages")
            # Trigger cleaner for each inserted document
            for doc_id in result.inserted_ids:
                chx.basic_publish(
                    exchange="", routing_key=args.clean_queue_name, body=str(doc_id)
                )
                print(f"[worker] Sent cleaning task for doc_id: {doc_id}")
        chx.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=args.queue_name, on_message_callback=callback)
    print("[worker] Waiting for messages. Ctrl+C to exit")
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        ch.stop_consuming()


if __name__ == "__main__":
    main()
