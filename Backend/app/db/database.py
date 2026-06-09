from pymongo import MongoClient
import os
from dotenv import load_dotenv
from app.core.config import MONGO_URL, DATABASE_NAME, USERS_COLLECTION, REVOKED_TOKENS_COLLECTION

load_dotenv()

client = MongoClient(MONGO_URL)
db = client[DATABASE_NAME]

users_collection = db[USERS_COLLECTION]
revoked_tokens_collection = db[REVOKED_TOKENS_COLLECTION]