import sqlite3
import json
import hashlib
import os
from typing import Dict, Any, Optional, List

import config

class CacheManager:
    def __init__(self):
        os.makedirs(config.CACHE_DIR, exist_ok=True)
        os.makedirs(config.CONTENT_CACHE_DIR, exist_ok=True)
        self.conn = sqlite3.connect(config.QUERY_CACHE_DB)
        self._create_tables()

    def _create_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS query_cache (
                    query_hash TEXT PRIMARY KEY,
                    results_json TEXT NOT NULL
                );
            """)

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()

    def get_query_cache(self, query: str) -> Optional[List[Dict]]:
        query_hash = self._get_hash(query)
        cursor = self.conn.cursor()
        cursor.execute("SELECT results_json FROM query_cache WHERE query_hash = ?", (query_hash,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None

    def set_query_cache(self, query: str, results: List[Dict]):
        query_hash = self._get_hash(query)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO query_cache (query_hash, results_json) VALUES (?, ?)",
                (query_hash, json.dumps(results))
            )

    def get_content_cache(self, url: str) -> Optional[Dict[str, Any]]:
        url_hash = self._get_hash(url)
        cache_path = os.path.join(config.CONTENT_CACHE_DIR, f"{url_hash}.json")
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def set_content_cache(self, url: str, data: Dict[str, Any]):
        url_hash = self._get_hash(url)
        cache_path = os.path.join(config.CONTENT_CACHE_DIR, f"{url_hash}.json")
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def close(self):
        self.conn.close()