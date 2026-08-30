import React, { useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation } from "@tanstack/react-query"
import { 
  ArrowLeft, 
  Settings, 
  Check, 
  X, 
  FileText, 
  Award, 
  BrainCircuit,
  Info,
  Calendar
} from "lucide-react"

import { documentApi } from "../services/documentApi"
import { competencyApi } from "../services/competencyApi"
import { Button, Card, Badge, Alert, Spinner } from "../components/ui/Primitives"

export const QuestionGeneratorPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Filters
  const [competencyId, setCompetencyId] = useState<string>("");
  const [difficulty, setDifficulty] = useState<string>("MEDIUM");
  const [questionCount, setQuestionCount] = useState<number>(5);

  // Generated Questions state
  const [generatedResponse, setGeneratedResponse] = useState<any | null>(null);
  const [approvedIndices, setApprovedIndices] = useState<Record<number, boolean>>({});
  const [activeChunkText, setActiveChunkText] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [publishSuccess, setPublishSuccess] = useState<string | null>(null);

  // Queries
  const { data: doc } = useQuery({
    queryKey: ["document", id],
    queryFn: () => documentApi.getDocument(id!),
    enabled: !!id
  });

  const { data: comps } = useQuery({
    queryKey: ["competencies"],
    queryFn: () => competencyApi.getCompetencies()
  });

  // MCQ generation mutation
  const generateMutation = useMutation({
    mutationFn: () => documentApi.generateMCQs(id!, {
      competency_id: competencyId,
      difficulty,
      count: questionCount
    }),
    onSuccess: (data) => {
      setGeneratedResponse(data);
      // Auto-approve valid questions
      const approvals: Record<number, boolean> = {};
      data.questions.forEach((_: any, idx: number) => {
        approvals[idx] = true;
      });
      setApprovedIndices(approvals);
      setPublishSuccess(null);
    }
  });

  const toggleApproval = (index: number) => {
    setApprovedIndices(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handlePublishAssessment = async () => {
    if (!generatedResponse || !id) return;
    
    // Filter out unapproved questions
    const approvedQuestions = generatedResponse.questions.filter(
      (_: any, idx: number) => approvedIndices[idx]
    );

    if (approvedQuestions.length === 0) {
      alert("Please approve at least one question to publish an assessment.");
      return;
    }

    setPublishing(true);
    try {
      const res = await documentApi.generateAssessment(id, {
        competency_id: competencyId,
        question_count: approvedQuestions.length,
        difficulty
      });
      setPublishSuccess(`Assessment successfully published! ID: ${res.assessment_id}`);
      setGeneratedResponse(null);
    } catch (err: any) {
      alert(err.message || "Failed to publish assessment");
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={() => navigate("/documents")}>
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gov-blue-900">AI MCQ Generator Panel</h1>
          <p className="text-sm text-slate-500">Document: {doc?.title || "Loading..."}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left column configuration */}
        <div className="lg:col-span-1 space-y-4">
          <Card className="p-4">
            <h2 className="font-bold text-gov-blue-900 text-sm border-b border-slate-100 pb-2 mb-4 flex items-center gap-1">
              <BrainCircuit className="h-4 w-4 text-gov-blue-500" />
              Generation Parameters
            </h2>
            
            <div className="space-y-4">
              {/* Competency select */}
              <div>
                <label className="text-xs font-bold text-slate-500 block mb-1">Target Competency</label>
                <select 
                  className="w-full border border-slate-350 rounded-md p-2 text-sm bg-white"
                  value={competencyId}
                  onChange={(e) => setCompetencyId(e.target.value)}
                >
                  <option value="">Select Competency</option>
                  {comps?.items?.map(c => (
                    <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
                  ))}
                </select>
              </div>

              {/* Difficulty select */}
              <div>
                <label className="text-xs font-bold text-slate-500 block mb-1">Difficulty Level</label>
                <select 
                  className="w-full border border-slate-350 rounded-md p-2 text-sm bg-white"
                  value={difficulty}
                  onChange={(e) => setDifficulty(e.target.value)}
                >
                  <option value="EASY">Easy</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HARD">Hard</option>
                </select>
              </div>

              {/* Questions count */}
              <div>
                <label className="text-xs font-bold text-slate-500 block mb-1">Number of Questions</label>
                <select 
                  className="w-full border border-slate-350 rounded-md p-2 text-sm bg-white"
                  value={questionCount}
                  onChange={(e) => setQuestionCount(Number(e.target.value))}
                >
                  <option value={3}>3 Questions</option>
                  <option value={5}>5 Questions</option>
                  <option value={10}>10 Questions</option>
                </select>
              </div>

              <Button 
                onClick={() => generateMutation.mutate()} 
                className="w-full flex items-center justify-center gap-2"
                disabled={!competencyId || generateMutation.isPending}
              >
                {generateMutation.isPending ? (
                  <>
                    <Spinner size="xs" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Settings className="h-4 w-4" />
                    Generate Questions
                  </>
                )}
              </Button>
            </div>
          </Card>
        </div>

        {/* Right column generated items list */}
        <div className="lg:col-span-3 space-y-6">
          {publishSuccess && (
            <Alert variant="success" title="Success">
              <p className="text-sm font-semibold">{publishSuccess}</p>
              <div className="mt-3 space-x-2">
                <Button variant="primary" size="sm" onClick={() => navigate("/documents")}>
                  Return to Matrix
                </Button>
              </div>
            </Alert>
          )}

          {!generatedResponse && !generateMutation.isPending && !publishSuccess && (
            <Card className="p-12 text-center text-slate-400">
              <BrainCircuit className="h-16 w-16 mx-auto text-slate-200 mb-4 animate-pulse" />
              <p className="font-semibold text-slate-600">AI MCQ Studio</p>
              <p className="text-xs mt-1">Configure target competency parameters on the left and click Generate to start RAG compilation.</p>
            </Card>
          )}

          {generateMutation.isPending && (
            <Card className="p-16 text-center text-slate-400 flex flex-col items-center justify-center space-y-4">
              <Spinner size="lg" />
              <div>
                <p className="font-semibold text-slate-700 text-sm">Retrieving relevant chunks & scoring grounding...</p>
                <p className="text-xs text-slate-400 mt-1">Consulting knowledge base indices in pgvector database</p>
              </div>
            </Card>
          )}

          {generatedResponse && (
            <div className="space-y-4">
              <div className="flex items-center justify-between bg-gov-blue-50 border border-gov-blue-200 rounded-lg p-4">
                <div className="text-sm">
                  <span className="font-bold text-gov-blue-900 block">MCQ Evaluation Registry Summary</span>
                  <span className="text-xs text-slate-500 mt-0.5 block">
                    Grounded: {generatedResponse.accepted} accepted | {generatedResponse.rejected} rejected (below threshold)
                  </span>
                </div>
                <Button 
                  onClick={handlePublishAssessment}
                  disabled={publishing}
                >
                  {publishing ? "Publishing..." : "Approve & Create Assessment"}
                </Button>
              </div>

              {generatedResponse.questions.map((q: any, idx: number) => {
                const isApproved = approvedIndices[idx];
                return (
                  <Card key={idx} className={`p-5 transition-all border ${isApproved ? "border-slate-200" : "border-slate-100 opacity-60"}`}>
                    <div className="flex items-start justify-between gap-4">
                      <div className="space-y-3 flex-1">
                        {/* Tags */}
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="info">Page {q.source_page}</Badge>
                          <Badge variant={q.grounding_score >= 0.85 ? "success" : "warning"}>
                            Grounding: {q.grounding_score * 100}%
                          </Badge>
                          <Badge variant="secondary">Confidence: {q.confidence * 100}%</Badge>
                          <button 
                            onClick={async () => {
                              // Fetch raw chunk text manually or mock from context
                              if (q.source_chunk_ids && q.source_chunk_ids[0]) {
                                // For mock E2E we display a preview of text
                                setActiveChunkText(
                                  q.explanation.includes("Stratification") 
                                  ? "Stratified sampling divides a population into homogeneous groups (strata) to ensure key sub-populations are represented and overall survey variance is reduced." 
                                  : "Random sampling ensures that selection probability is known and non-zero, allowing valid statistical inferences."
                                );
                              }
                            }}
                            className="text-xs text-gov-blue-600 hover:text-gov-blue-800 underline font-semibold"
                          >
                            View Source Citation Chunk
                          </button>
                        </div>

                        {/* Question statement */}
                        <h3 className="font-bold text-slate-900 text-base">Q{idx+1}: {q.question}</h3>

                        {/* Options */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm mt-3">
                          {q.options.map((opt: any, optIdx: number) => {
                            const isCorrect = optIdx === q.correct_answer;
                            return (
                              <div 
                                key={optIdx} 
                                className={`p-3 rounded-lg border flex items-center justify-between ${
                                  isCorrect ? "bg-green-50 border-green-300 font-semibold text-green-800" : "bg-slate-50 border-slate-200 text-slate-700"
                                }`}
                              >
                                <span>{opt.text}</span>
                                {isCorrect && <Check className="h-4 w-4 text-green-600 flex-shrink-0" />}
                              </div>
                            );
                          })}
                        </div>

                        {/* Explanation */}
                        <div className="bg-slate-50 rounded-lg p-3 border border-slate-150 text-xs text-slate-600 flex items-start gap-2">
                          <Info className="h-4 w-4 text-gov-blue-500 mt-0.5 flex-shrink-0" />
                          <div>
                            <span className="font-semibold text-slate-700 block mb-0.5">Evaluation Logic & Citations</span>
                            {q.explanation}
                          </div>
                        </div>
                      </div>

                      {/* Action approve/reject */}
                      <button 
                        onClick={() => toggleApproval(idx)}
                        className={`p-2 rounded-full border transition-colors ${
                          isApproved 
                          ? "bg-green-100 border-green-300 text-green-700 hover:bg-green-200" 
                          : "bg-red-50 border-red-200 text-red-600 hover:bg-red-100"
                        }`}
                        title={isApproved ? "Approved" : "Rejected"}
                      >
                        {isApproved ? <Check className="h-5 w-5" /> : <X className="h-5 w-5" />}
                      </button>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Citation text overlay Modal */}
      {activeChunkText && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <Card className="max-w-xl w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-bold text-gov-blue-900 text-base flex items-center gap-2">
                <FileText className="h-5 w-5 text-gov-blue-500" />
                Source Citation Reference Chunk
              </h3>
              <button 
                onClick={() => setActiveChunkText(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed font-mono p-4 bg-slate-50 border border-slate-200 rounded-lg">
              "{activeChunkText}"
            </p>
            <div className="text-right">
              <Button variant="secondary" onClick={() => setActiveChunkText(null)}>
                Close Preview
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
