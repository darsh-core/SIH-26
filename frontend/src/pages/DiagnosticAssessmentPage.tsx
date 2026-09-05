import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { 
  Sparkles, 
  BrainCircuit, 
  CheckCircle, 
  ArrowRight, 
  ArrowLeft, 
  Clock, 
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  BarChart3
} from "lucide-react";
import { assessmentApi, SubmitAnswerItem } from "../services/assessmentApi";
import { authApi } from "../services/authApi";
import { roleApi } from "../services/roleApi";
import { useAuthStore } from "../store/authStore";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from "../components/ui/Primitives";

interface QuestionItem {
  id: string;
  text: string;
  question_type: string;
  options: Array<{
    id: string;
    text: string;
  }>;
}

const EVALUATED_COMPETENCIES = [
  "Survey Design",
  "Sampling Methodology",
  "Data Quality",
  "Metadata Standards",
  "SQL",
  "Communication",
  "Ethics"
];

export const DiagnosticAssessmentPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user, updateUser } = useAuthStore();

  const [resolvedAssessmentId, setResolvedAssessmentId] = useState<string>(
    searchParams.get("assessment_id") || ""
  );
  const roleName = searchParams.get("role_name") || user?.profile?.designation || "Statistical Officer";
  const departmentName = searchParams.get("dept") || user?.profile?.department || "Agricultural Statistics Division";

  const [loading, setLoading] = useState(true);
  const [attemptId, setAttemptId] = useState<string>("");
  const [questions, setQuestions] = useState<QuestionItem[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [analyzingStage, setAnalyzingStage] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Auto-initialize diagnostic attempt on load
  useEffect(() => {
    setLoading(true);
    setError(null);

    const initAttempt = async () => {
      try {
        let activeId = searchParams.get("assessment_id");

        // If no ID or if it's the old placeholder, generate or retrieve a role diagnostic
        if (!activeId || activeId === "2e1fe4bb-22dd-48a0-9ed4-b08ca0730bc6") {
          const roleId = user?.profile?.job_role_id;
          if (roleId) {
            const diag = await assessmentApi.createRoleDiagnostic(roleId, 6);
            activeId = diag.assessment_id;
          } else {
            const roles = await roleApi.getRoles();
            const statRole = roles.find(r => r.code === "ROLE_STAT_OFFICER") || roles[0];
            const diag = await assessmentApi.createRoleDiagnostic(statRole.id, 6);
            activeId = diag.assessment_id;
          }
          setResolvedAssessmentId(activeId);
        } else {
          setResolvedAssessmentId(activeId);
        }

        const res = await assessmentApi.startAttempt(activeId);
        setAttemptId(res.attempt_id);
        setQuestions(res.questions || []);
      } catch (err: any) {
        console.error("Failed to start diagnostic attempt:", err);
        setError("Unable to initiate assessment attempt. Please verify network connection or try again.");
      } finally {
        setLoading(false);
      }
    };

    initAttempt();
  }, [searchParams, user]);

  const handleSelectOption = (questionId: string, optionId: string) => {
    setAnswers(prev => ({ ...prev, [questionId]: optionId }));
  };

  const currentQ = questions[currentIdx];
  const progressPercent = questions.length > 0 ? Math.round(((currentIdx + 1) / questions.length) * 100) : 0;
  const isLastQuestion = currentIdx === questions.length - 1;
  const allAnswered = questions.length > 0 && Object.keys(answers).length === questions.length;

  const handleSubmit = async () => {
    if (!attemptId || submitting) return;
    setSubmitting(true);
    setError(null);

    const formattedAnswers: SubmitAnswerItem[] = Object.entries(answers).map(([qId, optId]) => ({
      question_id: qId,
      selected_option_id: optId
    }));

    const activeId = resolvedAssessmentId || searchParams.get("assessment_id") || "";

    try {
      // 1. Submit answers to backend
      await assessmentApi.submitAnswers(activeId, attemptId, formattedAnswers);

      // 2. Refresh user profile in Zustand auth store so has_completed_assessment is now TRUE!
      try {
        const updatedUser = await authApi.getMe();
        updateUser(updatedUser);
      } catch (e) {
        console.warn("Could not refresh user profile:", e);
        if (user) {
          updateUser({ ...user, has_completed_assessment: true });
        }
      }

      // 3. Play sequential calculation transition messages
      setAnalyzingStage(1);
      setTimeout(() => setAnalyzingStage(2), 700);
      setTimeout(() => setAnalyzingStage(3), 1400);
      setTimeout(() => setAnalyzingStage(4), 2100);
      setTimeout(() => {
        navigate(`/initial-status?assessment_id=${activeId}&attempt_id=${attemptId}`);
      }, 2800);

    } catch (err: any) {
      console.error("Submission failed:", err);
      setError("Failed to submit diagnostic assessment. Please try again.");
      setSubmitting(false);
      setAnalyzingStage(null);
    }
  };

  // -------------------------------------------------------------
  // Transition / Analysis Screen (Prompt Section 6)
  // -------------------------------------------------------------
  if (analyzingStage !== null) {
    const stageMessages = [
      "Assessment Complete. Initializing evaluation...",
      "Analyzing your competency profile...",
      "Comparing your results with the requirements of your role...",
      "Identifying your priority skill gaps...",
      "Preparing your personalized learning plan..."
    ];

    return (
      <div className="min-h-[70vh] flex flex-col items-center justify-center p-6 text-center max-w-lg mx-auto">
        <div className="w-16 h-16 rounded-2xl bg-gov-blue-50 text-gov-blue-500 border border-gov-blue-200 flex items-center justify-center mb-6 animate-pulse">
          <BrainCircuit className="w-8 h-8" />
        </div>

        <h2 className="text-xl font-bold text-slate-900 mb-2">
          Assessment Complete
        </h2>
        <p className="text-sm text-slate-500 mb-8">
          Generating your official MoSPI competency twin against role standards.
        </p>

        {/* Progress Stages */}
        <div className="w-full space-y-3 text-left bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          {stageMessages.slice(1).map((msg, i) => {
            const stepNum = i + 1;
            const isDone = analyzingStage > stepNum;
            const isCurrent = analyzingStage === stepNum;

            return (
              <div 
                key={i} 
                className={`flex items-center gap-3 text-xs transition-opacity duration-300 ${
                  isDone ? "text-slate-800 font-semibold" : (isCurrent ? "text-gov-blue-600 font-bold" : "text-slate-400 opacity-60")
                }`}
              >
                {isDone ? (
                  <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                ) : isCurrent ? (
                  <div className="w-4 h-4 rounded-full border-2 border-gov-blue-500 border-t-transparent animate-spin shrink-0" />
                ) : (
                  <div className="w-4 h-4 rounded-full border border-slate-300 shrink-0" />
                )}
                <span>{msg}</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Loading State
  // -------------------------------------------------------------
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-gov-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-semibold text-slate-600">Loading AI Role Diagnostic questions...</p>
      </div>
    );
  }

  // -------------------------------------------------------------
  // Error State
  // -------------------------------------------------------------
  if (error || questions.length === 0) {
    return (
      <div className="max-w-md mx-auto my-12 text-center p-6 bg-white rounded-xl border border-slate-200 shadow-xs">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-900">Diagnostic Checkpoint Notice</h3>
        <p className="text-xs text-slate-500 mt-2 leading-relaxed">
          {error || "No diagnostic questions were found for this role track. Please retry or contact NSSTA support."}
        </p>
        <Button onClick={() => window.location.reload()} className="mt-4 bg-gov-blue-500 text-white text-xs">
          Retry Diagnostic
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* 1. Header Information Block (Prompt Section 5) */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 sm:p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">AI Role Diagnostic</h1>
              <Badge variant="info">Baseline Evaluation</Badge>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Role: <strong className="text-slate-800">{roleName}</strong> · Department: <strong className="text-slate-800">{departmentName}</strong>
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-500 font-medium">
            <span className="flex items-center gap-1">
              <HelpCircle className="w-4 h-4 text-gov-blue-500" />
              {questions.length} Questions
            </span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4 text-slate-400" />
              5–10 mins
            </span>
          </div>
        </div>

        <p className="text-xs text-slate-600 mt-3.5 leading-relaxed">
          <strong>Purpose:</strong> This assessment evaluates your current competency level against the requirements of your selected role.
        </p>

        {/* Evaluated Competencies tags */}
        <div className="mt-3 flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mr-1">Competencies:</span>
          {EVALUATED_COMPETENCIES.map((comp, idx) => (
            <span key={idx} className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium">
              {comp}
            </span>
          ))}
        </div>
      </div>

      {/* 2. Progress Indicator Bar */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs font-semibold text-slate-500">
          <span>Question {currentIdx + 1} of {questions.length}</span>
          <span>{progressPercent}% Completed</span>
        </div>
        <Progress value={progressPercent} className="h-2" colorClassName="bg-gov-blue-500" />
      </div>

      {/* 3. Question Card */}
      {currentQ && (
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span className="font-bold text-gov-blue-500 uppercase tracking-wider">Item #{currentIdx + 1}</span>
              <span className="text-[11px] font-mono bg-white px-2 py-0.5 rounded border border-slate-200">
                Single Choice
              </span>
            </div>
            <CardTitle className="text-base font-semibold text-slate-900 mt-2 leading-relaxed">
              {currentQ.text}
            </CardTitle>
          </CardHeader>

          <CardContent className="p-6 space-y-3">
            {currentQ.options.map((opt, oIdx) => {
              const isSelected = answers[currentQ.id] === opt.id;
              const optionLetter = String.fromCharCode(65 + oIdx);

              return (
                <div
                  key={opt.id}
                  onClick={() => handleSelectOption(currentQ.id, opt.id)}
                  className={`p-3.5 rounded-xl border text-xs sm:text-sm flex items-start gap-3 cursor-pointer transition-all ${
                    isSelected
                      ? "bg-indigo-50/70 border-gov-blue-500 ring-2 ring-gov-blue-500/20 text-slate-900 font-medium"
                      : "bg-white border-slate-200 hover:border-slate-300 text-slate-700 hover:bg-slate-50/60"
                  }`}
                >
                  <span className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold shrink-0 transition-colors ${
                    isSelected ? "bg-gov-blue-500 text-white" : "bg-slate-100 text-slate-600"
                  }`}>
                    {optionLetter}
                  </span>
                  <span className="pt-0.5 leading-relaxed">{opt.text}</span>
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* 4. Action Buttons (Prev, Next, Submit) */}
      <div className="flex items-center justify-between pt-2">
        <Button
          variant="outline"
          onClick={() => setCurrentIdx(prev => Math.max(0, prev - 1))}
          disabled={currentIdx === 0}
          className="flex items-center gap-1.5 text-xs"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Previous</span>
        </Button>

        {isLastQuestion ? (
          <Button
            onClick={handleSubmit}
            disabled={submitting || !allAnswered}
            className="flex items-center gap-2 bg-gov-blue-500 hover:bg-gov-blue-600 text-white font-bold px-6 py-2.5 rounded-lg shadow-md"
          >
            {submitting ? (
              <span>Submitting Assessment...</span>
            ) : (
              <>
                <span>Submit Assessment</span>
                <CheckCircle className="w-4 h-4" />
              </>
            )}
          </Button>
        ) : (
          <Button
            onClick={() => setCurrentIdx(prev => Math.min(questions.length - 1, prev + 1))}
            className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs px-5 py-2.5 rounded-lg shadow-xs"
          >
            <span>Next</span>
            <ArrowRight className="w-4 h-4" />
          </Button>
        )}
      </div>
    </div>
  );
};
