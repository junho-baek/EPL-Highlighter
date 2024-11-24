from pymongo import MongoClient
from common.mongodb.config import MONGODB_URI


client = MongoClient(MONGODB_URI)
