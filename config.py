# config.py

import os
# NEW: Import the dotenv library
from dotenv import load_dotenv

# NEW: Add this line at the top to load the .env file
# 它會尋找同目錄或上層目錄的 .env 檔案並載入
load_dotenv()

# --- Google Gemini API ---
# 這行程式碼維持不變，但現在它會從 .env 檔案中讀取金鑰
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Model Selection ---
EMBEDDING_MODEL = "text-embedding-004"
GENERATIVE_MODEL = "gemini-2.5-flash-latest"

# --- Google Search API ---
# 這兩行也維持不變
GOOGLE_API_KEY_SEARCH = os.getenv("GOOGLE_API_KEY_SEARCH")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# ... 以下所有其他設定都維持原樣 ...

# --- Processing Parameters ---
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
SEARCH_RESULTS_PER_QUERY = 3
SIMILARITY_THRESHOLD = 0.82

# --- Caching ---
CACHE_DIR = "cache"
QUERY_CACHE_DB = os.path.join(CACHE_DIR, "queries.sqlite")
CONTENT_CACHE_DIR = os.path.join(CACHE_DIR, "content")

# --- Reporting ---
REPORT_OUTPUT_DIR = "reports"