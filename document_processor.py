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

# =================================================================
# 【修改處】這是一個全新的、更簡潔的 process_document 函式
# 它現在只接收已經被擷取好的純文字，並對其進行切塊
# =================================================================
def process_document(section_text: str, doc_id: str) -> List[Chunk]:
    """
    【已修改】將傳入的章節純文字，切分成帶有位置資訊的區塊。
    """
    if not section_text:
        print("傳入的章節內容為空，已停止分析。")
        return []

    tokenizer = get_encoding("cl100k_base")
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="gpt-4",
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

    split_texts = text_splitter.split_text(section_text)
    
    chunks = []
    current_pos = 0
    for i, text_chunk in enumerate(split_texts):
        normalized_chunk_text = _normalize_text(text_chunk)
        
        start_char = section_text.find(text_chunk, current_pos)
        end_char = start_char + len(text_chunk)
        current_pos = start_char + 1
        
        chunk = Chunk(
            text=normalized_chunk_text,
            doc_id=doc_id,
            chunk_id=i,
            # 注意：這裡的位置是相對於章節文字的，報告產生器需要知道這一點
            start_char=start_char,
            end_char=end_char
        )
        chunks.append(chunk)
        
    print(f"目標章節已被切成 {len(chunks)} 個區塊進行分析。")
    return chunks