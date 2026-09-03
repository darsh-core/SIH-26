import os
import json
import hashlib
import time
from typing import List, Dict, Any

class DocumentChunker:
    """
    Deterministic document chunking that preserves semantic boundaries and source metadata.
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        # Default config from environment or fallback
        self.chunk_size = chunk_size or int(os.environ.get("CHUNK_SIZE", 1000))
        self.chunk_overlap = chunk_overlap or int(os.environ.get("CHUNK_OVERLAP", 200))
        
    def estimate_tokens(self, text: str) -> int:
        """Simple deterministic token estimation (approx 4 chars per token)"""
        return len(text) // 4
        
    def _create_chunk_hash(self, text: str, document_id: int, metadata: dict) -> str:
        """Deterministic hash for a chunk"""
        h = hashlib.sha256()
        h.update(text.encode('utf-8'))
        h.update(str(document_id).encode('utf-8'))
        h.update(json.dumps(metadata, sort_keys=True).encode('utf-8'))
        return h.hexdigest()

    def chunk_document(self, document_id: int, normalized_document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes a normalized document and produces a list of chunks.
        """
        sections = normalized_document.get("sections", [])
        doc_metadata = normalized_document.get("metadata", {})
        
        if not sections:
            raise ValueError("Document has no sections to chunk")

        chunks = []
        chunk_index = 0
        
        # We iterate over sections (e.g. pages or slides).
        # To maintain source context and overlap, we accumulate paragraphs.
        
        current_chunk_text = ""
        current_chunk_metadata = {"original_filename": doc_metadata.get("original_filename")}
        current_chunk_sources = set() # To track pages/slides spanning this chunk
        
        def push_chunk(text, metadata, sources):
            nonlocal chunk_index
            text = text.strip()
            if not text or len(text.strip()) < 10: # Ignore tiny useless chunks
                return
                
            # Merge sources into metadata
            final_metadata = dict(metadata)
            if sources:
                # e.g., "pages": [1, 2]
                source_keys = {}
                for s in sources:
                    # s is a tuple of (key, value) pairs
                    for k, v in s:
                        if k not in source_keys:
                            source_keys[k] = set()
                        source_keys[k].add(v)
                
                for k, v in source_keys.items():
                    final_metadata[k] = sorted(list(v)) if len(v) > 1 else list(v)[0]

            chunks.append({
                "document_id": document_id,
                "chunk_index": chunk_index,
                "text": text,
                "estimated_token_count": self.estimate_tokens(text),
                "character_count": len(text),
                "source_metadata": final_metadata,
                "chunk_hash": self._create_chunk_hash(text, document_id, final_metadata),
                "created_at": int(time.time())
            })
            chunk_index += 1

        for section in sections:
            sec_metadata = section.get("metadata", {})
            sec_text = section.get("text", "")
            
            # Split section into paragraphs
            paragraphs = [p.strip() for p in sec_text.split("\n\n") if p.strip()]
            
            for para in paragraphs:
                para_len = len(para)
                
                # If paragraph alone is bigger than chunk size, we have to split it by sentences (or just hard split)
                if para_len > self.chunk_size:
                    # Flush current if it has content
                    if current_chunk_text:
                        push_chunk(current_chunk_text, current_chunk_metadata, current_chunk_sources)
                        current_chunk_text = ""
                        current_chunk_sources = set()
                        
                    # Split giant paragraph by sentences (rough approximation)
                    sentences = [s.strip() + "." for s in para.split(". ") if s.strip()]
                    temp_chunk = ""
                    for sent in sentences:
                        if len(temp_chunk) + len(sent) > self.chunk_size:
                            push_chunk(temp_chunk, current_chunk_metadata, {tuple(sec_metadata.items())})
                            temp_chunk = sent
                        else:
                            temp_chunk += " " + sent if temp_chunk else sent
                    if temp_chunk:
                        current_chunk_text = temp_chunk
                        current_chunk_sources.add(tuple(sec_metadata.items()))
                    continue

                # Normal paragraph appending
                projected_len = len(current_chunk_text) + para_len + 2 # +2 for \n\n
                
                if projected_len > self.chunk_size:
                    # Flush current chunk
                    push_chunk(current_chunk_text, current_chunk_metadata, current_chunk_sources)
                    
                    # Compute overlap (take last N chars/words from previous chunk)
                    # For simplicity, we just take the last part of current_chunk_text based on overlap size
                    overlap_text = ""
                    if self.chunk_overlap > 0 and len(current_chunk_text) > self.chunk_overlap:
                        overlap_text = current_chunk_text[-self.chunk_overlap:]
                        # Try to find a clean start (space or newline)
                        clean_idx = overlap_text.find(" ")
                        if clean_idx != -1:
                            overlap_text = overlap_text[clean_idx:].strip()
                            
                    current_chunk_text = overlap_text + "\n\n" + para if overlap_text else para
                    # Keep previous sources for overlap, plus new source
                    current_chunk_sources.add(tuple(sec_metadata.items()))
                else:
                    current_chunk_text += "\n\n" + para if current_chunk_text else para
                    current_chunk_sources.add(tuple(sec_metadata.items()))
                    
        # Flush final chunk
        if current_chunk_text:
            push_chunk(current_chunk_text, current_chunk_metadata, current_chunk_sources)
            
        if not chunks:
            raise ValueError("Document contains no extractable semantic content")
            
        return chunks
