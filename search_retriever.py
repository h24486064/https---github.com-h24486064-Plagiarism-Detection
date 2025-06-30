# search_retriever.py
import requests
from typing import List, Dict, Optional
from trafilatura import fetch_url, extract
import config
from cache_manager import CacheManager
import time

class SearchRetriever:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def search_google(self, query: str) -> List[Dict]:
        """使用 Google Programmable Search API 進行網頁搜尋。"""
        cached = self.cache.get_query_cache(f"google:{query}")
        if cached:
            return cached

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': config.GOOGLE_API_KEY_SEARCH,
            'cx': config.GOOGLE_CSE_ID,
            'q': query,
            'num': config.SEARCH_RESULTS_PER_QUERY
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            results = response.json().get('items', [])
            if not results:
                 return []
            extracted = [{"title": r.get('title', ''), "link": r.get('link', '')} for r in results]
            self.cache.set_query_cache(f"google:{query}", extracted)
            return extracted
        except requests.exceptions.RequestException as e:
            if '429' in str(e):
                print(f"    - [警告] Google Search API 速率過快 (429)，該次搜尋失敗。")
            else:
                print(f"    - [錯誤] Google Search API 發生錯誤: {e}")
            return []

    def run_searches(self, queries: List[str]) -> Dict[str, str]:
        """對一組查詢執行所有搜尋，並回傳去重的 URL 字典。"""
        all_urls = {}
        for q in queries:
            # =================================================================
            # 【修改處】將延遲增加到 2 秒，以確保穩定性
            time.sleep(2)
            # =================================================================
            
            print(f"    - 正在搜尋關鍵字: \"{q[:50]}...\"")
            google_results = self.search_google(q)
            for res in google_results:
                if res.get('link'): # 確保連結存在
                    all_urls[res['link']] = res.get('title', '無標題')
        return all_urls

    def download_and_clean(self, url: str) -> Optional[str]:
        """下載網頁內容並使用 trafilatura 清理，支援快取。"""
        cached_content = self.cache.get_content_cache(url)
        if cached_content and 'cleaned_text' in cached_content:
            return cached_content['cleaned_text']

        try:
            downloaded = fetch_url(url, timeout=15) # 增加超時設定
            if downloaded:
                cleaned_text = extract(downloaded, include_comments=False, include_tables=False)
                if cleaned_text:
                    self.cache.set_content_cache(url, {'cleaned_text': cleaned_text})
                    return cleaned_text
        except Exception as e:
            print(f"      - [錯誤] 下載或清理失敗: {url}, 原因: {e}")
            return None
            
        return None