
from google.generativeai import GenerativeModel
import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = GenerativeModel("gemini-pro")

def extract_lit_review_via_ai(text: str) -> str:
    prompt = (
        "你是一位擅長處理中文論文的學者。以下是一篇論文的完整內容，"
        "請你幫我擷取『第二章：文獻探討』或是任何屬於文獻回顧的段落。\n\n"
        "請輸出乾淨、連貫的文獻探討內容，不要包含非相關章節。\n\n"
        f"全文如下：\n{text[:20000]}"  # Gemini 限制單次大約 20,000 字符
    )
    response = model.generate_content(prompt)
    return response.text.strip()
