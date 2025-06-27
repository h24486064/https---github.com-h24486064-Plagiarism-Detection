# main.py
import os
import time

import config
from document_processor import process_document, Chunk
from cache_manager import CacheManager
from search_retriever import SearchRetriever
from analysis_service import AnalysisService
from similarity_service import SimilarityService
import report_generator

def run_online_check(target_doc_path: str):
    doc_id = os.path.basename(target_doc_path)
    print(f"--- 開始線上檢測文件: {doc_id} ---")
    start_time = time.time()

    # 初始化所有服務
    cache = CacheManager()
    retriever = SearchRetriever(cache)
    analyzer = AnalysisService()
    similarity = SimilarityService(cache)
    
    # 讀取原文以供報告使用
    with open(target_doc_path, 'r', encoding='utf-8') as f:
        original_text_content = f.read()

    # 模組 1: 文件前處理
    chunks = process_document(target_doc_path, doc_id)
    
    final_results = []
    for i, chunk in enumerate(chunks):
        print(f"\n[INFO] 正在處理區塊 {i+1}/{len(chunks)}...")

        # --- 流程分支 1: AI 生成檢測 ---
        ai_score = analyzer.get_ai_detection_score(chunk.text)
        print(f"  - AI 生成分數 (模擬): {ai_score:.2f}")

        # --- 流程分支 2: 線上抄襲比對 ---
        # 1. 候選文件擷取層
        queries = analyzer.generate_search_queries(chunk.text)
        print(f"  - 生成的搜尋查詢: {queries}")
        urls_titles = retriever.run_searches(queries)
        
        candidate_pages = {}
        for url, title in urls_titles.items():
            print(f"    - 下載與清理來源: {title} ({url})")
            content = retriever.download_and_clean(url)
            if content:
                candidate_pages[url] = content

        # 2. 語意比對層
        top_hits = similarity.find_top_hits(chunk.text, candidate_pages)

        if not top_hits:
            print("  - 未發現高相似度網路來源。")
            # 即使沒抄襲，也可能純 AI 生成
            if ai_score > 0.8: # 假設高於 0.8 為高風險
                 final_results.append({
                    "original_chunk": chunk.__dict__,
                    "llm_verdict": {
                        "ai_generated": True, "web_plagiarism": False, "confidence": ai_score,
                        "justification": "未找到網路抄襲來源，但 AI 檢測分數極高。"
                    }
                 })
            continue

        # 3. LLM 裁決層
        # 只對最相似的來源進行精細判讀以節省成本
        best_hit = top_hits[0]
        print(f"  - 發現最高相似度來源 (sim={best_hit['similarity']:.3f})，送交 LLM 裁決...")
        
        verdict = analyzer.get_llm_adjudication(
            suspect_chunk=chunk.text,
            hit_chunk=best_hit['text'][:1000], # 截斷以符合 token 限制
            source_url=best_hit['url'],
            ai_score=ai_score
        )
        final_results.append({
            "original_chunk": chunk.__dict__,
            "source_hit": best_hit,
            "llm_verdict": verdict
        })

    # 模組 8: 報告輸出
    if final_results:
        print("\n--- 檢測完成，正在生成報告 ---")
        report_path = report_generator.generate_html_report(original_text_content, final_results, doc_id)
        print(f"報告已生成: {report_path}")
    else:
        print("\n--- 檢測完成，未發現任何高風險段落 ---")

    cache.close()
    print(f"--- 總耗時: {time.time() - start_time:.2f} 秒 ---")


if __name__ == '__main__':
    target_document = "submissions/my_new_paper_online.txt"
    os.makedirs('submissions', exist_ok=True)
    if not os.path.exists(target_document):
        with open(target_document, 'w', encoding='utf-8') as f:
            f.write("A key finding in recent transformer-based models is the emergence of in-context learning, where the model learns to perform tasks purely from examples given in the prompt, without any weight updates. This capability was notably demonstrated by Brown et al. in their 2020 paper on GPT-3.")
    
    run_online_check(target_document)