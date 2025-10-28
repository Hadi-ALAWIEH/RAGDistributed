  Application Overview


  This project is a Distributed Retrieval-Augmented Generation (RAG) Web Scraper Framework. Its purpose is to
  automatically scrape websites, clean the extracted content, and then use that content to power a smart search and
  question-answering system.

  It's designed as a pipeline that transforms unstructured web data into a structured, searchable knowledge base.

  ---

  Explanation of Each Part


  1. Scraping (`scraper/`)
   - `spider.py`: This is a generic web crawler built with the Scrapy library. When given a starting URL, it downloads the
     page's HTML. To gather more data, it also follows up to 10 links it finds on that page, scraping those as well.
   - `ray_workers.py`: This is the orchestrator for the scraping process. It uses Ray, a framework for distributed
     computing, to run multiple scraping tasks in parallel.
       - It reads the initial list of websites from infra/sites.txt.
       - It puts these website URLs into a RabbitMQ message queue. A queue is used to reliably manage the list of URLs that
         need to be scraped.
       - It then launches "workers" using Ray. Each worker pulls a URL from the queue, runs the Scrapy spider on it, and
         saves the raw HTML content into a MongoDB database.


  2. Processing (`processing/`)
   - `cleaner.py`: Raw HTML contains a lot of junk (like scripts, styles, and ads) that isn't useful for analysis. This
     script reads the raw HTML from MongoDB and uses the BeautifulSoup library to clean it. It strips out all the
     unnecessary tags and leaves only the core text content, which it then saves back to a different collection in MongoDB.


  3. RAG - Retrieval-Augmented Generation (`rag/`)
   - `index.py`: This is the core of the "smart" part of the application.
       - It takes the cleaned text from MongoDB.
       - It uses a machine learning model (SentenceTransformer) to convert the text into numerical representations called
         "vector embeddings." These embeddings capture the semantic meaning of the text.
       - It stores these embeddings in a FAISS index. FAISS is a library developed by Facebook AI for efficient similarity
         search. This index allows the application to quickly find text passages that are semantically similar to a user's
         query, even if they don't use the exact same words.


  4. API (`api/`)
   - `main.py`: This script creates a web API using FastAPI that serves as the main interface for the user. It has three main
     endpoints:
       - GET /raw: Allows you to view the raw, unprocessed HTML that was scraped.
       - GET /search: Allows you to perform a semantic search. You provide a query, and it uses the FAISS index to find the
         most relevant chunks of text from the scraped websites.
       - POST /rag: This endpoint takes a question from the user. It first uses the search functionality (the "Retrieval"
         part) to find relevant context from the scraped data. Then, it synthesizes that context into an answer (the
         "Generation" part). In this starter project, the final "generation" by a large language model (LLM) is placeholder,
         but it demonstrates the complete RAG flow.


  5. Infrastructure (`infra/`)
   - `docker-compose.yml`: This file makes setup easy. It defines the two external services the application depends on:
     RabbitMQ (the message queue) and MongoDB (the database). With Docker, you can start both with a single command.
   - `sites.txt`: A simple text file where you list the starting URLs for the websites you want to scrape.

  ---

  The Flow: From Scraping to Answering

  Here is the step-by-step flow of data through the system, as also described in docs/flowchart.mmd:


   1. Seeding: The process starts with a list of URLs in infra/sites.txt.
   2. Queuing: The ray_workers.py script reads these URLs and pushes them into a RabbitMQ queue. This ensures that each URL
      will be processed, even if a worker fails.
   3. Distributed Scraping: Ray workers pick up URLs from the queue. Each worker runs the Scrapy spider to crawl the site.
      The raw HTML is stored in a MongoDB collection named raw_html.
   4. Cleaning: The cleaner.py script runs, fetching the raw HTML from MongoDB, cleaning it, and storing the clean text in
      the clean_text collection.
   5. Indexing: The rag/index.py script is executed. It converts all the cleaned text into vector embeddings and builds the
      FAISS search index.
   6. Serving: The FastAPI server is started. It loads the FAISS index into memory, ready to respond to user queries.

  User Flow

  This is how a person would typically use the application:


   1. Configuration: The user decides which websites to scrape and lists them in infra/sites.txt.
   2. Execution: The user follows the README.md instructions to run the entire pipeline:
       - Start the backend services (RabbitMQ and MongoDB) using Docker.
       - Run the ray_workers.py script to start scraping.
       - Once scraping is done, run the cleaner.py script.
       - After cleaning, run rag/index.py to build the search index.
       - Finally, start the API with uvicorn.
   3. Interaction: With the API running, the user can now ask it questions. For example, they could send a request to the /rag
      endpoint like:

   1     {
   2       "q": "Who said life is short?"
   3     }

   4. Response: The API would then search its knowledge base (built from the scraped websites) for relevant information about
      that quote and return a synthesized answer based on what it found.
