# TECH:
- RabbitMQ (pika)	Queues URLs to scrape and distributes them to workers
- Ray	Runs multiple Scrapy processes in parallel
- Scrapy (via subprocess)	Actually crawls each URL
- MongoDB	Stores the scraped HTML/data
- sites.txt	Provides the initial seed URLs

# DOCKER
After running docker compose up -d, you will have
- RabbitMQ → available at:
    AMQP: amqp://guest:guest@localhost:5672//
- Web UI: http://localhost:15672
- MongoDB → available at mongodb://localhost:27017/

# FLOW

## Purpose
The purpose is to push those urls to a queue. The ray_worker (scraper) will be consuming those urls from the queue and processing them. 

inside spider.py we implement the scraping module which will be called inside spider.py run_spider function

## Steps
read sites.txt -> publish each URL to the queue named "urls" as a message (happens at `ch.basic_publish`) -> we define a consumer `ch.basic_consume` and give 2 params: the queue name it should read from and the function (callback) to execute when it read an item from the queue -> the callback that will be executed will run the spider by executed `run_spider` and sending it the url -> `run_spider` will run scrappy to scrape the website given its url -> the returned items will be saved inside monogo database name `rag_scraper` inside a collection called `raw_html`.

## Run the crawler

```
python scraper/ray_workers.py \
  --queue-url amqp://guest:guest@localhost:5672/%2F \
  --queue-name urls
```

NOTE: you can run this in multiple terminals to start multiple workers to process the queue in parallel

## Cleaner

The cleaner will read from the clean_tasks queue. The cleaner worker has to be executed and listening to this queue to clean text.
Crawler worker scrape the sites -> saves the data in mongodb -> pushes the result to the clean_tasks queue -> the cleaner worker will consume them and clean the result and save back to the mongodb clean_text collection.

run the cleaner to listen for tasks:

  `python ./processing/cleaner.py --queue-url amqp://guest:guest@localhost:5672/%2F --queue-name clean_tasks`

## Indexing (embeddings)
The cleaner push the cleaned result for each document to a new queue "rag_vectors". The rag vector worker inside rag/index.py will be subscribing to this queue and listening to messages to process them. One a new document arrives to this queue this worker will create an embedding(vector representation of the document's content). This will be using the pretrained model all-MiniLM-L6-v2 to create 384-dimensional vector embeddings. These embeddings will be saved locally inside FAISS Index File under rag/faiss.npy. It will also save some metadata inside mongodb rag_scraper.faiss_meta that maps FAISS index positions to document IDs

## API

Run the api:
`python api/main.py`

The api (fastapi server) has many endpoints. you can view them after you run the api under http://0.0.0.0:8000/docs


## Front end

Run the frontend:
```
cd frontend
npm install
npm run dev
```
