# document_processor.py
import re
import config
from typing import List, Dict
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
            text += page.extract_text() + "\n"
    # 潛在坑洞：PDF 格式複雜，表格、圖片、雙欄位可能導致亂碼，可能需要更強的 OCR 或解析工具
    return text

def _normalize_text(text: str) -> str:
    """執行大小寫、全半形、Unicode 正規化。"""
    text = text.lower() # 轉小寫
    text = unicodedata.normalize('NFKC', text) # Unicode 正規化
    # 可在此加入更多自訂正規化規則
    return text

def process_document(file_path: str, doc_id: str) -> List[Chunk]:
    """
    完整的文件處理流程：讀取 -> 正規化 -> 切段。
    回傳帶有原始位置映射的區塊列表。
    """
    # 步驟 1: 轉純文字 (Ingestion)
    if file_path.endswith(".pdf"):
        raw_text = _pdf_to_text(file_path)
    elif file_path.endswith(".txt"):
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    else:
        raise ValueError("Unsupported file format.")

    # 步驟 2: 正規化
    # 注意：為了位置映射，我們先對原始文本操作，切分後再正規化每個 chunk
    
    # 步驟 3: 切段 (Chunking)
    # 使用 LangChain 的 splitter 更穩健，它能處理邊界與重疊
    # tiktoken 用於精確計算 token 數
    tokenizer = get_encoding("cl100k_base")
    
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4", # 用於 token 計算的模型
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

    # langchain splitter 回傳的是字串列表，我們需要自己包裝成 Chunk 物件並找到位置
    split_texts = text_splitter.split_text(raw_text)
    
    chunks = []
    current_pos = 0
    for i, text_chunk in enumerate(split_texts):
        normalized_chunk_text = _normalize_text(text_chunk)
        start_char = raw_text.find(text_chunk, current_pos)
        if start_char == -1:
            # 若因重疊找不到，退回一步尋找
            start_char = raw_text.find(text_chunk, max(0, current_pos - config.CHUNK_OVERLAP * 5))

        end_char = start_char + len(text_chunk)
        current_pos = start_char + 1 # 更新搜索起點
        
        chunk = Chunk(
            text=normalized_chunk_text,
            doc_id=doc_id,
            chunk_id=i,
            start_char=start_char,
            end_char=end_char
        )
        chunks.append(chunk)
        
    print(f"文件 '{doc_id}' 已被切成 {len(chunks)} 個區塊。")
    return chunks