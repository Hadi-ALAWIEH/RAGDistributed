# Distributed RAG-Based Web Scraper Framework — Report

## Team
- Student(s): <Name(s)>
- Course: Distributed Systems
- Date: <Date>

## Objective
Describe the goal and the high-level idea of the project.

## Architecture & Flowchart
![Flowchart Screenshot](flowchart.png)

> Paste full-screen screenshots of each phase below; include a short paragraph for each.

## Phase 1 — Environment Setup
- Tools installed (Python, Ray, RabbitMQ, MongoDB, FastAPI).
- Repo init screenshot.
- **Paragraph:** What you did and why.

## Phase 2 — Distributed Scraping
- Screenshot: workers consuming from queue, Scrapy logs.
- **Paragraph:** How urls are queued and consumed; fault tolerance choices.

## Phase 3 — Processing & Normalization
- Screenshot: cleaner run + Mongo collections.
- **Paragraph:** Cleaning rules, JSON schema, performance notes.

## Phase 4 — RAG Indexing & Retrieval
- Screenshot: index build, vector DB contents.
- **Paragraph:** Embedding model, vector DB choice, retrieval params.

## Phase 5 — API
- Screenshot: Swagger UI, sample requests/responses.
- **Paragraph:** Endpoints, auth/rate limiting decisions.

## Bonus — LB/Monitoring/Cloud
- Screenshot(s) of optional parts (Nginx/Grafana/K8s), if implemented.
- **Paragraph:** What you configured.

## Results & Discussion
- Two websites tested, examples of queries, latency.
- Limitations and future work.

## Deliverables checklist
- [ ] All source files
- [ ] Screenshots for each phase
- [ ] Flowchart
- [ ] README with run instructions

