import React, { useState, useEffect } from "react"
import { useParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation } from "@tanstack/react-query"
import { AlertTriangle, Clock, ArrowLeft, ArrowRight, ShieldAlert, Award } from "lucide-react"

import { assessmentApi } from "../services/assessmentApi"
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Progress, Alert } from "../components/ui/Primitives"

export const AssessmentPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const assessmentId = id || "";

  // React State for attempt and answers selection
  const [attempt, setAttempt] = useState<any | null>(null);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // 1. Fetch assessment questions details
  const { 
    data: assessment, 
    isLoading: quizLoading, 
    error: quizError 
  } = useQuery({
    queryKey: ["assessment-questions", assessmentId],
    queryFn: () => assessmentApi.getAssessment(assessmentId),
    enabled: !!assessmentId
  });

  // 2. Start Assessment Attempt mutation
  const startAttemptMutation = useMutation({
    mutationFn: () => assessmentApi.startAttempt(assessmentId),
    onSuccess: (data) => {
      setAttempt(data);
    }
  });

  // Start attempt automatically on mount if assessment is loaded
  useEffect(() => {
    if (assessment && !attempt && !startAttemptMutation.isPending && !startAttemptMutation.isError) {
      startAttemptMutation.mutate();
    }
  }, [assessment, attempt]);

  // 3. Submit Answers mutation
  const submitMutation = useMutation({
    mutationFn: () => {
      const formattedAnswers = Object.entries(selectedAnswers).map(([qId, optId]) => ({
        question_id: qId,
        selected_option_id: optId
      }));
      return assessmentApi.submitAnswers(assessmentId, attempt.attempt_id, formattedAnswers);
    },
    onSuccess: (data) => {
      navigate(`/assessments/${assessmentId}/result`, { state: { result: data } });
    },
    onError: (err: any) => {
      setSubmitError(err.message || "Failed to submit answers. Make sure all questions are answered.");
    }
  });

  if (quizLoading || startAttemptMutation.isPending) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <svg className="animate-spin h-10 w-10 text-gov-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span className="text-sm font-semibold text-slate-500">Initializing secure assessment session...</span>
      </div>
    );
  }

  if (quizError || !assessment) {
    return (
      <div className="text-center py-12">
        <ShieldAlert className="h-12 w-12 text-rose-500 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-900">Error loading quiz details</h3>
        <p className="text-sm text-slate-500 mt-2">Verify assessment ID or server connections.</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate("/learning-plan")}>Back to Learning Plan</Button>
      </div>
    );
  }

  const questions = attempt?.questions || assessment?.questions || [];
  const totalQuestions = questions.length;
  
  if (totalQuestions === 0) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-bold text-slate-900 font-sans">No questions seeded inside this assessment.</h3>
        <Button variant="outline" className="mt-4" onClick={() => navigate("/learning-plan")}>Back</Button>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const progressPercentage = Math.round(((currentQuestionIndex + 1) / totalQuestions) * 100);

  const handleOptionSelect = (optionId: string) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: optionId
    }));
  };

  const handleNext = () => {
    if (currentQuestionIndex < totalQuestions - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const handleSubmit = () => {
    if (Object.keys(selectedAnswers).length < totalQuestions) {
      setSubmitError("Please answer all questions before submitting.");
      return;
    }
    submitMutation.mutate();
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Quiz info banner */}
      <div className="flex justify-between items-center border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-lg font-bold text-slate-900 leading-snug">{assessment.title}</h1>
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mt-1">Audit assessment checkpoint</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 bg-amber-50 border border-amber-200 px-3 py-1 rounded-md">
          <Clock className="h-4 w-4" />
          <span>30 mins limit</span>
        </div>
      </div>

      {/* Progress indicators */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs font-semibold text-slate-500">
          <span>Question {currentQuestionIndex + 1} of {totalQuestions}</span>
          <span>Progress {progressPercentage}%</span>
        </div>
        <Progress value={progressPercentage} colorClassName="bg-gov-blue-500" />
      </div>

      {submitError && (
        <Alert variant="destructive" className="bg-red-50 border-red-200 text-red-800">
          <div className="flex gap-2 items-center">
            <ShieldAlert className="h-4 w-4 shrink-0 text-red-600" />
            <span>{submitError}</span>
          </div>
        </Alert>
      )}

      {/* Question Card Display */}
      <Card className="shadow-md">
        <CardHeader className="bg-slate-50/50 py-5">
          <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider block mb-1">Audit question statement</span>
          <h2 className="text-sm font-semibold text-slate-800 leading-relaxed">
            {currentQuestion.text || currentQuestion.question_text}
          </h2>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          <span className="text-[10px] text-slate-400 font-extrabold uppercase tracking-wider block mb-2">Select one option:</span>
          
          <div className="space-y-3">
            {currentQuestion.options.map((opt: any) => {
              const isSelected = selectedAnswers[currentQuestion.id] === opt.id;
              
              return (
                <div 
                  key={opt.id}
                  onClick={() => handleOptionSelect(opt.id)}
                  className={`p-4 border rounded-md cursor-pointer transition-all flex items-center gap-3 ${
                    isSelected 
                      ? "bg-gov-blue-50/40 border-gov-blue-500 shadow-sm" 
                      : "border-slate-200 hover:border-slate-300 hover:bg-slate-50/30"
                  }`}
                >
                  {/* Styled Radio Input */}
                  <div className={`w-4.5 h-4.5 rounded-full border-2 flex items-center justify-center shrink-0 ${
                    isSelected ? "border-gov-blue-500 bg-gov-blue-500" : "border-slate-300"
                  }`}>
                    {isSelected && <div className="w-1.5 h-1.5 bg-white rounded-full" />}
                  </div>
                  <span className="text-xs text-slate-700 font-medium leading-normal">{opt.text || opt.option_text}</span>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Navigation Buttons Row */}
      <div className="flex justify-between items-center pt-2">
        <Button 
          variant="outline" 
          onClick={handlePrev}
          disabled={currentQuestionIndex === 0}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Previous
        </Button>

        {currentQuestionIndex === totalQuestions - 1 ? (
          <Button 
            variant="primary" 
            className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold border-amber-600 px-6"
            onClick={handleSubmit}
            isLoading={submitMutation.isPending}
          >
            Submit Assessment
          </Button>
        ) : (
          <Button 
            variant="outline" 
            onClick={handleNext}
            disabled={!selectedAnswers[currentQuestion.id]}
          >
            Next
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        )}
      </div>
    </div>
  )
}
