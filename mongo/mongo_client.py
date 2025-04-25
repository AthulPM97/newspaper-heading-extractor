from pymongo import MongoClient
import os

MONGO_URI = os.getenv("MONGO_URI")

# Connect to cluster
client = MongoClient(MONGO_URI)
