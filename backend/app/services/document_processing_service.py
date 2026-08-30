import os
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
import pypdf
import docx
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentChunk, DocumentEmbedding
from app.ai import get_embedding_provider

class PDFTextExtractor:
    @staticmethod
    def extract(file_path: str) -> List[Dict[str, Any]]:
        pages_data = []
        try:
            reader = pypdf.PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                pages_data.append({
                    "page_number": i + 1,
                    "text": text or ""
                })
        except Exception as e:
            print(f"Error in PDFTextExtractor: {e}")
            raise e
        return pages_data


class DOCXTextExtractor:
    @staticmethod
    def extract(file_path: str) -> List[Dict[str, Any]]:
        pages_data = []
        try:
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            # DOCX does not have explicit pages; we group paragraphs (e.g. 8 per page) to simulate pages
            paragraphs_per_page = 8
            for idx, start in enumerate(range(0, len(paragraphs), paragraphs_per_page)):
                text = "\n".join(paragraphs[start:start + paragraphs_per_page])
                pages_data.append({
                    "page_number": idx + 1,
                    "text": text
                })
        except Exception as e:
            print(f"Error in DOCXTextExtractor: {e}")
            raise e
        return pages_data


class TXTTextExtractor:
    @staticmethod
    def extract(file_path: str) -> List[Dict[str, Any]]:
        pages_data = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Split plain text into virtual pages of roughly 1500 characters each
            char_per_page = 1500
            for idx, start in enumerate(range(0, len(content), char_per_page)):
                text = content[start:start + char_per_page]
                pages_data.append({
                    "page_number": idx + 1,
                    "text": text
                })
        except Exception as e:
            print(f"Error in TXTTextExtractor: {e}")
            raise e
        return pages_data


class DocumentProcessingService:
    @staticmethod
    def process_document(db: Session, document_id: uuid.UUID) -> None:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        doc.status = "PROCESSING"
        db.commit()

        try:
            # 1. Select text extractor based on file extension
            ext = os.path.splitext(doc.filename)[1].lower()
            if ext == ".pdf":
                pages = PDFTextExtractor.extract(doc.file_path)
            elif ext == ".docx":
                pages = DOCXTextExtractor.extract(doc.file_path)
            elif ext in [".txt", ".log"]:
                pages = TXTTextExtractor.extract(doc.file_path)
            else:
                raise ValueError(f"Unsupported file extension: {ext}")

            # 2. Chunk pages
            chunks = DocumentProcessingService.chunk_pages(pages)

            # 3. Embed and store chunks
            embedding_provider = get_embedding_provider()
            
            for idx, chunk in enumerate(chunks):
                text_content = chunk["text"]
                
                db_chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=idx,
                    text_content=text_content,
                    start_char=chunk["start_char"],
                    end_char=chunk["end_char"],
                    page_number=chunk["page_start"],
                    metadata_json={
                        "page_end": chunk["page_end"],
                        "token_count": chunk["token_count"]
                    }
                )
                db.add(db_chunk)
                db.flush()

                # Generate embedding (1536 dim vector list)
                vector = embedding_provider.embed_text(text_content)
                
                db_embed = DocumentEmbedding(
                    chunk_id=db_chunk.id,
                    model_name="mock-embedding-3-small",
                    embedding=vector
                )
                db.add(db_embed)

            doc.status = "INDEXED"
            doc.metadata_json = {
                **doc.metadata_json,
                "chunk_count": len(chunks),
                "processed_at": datetime.now().isoformat()
            }
            db.commit()

        except Exception as e:
            db.rollback()
            doc.status = "FAILED"
            doc.metadata_json = {
                **doc.metadata_json,
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }
            db.commit()
            print(f"Failed to process document {document_id}: {e}")
            raise e

    @staticmethod
    def chunk_pages(pages: List[Dict[str, Any]], target_word_count: int = 400, overlap_word_count: int = 80) -> List[Dict[str, Any]]:
        """Splits page text records into overlapping semantic chunks deterministically."""
        chunks = []
        words_buffer: List[Tuple[str, int, int]] = []  # tuple of (word, page_num, char_offset)
        
        char_offset = 0
        for page in pages:
            text = page["text"]
            page_num = page["page_number"]
            
            # Simple word extraction keeping track of character indices
            pos = 0
            for word in text.split():
                word_len = len(word)
                words_buffer.append((word, page_num, char_offset + pos))
                pos += word_len + 1  # word + whitespace
            char_offset += len(text) + 1

        if not words_buffer:
            return []

        # Slice the words buffer into chunks with overlap
        i = 0
        while i < len(words_buffer):
            chunk_slice = words_buffer[i : i + target_word_count]
            if not chunk_slice:
                break
                
            chunk_text = " ".join([w[0] for w in chunk_slice])
            page_start = chunk_slice[0][1]
            page_end = chunk_slice[-1][1]
            start_char = chunk_slice[0][2]
            end_char = chunk_slice[-1][2] + len(chunk_slice[-1][0])
            
            # Estimate token count (standard token heuristic: ~1.3 tokens per word)
            token_est = int(len(chunk_slice) * 1.3)
            
            chunks.append({
                "text": chunk_text,
                "page_start": page_start,
                "page_end": page_end,
                "start_char": start_char,
                "end_char": end_char,
                "token_count": token_est
            })
            
            # Move index forward by target minus overlap
            i += max(1, target_word_count - overlap_word_count)
            
        return chunks

    @staticmethod
    def search_similar_chunks(db: Session, query_embedding: List[float], top_k: int = 5) -> List[Tuple[DocumentChunk, float]]:
        """COSINE SIMILARITY query helper using pgvector's cosine_distance method."""
        # cosine similarity = 1 - cosine_distance
        distance_col = DocumentEmbedding.embedding.cosine_distance(query_embedding)
        
        results = db.query(DocumentChunk, (1.0 - distance_col).label("similarity"))\
            .join(DocumentEmbedding, DocumentChunk.id == DocumentEmbedding.chunk_id)\
            .order_by(distance_col.asc())\
            .limit(top_k)\
            .all()
            
        return [(row[0], float(row[1])) for row in results]
