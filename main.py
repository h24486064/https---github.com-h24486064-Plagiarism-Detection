# main.py
import os
import time

import config
# 【修改處】引入新的工具和舊的函式
from document_processor import process_document, Chunk, _pdf_to_text
from ai_literature_extractor import extract_lit_review_via_ai
# =================================================================

from cache_manager import CacheManager
from search_retriever import SearchRetriever
from analysis_service import AnalysisService
from similarity_service import SimilarityService
import report_generator

def run_online_check(target_doc_path: str):
    doc_id = os.path.basename(target_doc_path)
    print(f"--- 開始線上檢測文件: {doc_id} ---")
    start_time = time.time()

    # 初始化服務
    cache = CacheManager()
    retriever = SearchRetriever(cache)
    analyzer = AnalysisService()
    similarity = SimilarityService(cache)
    
    # 將整個 PDF 轉為純文字
    print("正在讀取並轉換 PDF 全文...")
    full_text = _pdf_to_text(target_doc_path)
    if not full_text:
        print("[錯誤] 無法從 PDF 中提取任何文字。")
        return

    #  呼叫 AI 擷取文獻回顧
    print("正在呼叫 AI 擷取『文獻回顧』章節...")
    section_text_for_report = extract_lit_review_via_ai(full_text)
    if not section_text_for_report:
        print("[錯誤] AI 未能成功擷取到文獻回顧章節。")
        return
    print("[INFO] AI 已成功擷取目標章節！")

    # 將 AI 擷取出的文字，給 document_processor 切塊
    chunks = process_document(section_text_for_report, doc_id)
    # =================================================================
    
    if not chunks:
        return

    final_results = []
    for i, chunk in enumerate(chunks):
        print(f"\n[INFO] 正在處理區塊 {i+1}/{len(chunks)}...")
        
        # 進行 AI 生成檢測...
        ai_score = analyzer.get_ai_detection_score(chunk.text)
        is_ai_generated = ai_score > 80 
        print(f"  - AI 生成分數: {ai_score:.0f}/100")

        # 進行線上來源比對...
        queries = analyzer.generate_search_queries(chunk.text)
        print(f"  - AI 生成的搜尋查詢: {queries}")
        urls_titles = retriever.run_searches(queries)
        
        candidate_pages = {}
        for url, title in list(urls_titles.items())[:5]:
            print(f"    - 下載與清理來源: {title} ({url})")
            content = retriever.download_and_clean(url)
            if content:
                candidate_pages[url] = content

        top_hits = similarity.find_top_hits(chunk.text, candidate_pages)

        # 判斷結果...
        best_hit = None
        is_plagiarized = False
        if top_hits:
            best_hit = top_hits[0]
            if best_hit['similarity'] >= config.SIMILARITY_THRESHOLD:
                is_plagiarized = True
                print(f"  - [抄襲判斷] 發現高相似度來源 (相似度: {best_hit['similarity']:.3f})")
            else:
                 print(f"  - [抄襲判斷] 找到相似來源，但相似度 ({best_hit['similarity']:.3f}) 未達閾值。")
        else:
            print("  - [抄襲判斷] 未發現高相似度網路來源。")

        # 綜合判斷...
        if is_ai_generated or is_plagiarized:
            justifications = []
            if is_plagiarized:
                justifications.append(f"與網路來源相似度高達 {best_hit['similarity']:.2f}。")
            if is_ai_generated:
                justifications.append(f"AI 生成檢測分數為 {ai_score:.0f}/100。")

            verdict = {
                "ai_generated": is_ai_generated,
                "web_plagiarism": is_plagiarized,
                "confidence": max(best_hit['similarity'] if is_plagiarized else 0, ai_score / 100.0),
                "justification": " ".join(justifications)
            }
            
            final_results.append({
                "original_chunk": chunk.__dict__,
                "source_hit": best_hit,
                "llm_verdict": verdict 
            })

    # 報告輸出
    if final_results:
        print("\n--- 檢測完成，正在生成報告 ---")
        report_generator.generate_reports(
            original_text=section_text_for_report, 
            analysis_results=final_results, 
            doc_id=doc_id
        )
        print(f"報告已生成於 'reports' 資料夾中。")
    else:
        print("\n--- 檢測完成，未發現任何高風險段落 ---")

    cache.close()
    print(f"--- 總耗時: {time.time() - start_time:.2f} 秒 ---")


if __name__ == '__main__':
    os.makedirs("submissions", exist_ok=True)
    os.makedirs("cache", exist_ok=True)
    os.makedirs("reports", exist_ok=True)

    target_document = "submissions/test.pdf" # 請將您的測試檔案放在 submissions 資料夾
    
    if not os.path.exists(target_document):
        print(f"錯誤：找不到目標文件 '{target_document}'。")
        print("請確認您已經將檔案放入 'submissions' 資料夾，並且檔名正確。")
    else:
        run_online_check(target_document)