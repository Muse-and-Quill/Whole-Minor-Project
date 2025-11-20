# student/services/mongo_client.py
from pymongo import MongoClient
import os
from config import Config

_client = None
_db = None

def _get_config_value(*names, default=None):
    """
    Try to read the first non-empty attribute from Config and return it.
    """
    for name in names:
        val = getattr(Config, name, None)
        if val:
            return val
    return default

def get_mongo_db(debug_print=False):
    """
    Return a connected pymongo Database object.
    The function is safe with different environment variable / config names:
      - MONGO_URI or MONGODB_URI
      - MONGO_DBNAME or MONGODB_DB_NAME or MONGODB_DBNAME

    If debug_print is True it will print the final uri and dbname chosen.
    """
    global _client, _db
    if _db is not None:
        return _db

    # Try Config attributes first (safe with getattr)
    uri = _get_config_value("MONGO_URI", "MONGODB_URI", "MONGODB_URI", default=None)

    # Then environment variables (named variants)
    if not uri:
        uri = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or os.getenv("MONGODB_URI") or os.getenv("MONGO_URI")

    # DB name: support multiple naming conventions
    dbname = _get_config_value("MONGO_DBNAME", "MONGODB_DB_NAME", "MONGODB_DBNAME", default=None)
    if not dbname:
        dbname = os.getenv("MONGO_DBNAME") or os.getenv("MONGODB_DB_NAME") or os.getenv("MONGODB_DBNAME") or os.getenv("MONGO_DB")

    if not uri:
        raise RuntimeError("No MongoDB URI configured. Set MONGO_URI or MONGODB_URI in your .env or Config.")

    # Try to parse DB name out of URI if not provided separately
    if not dbname:
        try:
            # URI forms like: mongodb+srv://user:pass@host/<dbname>?options...
            # or mongodb://host:port/<dbname>
            # Basic heuristic: split after first '/' following the host portion
            if "://" in uri:
                after_scheme = uri.split("://", 1)[1]
                if "/" in after_scheme:
                    # take substring after the first '/' and before '?' if present
                    maybe = after_scheme.split("/", 1)[1]
                    maybe_db = maybe.split("?", 1)[0]
                    if maybe_db:
                        dbname = maybe_db
        except Exception:
            dbname = None

    if not dbname:
        dbname = "uap"  # fallback default

    if debug_print:
        print(f"[mongo_client] Using URI: {uri}")
        print(f"[mongo_client] Using DB: {dbname}")

    _client = MongoClient(uri)
    _db = _client[dbname]
    return _db
