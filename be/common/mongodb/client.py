from pymongo import MongoClient
from common.mongodb.config import MONGODB_URI


mongodb_client = MongoClient(MONGODB_URI)
mongodb_client.admin.command("ping")

db = mongodb_client.epl_highlighter
