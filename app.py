from flask import Flask, jsonify, render_template
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pymongo
import uuid
from datetime import datetime
import requests
import json
import time
from bson import ObjectId

app = Flask(__name__)

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["twitter_trends"]
collection = db["trends"]

# Path to cookies file
cookies_file = "cookies.json"

# Selenium setup
def fetch_trending_topics():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run Chrome in headless mode
    driver = webdriver.Chrome(options=options)

    try:
        # Navigate to Twitter page
        driver.get("https://twitter.com/explore/tabs/trending")
        time.sleep(5)

        # Load cookies
        with open(cookies_file, "r") as file:
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)

        # Refresh the page to apply cookies
        driver.refresh()
        time.sleep(5)

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract trending topics
        trending_spans = soup.find_all("span", class_="r-18u37iz")
        print(trending_spans,'trending spans')
        trending_topics = [span.get_text(strip=True) for span in trending_spans[:5]]

        # Fetch the current IP address
        response = requests.get("http://httpbin.org/ip")
        current_ip = response.json().get("origin") if response.status_code == 200 else "Unknown"

        # Prepare the record
        record = {
            "unique_id": str(uuid.uuid4()),
            "trend1": trending_topics[0] if len(trending_topics) > 0 else None,
            "trend2": trending_topics[1] if len(trending_topics) > 1 else None,
            "trend3": trending_topics[2] if len(trending_topics) > 2 else None,
            "trend4": trending_topics[3] if len(trending_topics) > 3 else None,
            "trend5": trending_topics[4] if len(trending_topics) > 4 else None,
            "date_time": datetime.now().isoformat(),
            "ip_address": current_ip,
        }

        # Insert into MongoDB
        collection.insert_one(record)

        driver.quit()
        return record

    except Exception as e:
        driver.quit()
        return {"error": str(e)}

@app.route("/")
def index():
    # Fetch all records from MongoDB
    all_records = list(collection.find())
    
    # Convert ObjectId to string for MongoDB data
    for record in all_records:
        if "_id" in record:
            record["_id"] = str(record["_id"])
    
    # Fetch fresh data from the script
    fresh_data = fetch_trending_topics()

    # Convert ObjectId to string for fresh data (if inserted into MongoDB)
    if "_id" in fresh_data and isinstance(fresh_data["_id"], ObjectId):
        fresh_data["_id"] = str(fresh_data["_id"])

    # Render the template with fresh data and all records from MongoDB
    return render_template("index.html", fresh_data=fresh_data, all_records=all_records)

@app.route("/run-script", methods=["GET"])
def run_script():
    result = fetch_trending_topics()
    
    # Convert ObjectId to string if it exists in the result
    if "_id" in result and isinstance(result["_id"], ObjectId):
        result["_id"] = str(result["_id"])

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
