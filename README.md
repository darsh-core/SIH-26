# SkillStat AI 🎯
**Smart India Hackathon 2026 (Problem ID 26101)**  
*MoSPI - Data Informatics & Innovation Division (DIID) - Smart Education*

SkillStat AI is an AI-enabled competency-learning platform designed to identify competency gaps, recommend personalized training via the iGOT Karmayogi ecosystem, and generate dynamic assessments from uploaded learning material.

---

## 🚀 Progress & Implementation Status

### Sprint 1: Core Competency & Assessment Engine (✅ Completed)
*   **Backend Source of Truth:** Migrated all mock dashboard data to be driven strictly by the backend database.
*   **Deterministic Competency Scoring:** Replaced arbitrary AI scoring with a deterministic algorithm based on question difficulty and correct answers.
*   **Gap Calculation Engine:** Real-time computation of skill gaps based on the user's current competency versus their target Role requirements.
*   **AI Assessment Hardening:** Verified end-to-end integration with local **Ollama (Llama 3.2 3B)** for AI-driven question generation based on assessment blueprints.

### Sprint 2: Document Intelligence & RAG Foundation (🚧 In Progress)
*   **Task 1: Document Ingestion Foundation (✅):** Built a production-oriented pipeline for uploading and extracting text from PDFs, DOCX, PPTX, and TXT files.
*   **Task 2: Semantic Chunking (✅):** Created a deterministic, source-preserving document chunker that maintains semantic boundaries and overlaps without blind character-splitting.
*   **Task 3: Real Embeddings & Vector Store (✅):** 
    *   Integrated **ChromaDB** for local, persistent vector storage.
    *   Integrated **Sentence-Transformers** (`all-MiniLM-L6-v2`) for generating 384-dimensional semantic embeddings.
    *   Implemented background processing (`BackgroundTasks`), idempotency (preventing duplicate chunks), and robust error recovery.
*   **Task 4: RAG & Generation (⏳ Pending)**

---

## 🛠️ Tech Stack
*   **Backend:** FastAPI (Python), SQLite (Relational), ChromaDB (Vector)
*   **AI / ML:** Ollama (Llama 3.2), Sentence-Transformers (Hugging Face)
*   **Frontend:** React, Vite, TailwindCSS

---

## 🏃‍♂️ Running the Project Locally

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

*Note: Ensure Ollama is running locally on port 11434 with the `llama3.2:3b` model downloaded.*
