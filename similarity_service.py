# similarity_service.py
import google.generativeai as genai # 替換 import
from typing import List, Dict, Tuple
from numpy import dot
from numpy.linalg import norm
import numpy as np

import config
from cache_manager import CacheManager

class SimilarityService:
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    def _cosine_similarity(self, a, b):
        return dot(a, b) / (norm(a) * norm(b))
    
    def get_embedding(self, text: str, url: str = "local") -> List[float]:
        """獲取文字的 embedding，優先從快取讀取。"""
        if url != "local":
            cached_data = self.cache.get_content_cache(url)
            if cached_data and 'embedding' in cached_data:
                return cached_data['embedding']

        # 注意：genai 的 embedding 介面與 openai 不同
        response = genai.embed_content(
            model=config.EMBEDDING_MODEL,
            content=text,
            task_type="RETRIEVAL_DOCUMENT" 
        )
        embedding = response['embedding']

        # 更新快取
        if url != "local":
            # 確保不會覆寫掉 text
            updated_data = self.cache.get_content_cache(url) or {}
            updated_data['embedding'] = embedding
            self.cache.set_content_cache(url, updated_data)
        
        return embedding

    def find_top_hits(self, target_chunk: str, candidate_pages: Dict[str, str]) -> List[Dict]:
        """
        在記憶體中進行語意比對，找出最相似的段落。
        candidate_pages: {url: cleaned_text}
        """
        if not candidate_pages:
            return []

        target_vec = self.get_embedding(target_chunk)
        
        top_hits = []
        for url, content in candidate_pages.items():
            if not content: continue
            
            # 直接比對整篇文章
            candidate_vec = self.get_embedding(content, url)
            
            score = self._cosine_similarity(target_vec, candidate_vec)
            
            if score >= config.SIMILARITY_THRESHOLD:
                top_hits.append({
                    "url": url,
                    "text": content,
                    "similarity": score
                })
        
        # 依相似度排序
        return sorted(top_hits, key=lambda x: x['similarity'], reverse=True)