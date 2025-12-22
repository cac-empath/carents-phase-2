import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_ENDPOINT = os.getenv("API_ENDPOINT")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

API_URL = f"{API_BASE_URL}{API_ENDPOINT}"

if not API_URL or not AUTH_TOKEN:
    raise ValueError("API_URL or AUTH_TOKEN not set in .env")
