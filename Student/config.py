# student/config.py
import os
from dotenv import load_dotenv
load_dotenv()  # loads .env from project root

class Config:
    # Flask
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "LeSserafim")
    JWT_SECRET = os.getenv("JWT_SECRET", "SweetJuicePixy")

    # SQLAlchemy (if you need SQLite for local caches / small models)
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///uap.db")

    # Mail settings (names from your DICT env)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"

    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "info.unifiedacademics@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "ghys gubd xvkn oyfo")
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        os.getenv("MAIL_USERNAME", "info.unifiedacademics@gmail.com")
    )

    # MongoDB (use the same keys you had)
    # Some old files use MONGO_URI / MONGO_DBNAME; we support both names for flexibility
    MONGODB_URI = os.getenv(
        "MONGODB_URI",
        "mongodb+srv://infounifiedacademics_db_user:sachinpokemon@uap.vpd12hn.mongodb.net/?appName=UAP"
    )
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "uap_db")

    # OTP expiry (minutes)
    OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", 5))
