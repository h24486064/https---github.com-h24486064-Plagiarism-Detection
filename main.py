# main.py
import os
import time

import config
# --- 修改處 1: 從 document_processor 匯入 _pdf_to_text 函式 ---
from document_processor import process_document, Chunk, _pdf_to_text
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
    
    # --- 修改處 2: 根據檔案類型，用正確的方式讀取原文 ---
    # 為了最後生成報告，需要預先讀取文件的純文字內容
    original_text_content = ""
    if target_doc_path.lower().endswith(".pdf"):
        # 如果是 PDF，使用 PyPDF2 的函式來提取文字
        original_text_content = _pdf_to_text(target_doc_path)
    elif target_doc_path.lower().endswith(".txt"):
        # 如果是 txt，才用原本的方式讀取
        with open(target_doc_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_text_content = f.read()
    else:
        print(f"錯誤：不支援的檔案格式 '{target_doc_path}'")
        return # 如果檔案格式不支援，直接結束程式

    # 模組 1: 文件前處理
    # 這裡的 process_document 內部也會做一次同樣的文字提取，
    # 雖然有效率可優化的空間，但目前能確保程式正確執行。
    chunks = process_document(target_doc_path, doc_id)
    
    final_results = []
    for i, chunk in enumerate(chunks):
        print(f"\n[INFO] 正在處理區塊 {i+1}/{len(chunks)}...")

        # --- 流程分支 1: AI 生成檢測 ---
        ai_score = analyzer.get_ai_detection_score(chunk.text)
        print(f"  - AI 生成分數: {ai_score:.2f}")

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
            if ai_score > 80: # 假設高於 80 為高風險
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
        # 注意：您的 report_generator.py 中主函式為 generate_reports
        # 您可以依照您 report_generator.py 的實際函式名稱呼叫
        report_generator.generate_reports(
            original_text=original_text_content, 
            analysis_results=final_results, 
            doc_id=doc_id
        )
        print(f"報告已生成於 'reports' 資料夾中。")
    else:
        print("\n--- 檢測完成，未發現任何高風險段落 ---")

    cache.close()
    print(f"--- 總耗時: {time.time() - start_time:.2f} 秒 ---")


if __name__ == '__main__':
    # --- 新增：自動建立所需資料夾 ---
    os.makedirs("submissions", exist_ok=True)
    os.makedirs("cache", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    # --- 請修改這裡 ---
    target_document = "submissions/1-s2.0-074959789190020T-main.pdf" 
    
    # 檢查文件是否存在
    if not os.path.exists(target_document):
        print(f"錯誤：找不到目標文件 '{target_document}'。")
        print("請確認您已經將檔案放入 'submissions' 資料夾，並且檔名正確。")
    else:
        run_online_check(target_document)