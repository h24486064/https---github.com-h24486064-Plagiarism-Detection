# report_generator.py

import json
import os
import html
from typing import List, Dict

import config

def generate_reports(original_text: str, analysis_results: List[Dict], doc_id: str):
    if not analysis_results:
        print("沒有發現可疑段落，不生成報告。")
        return

    print("正在生成報告...")
    os.makedirs(config.REPORT_OUTPUT_DIR, exist_ok=True)
    
    html_report_path = _generate_html_report(original_text, analysis_results, doc_id)
    print(f"HTML 報告已生成: {html_report_path}")

    json_report_path = _generate_json_report(analysis_results, doc_id)
    print(f"JSON 總結已生成: {json_report_path}")


def _generate_html_report(original_text: str, analysis_results: List[Dict], doc_id: str) -> str:
    highlighted_text = original_text
    
    if not analysis_results:
        return ""

    # 從後往前替換，避免字元索引錯亂
    sorted_results = sorted(analysis_results, key=lambda x: x['original_chunk']['metadata']['start_char'], reverse=True)
    
    for result in sorted_results:
        chunk_meta = result['original_chunk']['metadata']
        
        # =================================================================
        # 【修改處】因為 chunks 的位置現在直接相對於章節原文，不再需要計算偏移量
        start = chunk_meta['start_char']
        end = chunk_meta['end_char']
        # =================================================================
        
        if start < 0 or end > len(highlighted_text):
            print(f"偵測到無效的高亮位置 (start={start}, end={end})，已跳過此區塊。")
            continue

        verdict = result.get('llm_verdict', {})
        is_plagiarism = verdict.get('web_plagiarism', False)
        is_ai = verdict.get('ai_generated', False)
        
        color = "rgba(255, 255, 0, 0.4)"
        if is_plagiarism and is_ai:
             color = "rgba(255, 0, 255, 0.5)"
        elif is_plagiarism:
            color = "rgba(255, 77, 77, 0.5)"
        elif is_ai:
            color = "rgba(255, 165, 0, 0.5)"

        tooltip_text = f"判斷理由: {html.escape(verdict.get('justification', 'N/A'))}\n"
        tooltip_text += f"信賴度: {verdict.get('confidence', 0.0):.2f}"
        
        original_segment = highlighted_text[start:end]
        highlighted_segment = f'<span class="highlight" style="background-color:{color};" title="{tooltip_text}">{html.escape(original_segment)}</span>'
        highlighted_text = highlighted_text[:start] + highlighted_segment + highlighted_text[end:]

    table_rows = ""
    for res in sorted(analysis_results, key=lambda x: x['original_chunk']['metadata']['start_char']):
        verdict = res.get('llm_verdict', {})
        source_hit = res.get('source_hit') or {}
        
        chunk_meta = res['original_chunk']['metadata']
        # 同樣地，直接使用 chunk 的位置
        start = chunk_meta['start_char']
        end = chunk_meta['end_char']
        
        if start < 0 or end > len(original_text):
            continue
        display_text = original_text[start:end]

        source_text = source_hit.get('text', 'N/A (無網路來源)')
        source_url = source_hit.get('url', '#')
        similarity = source_hit.get('similarity', 0.0)
        
        judgement_html = f"""
        AI 生成: {'是' if verdict.get('ai_generated') else '否'}<br>
        網路抄襲: {'是' if verdict.get('web_plagiarism') else '否'}
        """

        table_rows += f"""
        <tr>
            <td>{html.escape(display_text[:300])}...</td>
            <td><a href="{source_url}" target="_blank">{html.escape(source_text[:200])}...</a></td>
            <td>{similarity:.3f}</td>
            <td>{judgement_html}</td>
            <td>{html.escape(verdict.get('justification', 'N/A'))}</td>
            <td>{verdict.get('confidence', 0.0):.2f}</td>
        </tr>
        """
    
    html_template = f"""
    <html>
    <head>
        <title>抄襲與 AI 生成檢測報告: {doc_id}</title>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; }}
            h1, h2 {{ color: #1a237e; border-bottom: 2px solid #3f51b5; padding-bottom: 5px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; font-size: 0.9em; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; vertical-align: top; }}
            th {{ background-color: #e8eaf6; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .content {{ white-space: pre-wrap; word-wrap: break-word; border: 1px solid #ccc; padding: 1.5em; background: #fafafa; border-radius: 5px; margin-top: 20px;}}
            .highlight {{ cursor: help; padding: 2px 0; border-radius: 3px; }}
            a {{ color: #3f51b5; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            .summary {{ background-color: #e3f2fd; border-left: 5px solid #2196f3; padding: 15px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <h1>抄襲與 AI 生成檢測報告</h1>
        <p><strong>文件名稱:</strong> {doc_id}</p>
        
        <div class="summary">
            <strong>報告總結:</strong> 本次分析針對指定章節，共發現 {len(analysis_results)} 個高風險段落。請檢視下方高亮原文與詳細分析表格。
        </div>

        <h2>高亮原文 (僅顯示被分析之章節)</h2>
        <div class="content">{highlighted_text}</div>
        
        <h2>詳細分析表格</h2>
        <table>
            <tr>
                <th>可疑段落原文 (預覽)</th>
                <th>最相似網路來源 (含連結)</th>
                <th>相似度分數</th>
                <th>AI/抄襲判斷</th>
                <th>判斷理由</th>
                <th>信賴度</th>
            </tr>
            {table_rows}
        </table>
    </body>
    </html>
    """
    
    report_path = os.path.join(config.REPORT_OUTPUT_DIR, f"{doc_id}_report.html")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    return report_path


def _generate_json_report(analysis_results: List[Dict], doc_id: str) -> str:
    """產生一份機器可讀的 JSON 格式報告。"""
    plagiarism_count = sum(1 for res in analysis_results if res.get('llm_verdict', {}).get('web_plagiarism'))
    ai_count = sum(1 for res in analysis_results if res.get('llm_verdict', {}).get('ai_generated'))

    output = {
        "doc_id": doc_id,
        "summary": {
            "total_suspicious_chunks": len(analysis_results),
            "plagiarism_chunks_count": plagiarism_count,
            "ai_chunks_count": ai_count
        },
        "details": []
    }

    for res in analysis_results:
        source_hit = res.get('source_hit') or {}
        output['details'].append({
            "original_chunk_metadata": res.get('original_chunk', {}).get('metadata'),
            "original_chunk_text": res.get('original_chunk', {}).get('text'),
            "llm_verdict": res.get('llm_verdict'),
            "source_details": {
                "url": source_hit.get('url'),
                "similarity_score": source_hit.get('similarity'),
                "source_text_preview": source_hit.get('text', '')[:200] + '...' if source_hit.get('text') else None
            }
        })

    report_path = os.path.join(config.REPORT_OUTPUT_DIR, f"{doc_id}_summary.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
        
    return report_path