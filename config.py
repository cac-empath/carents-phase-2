import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_ENDPOINT = os.getenv("API_ENDPOINT")
AUTH_URL = os.getenv("AUTH_URL")

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

API_URL = f"{API_BASE_URL}{API_ENDPOINT}"

if not API_URL:
    raise ValueError("API_URL not set in .env")

if not AUTH_URL or not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("Auth config not set in .env")
