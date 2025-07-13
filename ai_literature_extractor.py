# ai_literature_extractor.py

from google.generativeai import GenerativeModel
import google.generativeai as genai
import os
import re # 匯入正規表達式模組

# 確保 genai 已被正確設定
# 請確保您的 .env 檔案中有 GOOGLE_API_KEY
if os.getenv("GOOGLE_API_KEY"):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
else:
    # 如果您是從 config.py 讀取，請確保 config 已被載入
    import config
    genai.configure(api_key=config.GOOGLE_API_KEY)


model = GenerativeModel("gemini-2.5-flash")  # 使用 Google Gemini 的生成模型

def extract_lit_review_via_ai(text: str) -> str:
    """
    【已修正】使用 AI 智慧擷取文獻回顧章節，並清理 AI 可能加入的額外回應。
    """
    # =================================================================
    # 【修改處 1】使用更嚴格、更直接的 Prompt
    # =================================================================
    prompt = (
        "你是一個高效率的文字處理工具。你的唯一任務是從以下提供的論文全文中，精準地擷取『第二章 文獻探討』或任何相關的文獻回顧內容。\n\n"
        "**輸出規則：**\n"
        "1.  **絕對不要**包含任何你自己的開場白、結語、註解或任何非論文原文的文字。\n"
        "2.  你的輸出**必須**直接以『第二章 文獻探討』或實際的章節內容開頭。\n"
        "3.  請完整輸出該章節的全部內容，直到下一個章節（例如第三章）開始之前為止。\n\n"
        f"論文全文如下：\n---\n{text[:30000]}\n---\n"  
    )
    
    print("    - [AI 擷取] 正在向 AI 發送請求以擷取目標章節...")
    try:
        response = model.generate_content(prompt)
        ai_output = response.text.strip()
        
        # =================================================================
        # 【修改處 2】增加後處理清洗步驟，作為雙重保險
        # 移除常見的 AI 開場白，例如 "好的，..."、"這是一篇..." 等
        # 這個正規表達式會尋找以中文、逗號、冒號或空格開頭，並以換行符結束的短句
        cleaned_output = re.sub(r'^[好的,好的，這是一篇論文中與文獻探討相關的段落與內容以下是擷取出的文獻回歸內容\n].*?\n', '', ai_output, flags=re.IGNORECASE)
        # =================================================================

        if cleaned_output:
            print("    - [AI 擷取] 已成功擷取並清理章節內容。")
            return cleaned_output
        else:
            # 如果清理後變空，代表 AI 可能只回了開場白，回傳原始輸出讓使用者判斷
            print("    - [警告] 清理後內容為空，可能 AI 未正確擷取。")
            return ai_output

    except Exception as e:
        print(f"    - [錯誤] AI 擷取章節時發生錯誤: {e}")
        return ""
    
import re
def extract_inline_citations(paragraph: str):
    pat = r"\(([A-Z][A-Za-z\- ]+?)(?: et al\.)?,\s*\d{4}\)"
    return re.findall(pat, paragraph)


def extract_paragraphs_with_citations(review_text: str):
    """
    參數：Step 1 回傳的 review_text
    回傳： [{'idx':0, 'paragraph':..., 'citations':[('Smith', '2022'), ...]}, ...]
    """
    para_list = []
    raw_paras = [p.strip() for p in review_text.split("\n\n") if p.strip()]
    for idx, p in enumerate(raw_paras):
        cits = citation_parser.extract_inline_citations(p)
        if cits:                       # 只保留有引用的段落
            para_list.append({
                "idx": idx,
                "paragraph": p,
                "citations": list(set(cits))
            })
    return para_list     