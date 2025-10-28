from bs4 import BeautifulSoup
from pymongo import MongoClient
from bson import ObjectId
import re

mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["rag_scraper"]
raw_col = db["raw_html"]
clean_col = db["clean_text"]

def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def main():
    for doc in raw_col.find():
        _id = doc["_id"]
        text = clean_html(doc.get("html", ""))
        clean_col.update_one(
            {"_id_str": str(_id)},
            {"$set": {"_id_str": str(_id), "url": doc.get("url"), "text": text}},
            upsert=True
        )
    print("Cleaning done.")

if __name__ == "__main__":
    main()
