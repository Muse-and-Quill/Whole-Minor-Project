# Faculty/services/mongo_client.py
from pymongo import MongoClient
import os
from config import Config

_client = None
_db = None

def _get_config_value(*names, default=None):
    for name in names:
        val = getattr(Config, name, None)
        if val:
            return val
    return default

def get_mongo_db(debug_print=False):
    global _client, _db
    if _db is not None:
        return _db

    uri = _get_config_value("MONGO_URI", "MONGODB_URI", default=None)
    if not uri:
        uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI")

    dbname = _get_config_value("MONGO_DBNAME", "MONGODB_DB_NAME", "MONGODB_DBNAME", default=None)
    if not dbname:
        dbname = os.getenv("MONGO_DBNAME") or os.getenv("MONGODB_DB_NAME") or os.getenv("MONGODB_DBNAME")

    if not uri:
        raise RuntimeError("No MongoDB URI configured. Set MONGO_URI or MONGODB_URI in .env")

    # parse db from uri if not provided
    if not dbname:
        try:
            if "://" in uri:
                after = uri.split("://", 1)[1]
                if "/" in after:
                    maybe = after.split("/", 1)[1].split("?",1)[0]
                    if maybe:
                        dbname = maybe
        except Exception:
            dbname = None

    if not dbname:
        dbname = "uap"

    if debug_print:
        print(f"[faculty mongo_client] uri={uri}, dbname={dbname}")

    _client = MongoClient(uri)
    _db = _client[dbname]
    return _db
