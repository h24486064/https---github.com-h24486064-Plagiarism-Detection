import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()
# 從 .env 檔案中讀取所有環境變數

# --- Google Gemini API ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


EMBEDDING_MODEL = "text-embedding-004" 
GENERATIVE_MODEL = "gemini-2.5-flash"

# --- Google Search API ---
GOOGLE_API_KEY_SEARCH = os.getenv("GOOGLE_API_KEY_SEARCH")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")


CHUNK_SIZE = 1500
CHUNK_OVERLAP = 100
SEARCH_RESULTS_PER_QUERY = 10
SIMILARITY_THRESHOLD = 80

CACHE_DIR = "cache"
QUERY_CACHE_DB = os.path.join(CACHE_DIR, "queries.sqlite")
CONTENT_CACHE_DIR = os.path.join(CACHE_DIR, "content")

REPORT_OUTPUT_DIR = "reports"