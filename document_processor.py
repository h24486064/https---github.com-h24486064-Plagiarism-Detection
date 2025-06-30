# document_processor.py
import re
import config
from typing import List, Dict, Tuple
import unicodedata
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tiktoken import get_encoding
import PyPDF2


class Chunk:
    def __init__(self, text: str, doc_id: str, chunk_id: int, start_char: int, end_char: int):
        self.text = text
        self.doc_id = doc_id
        self.chunk_id = chunk_id
        self.metadata = {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "start_char": start_char,
            "end_char": end_char
        }

def _pdf_to_text(file_path: str) -> str:
    """從 PDF 檔案中提取純文字，保留換行符。"""
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def _normalize_text(text: str) -> str:
    """執行大小寫、全半形、Unicode 正規化。"""
    text = unicodedata.normalize('NFKC', text)
    text = text.lower()
    return text

def _extract_literature_review_section(full_text: str) -> Tuple[str, int]:
    """
    【最終修正版】使用更精準的邊界定位，確保只擷取目標章節內容。
    """
    cleaned_text = _normalize_text(full_text)
    
    start_keywords = ["第二章 文獻探討", "第二章文獻探討", "文獻回顧"]
    end_keywords = ["第三章 研究方法", "第三章研究方法", "研究方法"]
    
    start_pos = -1
    last_match_start = None

    for keyword in start_keywords:
        keyword_regex = r'\s*'.join(list(keyword.replace(" ", "")))
        full_regex = r'(?:^|\n)\s*(?:\d{1,2}\.?\d?)*\s*' + keyword_regex
        matches = list(re.finditer(full_regex, cleaned_text))
        if matches:
            last_match_start = matches[-1]

    if last_match_start:
        # 起始位置是章節標題的結尾，這樣才不會包含標題本身
        start_pos = last_match_start.end()
        print(f"[INFO] 成功定位到內文中的起始章節，從位置 {start_pos} 開始擷取。")
    else:
        print("[錯誤] 在文件中找不到任何指定的起始章節（如『第二章 文獻探討』）。")
        return "", 0

    end_pos = -1
    text_after_start = cleaned_text[start_pos:] 
    
    for keyword in end_keywords:
        keyword_regex = r'\s*'.join(list(keyword.replace(" ", "")))
        full_regex = r'(?:^|\n)\s*(?:\d{1,2}\.?\d?)*\s*' + keyword_regex
        
        match = re.search(full_regex, text_after_start)
        if match:
            # =================================================================
            # 【修改處】結束位置是下一個章節標題的「開頭」，而不是結尾
            # 這樣可以確保不會包含到下一個章節的任何內容
            end_pos = start_pos + match.start()
            # =================================================================
            print(f"[INFO] 找到結束章節: '{keyword}'，在位置 {end_pos} 停止擷取。")
            break

    if end_pos != -1:
        extracted_text = full_text[start_pos:end_pos]
        print(f"[INFO] 已成功抽取章節，最終長度為 {len(extracted_text)} 字元。")
        return extracted_text, start_pos
    else:
        max_len = 30000 
        print(f"[INFO] 未找到明確結束章節，將從起始位置截取前 {max_len} 字元進行分析。")
        extracted_text = full_text[start_pos : start_pos + max_len]
        return extracted_text, start_pos

def process_document(file_path: str, doc_id: str) -> Tuple[List[Chunk], str]:
    if file_path.lower().endswith(".pdf"):
        raw_text = _pdf_to_text(file_path)
    elif file_path.lower().endswith(".txt"):
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    else:
        raise ValueError("Unsupported file format.")
    
    if not raw_text.strip():
        print(f"[警告] 文件 '{doc_id}' 內容為空或無法提取文字。")
        return [], ""

    section_text, text_offset = _extract_literature_review_section(raw_text)
    
    if not section_text:
        print("[錯誤] 因未能抽取到目標章節，已停止分析。")
        return [], ""

    tokenizer = get_encoding("cl100k_base")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4",
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

    split_texts = text_splitter.split_text(section_text)
    
    chunks = []
    current_pos_in_section = 0
    for i, text_chunk in enumerate(split_texts):
        normalized_chunk_text = _normalize_text(text_chunk)
        
        start_char_in_section = section_text.find(text_chunk, current_pos_in_section)
        
        if start_char_in_section == -1:
             start_char_in_section = section_text.find(text_chunk, max(0, current_pos_in_section - config.CHUNK_OVERLAP*2))

        start_char_in_full = start_char_in_section + text_offset
        end_char_in_full = start_char_in_full + len(text_chunk)
        
        current_pos_in_section = start_char_in_section + 1
        
        chunk = Chunk(
            text=normalized_chunk_text,
            doc_id=doc_id,
            chunk_id=i,
            start_char=start_char_in_full,
            end_char=end_char_in_full
        )
        chunks.append(chunk)
        
    print(f"目標章節已被切成 {len(chunks)} 個區塊進行分析。")
    return chunks, section_text