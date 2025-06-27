# config.py

import os
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# --- Google Gemini API ---
# GOOGLE_API_KEY 會從 .env 檔案中讀取
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Model Selection (全部使用 Google 的模型) ---
# 用於生成 Embedding 的模型
EMBEDDING_MODEL = "text-embedding-004" 
# 用於生成搜尋查詢、以及進行最終裁決的語言模型
GENERATIVE_MODEL = "gemini-1.5-flash-latest"

# --- Google Search API ---
# 維持不變
GOOGLE_API_KEY_SEARCH = os.getenv("GOOGLE_API_KEY_SEARCH")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

# ... 以下所有其他設定都維持原樣 ...

# --- Processing Parameters ---
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
SEARCH_RESULTS_PER_QUERY = 10
SIMILARITY_THRESHOLD = 0.80

# --- Caching ---
CACHE_DIR = "cache"
QUERY_CACHE_DB = os.path.join(CACHE_DIR, "queries.sqlite")
CONTENT_CACHE_DIR = os.path.join(CACHE_DIR, "content")

# --- Reporting ---
REPORT_OUTPUT_DIR = "reports"