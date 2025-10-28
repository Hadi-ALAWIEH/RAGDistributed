# Distributed RAG-Based Web Scraper Framework (Starter)

This is a minimal, end-to-end scaffold that satisfies the midterm requirements in a practical way and is designed to be finished within **two working sessions**.

## Quickstart (Local, no containers)
1. **Python env**
   ```bash
   py -m venv .venv || python3 -m venv .venv
   source .venv/bin/activate || .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start RabbitMQ and MongoDB**
   - Easiest via Docker (if you have it):
     ```bash
     docker compose -f infra/docker-compose.yml up -d
     ```
   - Or install locally and start services.

3. **(One-time) Build vector index**
   ```bash
   python rag/index.py --rebuild
   ```

4. **Run Ray worker(s) to consume URLs from the queue and scrape**
   - Terminal A (Ray head):
     ```bash
     ray start --head
     ```
   - Terminal B (workers):
     ```bash
     python scraper/ray_workers.py --queue-url amqp://guest:guest@localhost// --sites-file infra/sites.txt
     ```

5. **Process & clean scraped HTML into text**
   ```bash
   python processing/cleaner.py
   ```

6. **Serve API**
   ```bash
   uvicorn api.main:app --reload
   ```

7. **Test API**
   - Raw data: `GET http://127.0.0.1:8000/raw?limit=5`
   - Search enhanced content: `GET http://127.0.0.1:8000/search?q=quotes`
   - RAG query: `POST http://127.0.0.1:8000/rag` with JSON `{"q":"Who said life is short?"}`

## Two websites to test
- https://quotes.toscrape.com
- https://books.toscrape.com

You can change or add websites by editing `infra/sites.txt`.

## What this includes
- **Scrapy** spider for generic crawling and **BeautifulSoup** for parsing.
- **Ray** for distributed task execution.
- **RabbitMQ** as URL/message queue.
- **MongoDB** for raw + cleaned storage.
- **FAISS** for vector index + retrieval.
- **FastAPI** with endpoints for raw/processed/search/RAG.
- **Flowchart** (Mermaid) in `docs/flowchart.mmd` you can screenshot for the report.
- **Report template** in `docs/report_template.md`.

## Minimal workflow
1. Fill `infra/sites.txt` with at least two sites.
2. Start infra (RabbitMQ, MongoDB).
3. Run Ray workers to scrape (consumes URLs from queue, emits HTML to MongoDB).
4. Run cleaner to parse HTML → text JSON in MongoDB.
5. Build FAISS index over cleaned text.
6. Use the API to search and do RAG.

> Tip: If short on time, you can run **everything on one machine** (Ray still works locally). Docker/Kubernetes files are provided as **optional**.

