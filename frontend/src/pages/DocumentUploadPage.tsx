import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Upload, FileText, ArrowLeft, CheckCircle, AlertTriangle } from "lucide-react"

import { documentApi } from "../services/documentApi"
import { Button, Card, Progress, Alert } from "../components/ui/Primitives"

export const DocumentUploadPage = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [docId, setDocId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("IDLE"); // IDLE, UPLOADING, PROCESSING, INDEXED, FAILED
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  // Poll processing status if docId is set
  useEffect(() => {
    if (!docId) return;

    const interval = setInterval(async () => {
      try {
        const details = await documentApi.getDocument(docId);
        setStatus(details.status);
        
        if (details.status === "INDEXED" || details.status === "READY") {
          setProgress(100);
          clearInterval(interval);
        } else if (details.status === "FAILED") {
          setProgress(0);
          setError(details.metadata?.error || "Document processing failed. Please try again.");
          clearInterval(interval);
        } else if (details.status === "PROCESSING") {
          setProgress(65);
        } else if (details.status === "UPLOADED") {
          setProgress(35);
        }
      } catch (err: any) {
        clearInterval(interval);
        setError(err.message || "Failed to fetch document status");
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [docId]);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    const ext = selectedFile.name.split(".").pop()?.toLowerCase();
    if (!["pdf", "docx", "pptx", "txt"].includes(ext || "")) {
      setError("Unsupported file format. Please upload PDF, DOCX, PPTX, or TXT.");
      setFile(null);
      return;
    }
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError("File exceeds 10MB size limit.");
      setFile(null);
      return;
    }
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStatus("UPLOADING");
    setProgress(15);
    setError(null);

    try {
      const res = await documentApi.uploadDocument(file);
      setDocId(res.document_id);
      if (res.is_duplicate) {
        setStatus(res.status === "READY" || res.status === "INDEXED" ? "READY" : res.status);
        setProgress(100);
      } else {
        setStatus(res.status);
        setProgress(35);
      }
    } catch (err: any) {
      setError(err.message || "Upload failed. Verify server is running.");
      setStatus("FAILED");
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={() => navigate("/documents")}>
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <h1 className="text-xl font-bold text-slate-800">Upload Training Material</h1>
      </div>

      <Card className="p-8">
        {status === "IDLE" && (
          <div className="space-y-6">
            {/* Drag drop area */}
            <div 
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
                dragActive ? "border-gov-blue-500 bg-gov-blue-50/50" : "border-slate-300 hover:border-gov-blue-400"
              }`}
              onClick={() => document.getElementById("fileInput")?.click()}
            >
              <input 
                id="fileInput"
                type="file" 
                className="hidden" 
                accept=".pdf,.docx,.pptx,.txt"
                onChange={handleFileChange}
              />
              <Upload className="h-12 w-12 mx-auto text-slate-400 mb-4" />
              <p className="font-semibold text-slate-700">Drag & drop your training material here</p>
              <p className="text-xs text-slate-400 mt-1">Supports PDF, DOCX, PPTX, or TXT (Max 10MB)</p>
            </div>

            {file && (
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-gov-blue-500" />
                  <div className="text-sm">
                    <p className="font-semibold text-slate-800 truncate max-w-sm">{file.name}</p>
                    <p className="text-slate-400 text-xs">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  </div>
                </div>
                <Button variant="primary" onClick={handleUpload}>
                  Start Uploading
                </Button>
              </div>
            )}
          </div>
        )}

        {status !== "IDLE" && (
          <div className="space-y-6">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-semibold text-gov-blue-900">Processing Stage: {status}</span>
                <span className="text-sm font-semibold text-gov-blue-900">{progress}%</span>
              </div>
              <Progress value={progress} className="h-2.5" />
            </div>

            {/* Stages timeline indicator */}
            <div className="grid grid-cols-5 gap-2 text-center text-xs font-semibold mt-4">
              <div className={status === "UPLOADING" ? "text-gov-blue-600" : "text-slate-400"}>
                <p>Uploading</p>
                <div className={`h-1.5 rounded-full mt-1 ${status === "UPLOADING" ? "bg-gov-blue-500" : "bg-slate-200"}`}></div>
              </div>
              <div className={status === "UPLOADED" ? "text-gov-blue-600" : "text-slate-400"}>
                <p>Extracting</p>
                <div className={`h-1.5 rounded-full mt-1 ${status === "UPLOADED" ? "bg-gov-blue-500" : "bg-slate-200"}`}></div>
              </div>
              <div className={status === "PROCESSING" ? "text-gov-blue-600" : "text-slate-400"}>
                <p>Chunking</p>
                <div className={`h-1.5 rounded-full mt-1 ${status === "PROCESSING" ? "bg-gov-blue-500" : "bg-slate-200"}`}></div>
              </div>
              <div className={status === "PROCESSING" ? "text-gov-blue-600" : "text-slate-400"}>
                <p>Embedding</p>
                <div className={`h-1.5 rounded-full mt-1 ${status === "PROCESSING" ? "bg-gov-blue-500" : "bg-slate-200"}`}></div>
              </div>
              <div className={status === "INDEXED" ? "text-green-600" : "text-slate-400"}>
                <p>Indexed</p>
                <div className={`h-1.5 rounded-full mt-1 ${status === "INDEXED" ? "bg-green-500" : "bg-slate-200"}`}></div>
              </div>
            </div>

            {status === "INDEXED" && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center space-y-3">
                <CheckCircle className="h-10 w-10 text-green-500 mx-auto" />
                <p className="font-semibold text-green-800 text-sm">Document successfully indexed into pgvector!</p>
                <Button variant="secondary" onClick={() => navigate("/documents")}>
                  Return to Documents
                </Button>
              </div>
            )}
          </div>
        )}

        {error && (
          <Alert variant="destructive" title="Error Processing Document" className="mt-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
            <div className="mt-2 text-right">
              <Button variant="secondary" size="sm" onClick={() => { setStatus("IDLE"); setFile(null); setError(null); }}>
                Try Again
              </Button>
            </div>
          </Alert>
        )}
      </Card>
    </div>
  );
};
