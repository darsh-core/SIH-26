import os
import hashlib
import json
import uuid
import time
from fastapi import UploadFile
from sqlalchemy.orm import Session
from models import Document, DocumentState, DocumentChunk
from services.extractors import ExtractorFactory
from services.chunking import DocumentChunker

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
MAX_FILE_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE", 10 * 1024 * 1024)) # 10MB Default

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
    "text/plain": ".txt"
}

ALLOWED_EXTENSIONS = [".pdf", ".docx", ".pptx", ".txt"]

class DocumentService:
    @staticmethod
    def ensure_upload_dir():
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

    @staticmethod
    def calculate_hash(file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    async def process_upload(user_id: int, file: UploadFile, db: Session) -> Document:
        DocumentService.ensure_upload_dir()
        
        # Validation: Size (check while reading or after saving)
        # Validation: Extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
            
        # Optional MIME check (FastAPI file.content_type is client-provided, so it's a weak check, but good for quick rejection)
        if file.content_type and file.content_type not in ALLOWED_MIME_TYPES and file.content_type != "application/octet-stream":
            # Some clients send octet-stream for everything, so we only aggressively reject known bad types
            pass
            
        # Secure filename
        safe_filename = f"{uuid.uuid4()}{ext}"
        storage_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Save file to disk
        file_size = 0
        max_size = int(os.environ.get("MAX_UPLOAD_SIZE", 10 * 1024 * 1024))
        
        with open(storage_path, "wb") as f:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > max_size:
                    os.remove(storage_path)
                    raise ValueError(f"File exceeds maximum allowed size of {max_size / 1024 / 1024}MB")
                f.write(chunk)
                
        if file_size == 0:
            os.remove(storage_path)
            raise ValueError("File is empty")
            
        # Hash
        doc_hash = DocumentService.calculate_hash(storage_path)
        
        # Check duplicate
        existing = db.query(Document).filter(
            Document.user_id == user_id,
            Document.document_hash == doc_hash
        ).first()
        
        if existing:
            # Clean up the newly uploaded file and return the existing document
            os.remove(storage_path)
            return existing

        # Create record
        doc = Document(
            user_id=user_id,
            original_filename=file.filename,
            safe_filename=safe_filename,
            file_type=ext,
            file_size=file_size,
            upload_timestamp=int(time.time()),
            processing_status=DocumentState.UPLOADED.value,
            document_hash=doc_hash,
            created_at=int(time.time()),
            updated_at=int(time.time())
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        return doc

    @staticmethod
    def extract_document_background(doc_id: int, db: Session):
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return
            
        doc.processing_status = DocumentState.PROCESSING.value
        doc.updated_at = int(time.time())
        db.commit()
        
        storage_path = os.path.join(UPLOAD_DIR, doc.safe_filename)
        
        try:
            # 1. Extract and Normalize
            extractor = ExtractorFactory.get_extractor(doc.file_type)
            normalized_content = extractor.extract(storage_path, doc.original_filename)
            
            if not normalized_content["sections"]:
                raise ValueError("No text could be extracted from the document (empty content)")
                
            doc.extracted_text = json.dumps(normalized_content)
            
            # 2. Chunking
            chunker = DocumentChunker()
            chunk_dicts = chunker.chunk_document(doc.id, normalized_content)
            
            # 3. Reprocessing Strategy: delete old chunks before saving new ones
            db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete()
            
            # 4. Save new chunks
            for c_dict in chunk_dicts:
                chunk = DocumentChunk(
                    document_id=c_dict["document_id"],
                    chunk_index=c_dict["chunk_index"],
                    text=c_dict["text"],
                    estimated_token_count=c_dict["estimated_token_count"],
                    character_count=c_dict["character_count"],
                    source_metadata=json.dumps(c_dict["source_metadata"]),
                    chunk_hash=c_dict["chunk_hash"],
                    created_at=c_dict["created_at"]
                )
                db.add(chunk)
            
            doc.processing_status = DocumentState.READY_FOR_EMBEDDING.value
            doc.processing_error = None
            
        except Exception as e:
            doc.processing_status = DocumentState.FAILED.value
            doc.processing_error = str(e)
            
        finally:
            doc.updated_at = int(time.time())
            db.commit()

    @staticmethod
    def embed_document_background(doc_id: int, user_id: int, db: Session):
        from services.embedding_service import EmbeddingService
        
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc or doc.processing_status != DocumentState.EMBEDDING.value:
            return
            
        try:
            embedder = EmbeddingService()
            chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).all()
            
            if not chunks:
                raise ValueError("No chunks found to embed")
                
            embedder.embed_chunks(doc.id, chunks, user_id)
            
            doc.processing_status = DocumentState.EMBEDDED.value
            doc.processing_error = None
            
        except Exception as e:
            doc.processing_status = DocumentState.FAILED.value
            doc.processing_error = str(e)
            
        finally:
            doc.updated_at = int(time.time())
            db.commit()
