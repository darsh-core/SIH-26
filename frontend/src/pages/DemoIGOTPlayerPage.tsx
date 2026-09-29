import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { 
  Award, 
  ArrowLeft, 
  CheckCircle2, 
  Circle, 
  Clock, 
  BookOpen, 
  Play, 
  ArrowRight, 
  ChevronRight, 
  ChevronLeft,
  ShieldCheck, 
  Sparkles, 
  FileText,
  AlertCircle,
  Download,
  Eye,
  Check,
  HelpCircle,
  FileCheck,
  Video,
  ListOrdered,
  X
} from "lucide-react";
import { learningApi } from "../services/learningApi";
import { Button, Badge, Progress } from "../components/ui/Primitives";

// Sample Trainer-Generated MCQ Assessment Questions
const TRAINER_MCQ_QUESTIONS = [
  {
    id: "q1",
    question: "Which sampling design is recommended by MoSPI for nationwide household inquiries where Primary Sampling Units (PSUs) vary significantly in population size?",
    options: [
      "Probability Proportional to Size (PPS) Sampling",
      "Simple Random Sampling Without Replacement (SRSWOR)",
      "Convenience Sampling",
      "Non-proportional Quota Sampling"
    ],
    correctIdx: 0,
    explanation: "Probability Proportional to Size (PPS) sampling ensures larger clusters (e.g. villages or UFS blocks) have an inclusion probability proportional to their size, minimizing total estimation variance."
  },
  {
    id: "q2",
    question: "Under MoSPI statistical audit guidelines, what is the Relative Standard Error (RSE) threshold above which estimates must be flagged with cautionary reliability caveats?",
    options: [
      "RSE > 5%",
      "RSE > 20%",
      "RSE > 35%",
      "RSE > 50%"
    ],
    correctIdx: 1,
    explanation: "Official statistical reports require flagging point estimates with RSE exceeding 20% to caution policy planners regarding sample variance limits."
  },
  {
    id: "q3",
    question: "What is the primary operational objective of pilot pre-testing and cognitive interviewing during questionnaire schedule design?",
    options: [
      "To reduce enumerator travel costs",
      "To test respondent comprehension, recall strategies, and isolate ambiguous phrasing before deployment",
      "To automatically eliminate non-response rates",
      "To replace supervisory field inspection"
    ],
    correctIdx: 1,
    explanation: "Cognitive interviewing evaluates how respondents interpret questions and recall data, allowing survey methodologists to refine schedules prior to nationwide rollout."
  }
];

export const DemoIGOTPlayerPage: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [activeModuleIdx, setActiveModuleIdx] = useState<number>(0);
  const [activeLessonIdx, setActiveLessonIdx] = useState<number>(0);

  // PDF Preview Modal State
  const [showPdfModal, setShowPdfModal] = useState<boolean>(false);

  // Trainer MCQ State
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [assessmentSubmitted, setAssessmentSubmitted] = useState<boolean>(false);
  const [assessmentScore, setAssessmentScore] = useState<number>(0);

  // 1. Fetch Course Details with Modules & Lessons
  const {
    data: course,
    isLoading: courseLoading,
    error: courseError,
  } = useQuery({
    queryKey: ["learning-course", courseId],
    queryFn: () => learningApi.getCourse(courseId!),
    enabled: !!courseId,
  });

  // 2. Fetch Progress
  const {
    data: progress,
    isLoading: progressLoading,
  } = useQuery({
    queryKey: ["learning-progress", courseId],
    queryFn: () => learningApi.getProgress(courseId!),
    enabled: !!courseId,
  });

  // Complete module mutation
  const completeModuleMutation = useMutation({
    mutationFn: (moduleId: string) => learningApi.completeModule(courseId!, moduleId),
    onSuccess: (updated) => {
      queryClient.setQueryData(["learning-progress", courseId], updated);
      queryClient.invalidateQueries({ queryKey: ["learning-history"] });
      queryClient.invalidateQueries({ queryKey: ["learning-plans"] });
      if (course && activeModuleIdx < course.modules.length - 1) {
        setActiveModuleIdx(prev => prev + 1);
        setActiveLessonIdx(0);
        setAssessmentSubmitted(false);
        setSelectedAnswers({});
      }
    },
  });

  // Complete course mutation
  const completeCourseMutation = useMutation({
    mutationFn: () => learningApi.completeCourse(courseId!),
    onSuccess: (updated) => {
      queryClient.setQueryData(["learning-progress", courseId], updated);
      queryClient.invalidateQueries({ queryKey: ["learning-history"] });
      queryClient.invalidateQueries({ queryKey: ["competency-gaps"] });
      queryClient.invalidateQueries({ queryKey: ["learning-plans"] });
    },
  });

  if (courseLoading || progressLoading) {
    return (
      <div className="fixed inset-0 z-50 bg-slate-950 flex flex-col items-center justify-center gap-4 text-white">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-semibold text-slate-400">Launching iGOT Full-Screen Immersive Canvas...</span>
      </div>
    );
  }

  if (courseError || !course) {
    return (
      <div className="fixed inset-0 z-50 bg-slate-950 flex flex-col items-center justify-center p-6 text-center text-white space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h2 className="text-xl font-bold">Learning Resource Unavailable</h2>
        <p className="text-sm text-slate-400 max-w-md">The requested course could not be retrieved.</p>
        <Button variant="outline" className="text-slate-900 bg-white hover:bg-slate-100" onClick={() => navigate("/dashboard")}>
          Return to Dashboard
        </Button>
      </div>
    );
  }

  const modules = course.modules || [];
  const currentModule = modules[activeModuleIdx] || modules[0];
  const currentLessons = currentModule?.lessons || [];
  const currentLesson = currentLessons[activeLessonIdx] || currentLessons[0];

  const isLastLesson = activeLessonIdx >= currentLessons.length - 1;
  const isLastModule = activeModuleIdx >= modules.length - 1;

  const handlePrev = () => {
    if (activeLessonIdx > 0) {
      setActiveLessonIdx(prev => prev - 1);
    } else if (activeModuleIdx > 0) {
      setActiveModuleIdx(prev => prev - 1);
      const prevModLessons = modules[activeModuleIdx - 1]?.lessons || [];
      setActiveLessonIdx(Math.max(0, prevModLessons.length - 1));
    }
  };

  const handleNext = () => {
    if (activeLessonIdx < currentLessons.length - 1) {
      setActiveLessonIdx(prev => prev + 1);
    } else if (activeModuleIdx < modules.length - 1) {
      setActiveModuleIdx(prev => prev + 1);
      setActiveLessonIdx(0);
    }
  };

  const handleOptionSelect = (qId: string, optIdx: number) => {
    if (assessmentSubmitted) return;
    setSelectedAnswers(prev => ({ ...prev, [qId]: optIdx }));
  };

  const handleSubmitAssessment = () => {
    let score = 0;
    TRAINER_MCQ_QUESTIONS.forEach(q => {
      if (selectedAnswers[q.id] === q.correctIdx) {
        score += 1;
      }
    });
    const finalPct = Math.round((score / TRAINER_MCQ_QUESTIONS.length) * 100);
    setAssessmentScore(finalPct);
    setAssessmentSubmitted(true);

    if (currentModule) {
      completeModuleMutation.mutate(currentModule.id);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950 text-slate-100 flex flex-col font-sans overflow-hidden">
      
      {/* =========================================================
         TOP PLAYER CONTROL HEADER (No AppShell Left or Top Navbars!)
         ========================================================= */}
      <header className="h-16 bg-slate-900 border-b border-slate-800 px-4 sm:px-6 flex items-center justify-between shrink-0 z-20">
        
        {/* Left: Exit & Title */}
        <div className="flex items-center gap-4 min-w-0">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-2 text-xs font-bold text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700 transition-colors shrink-0"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Exit to VICTUS 11</span>
          </button>

          <div className="h-4 w-px bg-slate-800 hidden sm:block shrink-0" />

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-600/30 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded">
                iGOT Karmayogi
              </span>
              <span className="text-xs font-bold text-white truncate max-w-xs sm:max-w-md">
                {course.title}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 truncate">
              Module {activeModuleIdx + 1} of {modules.length}: <strong className="text-slate-200">{currentModule?.title}</strong>
            </p>
          </div>
        </div>

        {/* Center / Right: PREVIOUS & NEXT Buttons */}
        <div className="flex items-center gap-3 shrink-0">
          <Button
            size="sm"
            disabled={activeLessonIdx === 0 && activeModuleIdx === 0}
            onClick={handlePrev}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700 text-xs font-bold px-3.5 h-9 gap-1.5"
          >
            <ChevronLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Previous</span>
          </Button>

          <Button
            size="sm"
            disabled={isLastModule && isLastLesson}
            onClick={handleNext}
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 h-9 gap-1.5 shadow-sm"
          >
            <span className="hidden sm:inline">Next</span>
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* =========================================================
         MAIN WORKSPACE: LEFT CURRICULUM PANEL + CENTER VIDEO & CONTENT
         ========================================================= */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* ---------------------------------------------------------
           LEFT SIDE PANEL: CURRICULUM CONTENTS LIST
           --------------------------------------------------------- */}
        <aside className="w-80 sm:w-88 bg-slate-950 border-r border-slate-800 flex flex-col shrink-0 overflow-y-auto">
          <div className="p-4 border-b border-slate-800 bg-slate-900/60 flex items-center justify-between">
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-300 flex items-center gap-2">
              <ListOrdered className="w-4 h-4 text-blue-400" />
              <span>Curriculum Outline</span>
            </h3>
            <span className="text-[11px] font-bold text-blue-400 bg-blue-950 px-2 py-0.5 rounded border border-blue-800">
              {modules.length} Modules
            </span>
          </div>

          <div className="p-3 space-y-3 flex-1">
            {modules.map((m, mIdx) => {
              const isModSelected = mIdx === activeModuleIdx;
              const lessons = m.lessons || [];

              return (
                <div key={m.id} className="rounded-xl border border-slate-800 bg-slate-900/80 overflow-hidden">
                  <button
                    onClick={() => {
                      setActiveModuleIdx(mIdx);
                      setActiveLessonIdx(0);
                    }}
                    className={`w-full p-3.5 text-left flex items-start justify-between gap-3 transition-colors ${
                      isModSelected 
                        ? "bg-blue-950/60 border-l-4 border-l-blue-500 text-white" 
                        : "hover:bg-slate-800/60 text-slate-300"
                    }`}
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-slate-400 uppercase">
                          Module {m.sequence_order}
                        </span>
                        <span className="text-[10px] text-slate-500">• {m.duration_minutes}m</span>
                      </div>
                      <h4 className="text-xs font-bold leading-tight truncate">{m.title}</h4>
                    </div>

                    <div className="shrink-0 mt-1">
                      {isModSelected ? (
                        <Play className="w-4 h-4 text-blue-400 fill-current" />
                      ) : (
                        <Circle className="w-4 h-4 text-slate-600" />
                      )}
                    </div>
                  </button>

                  {/* Lesson List */}
                  {isModSelected && lessons.length > 0 && (
                    <div className="bg-slate-950/90 border-t border-slate-800 p-2 space-y-1">
                      {lessons.map((l, lIdx) => {
                        const isLessSelected = lIdx === activeLessonIdx;
                        return (
                          <button
                            key={l.id}
                            onClick={() => setActiveLessonIdx(lIdx)}
                            className={`w-full p-2 rounded-lg text-left text-xs flex items-center justify-between transition-all ${
                              isLessSelected
                                ? "bg-blue-600 text-white font-bold shadow-xs"
                                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900"
                            }`}
                          >
                            <div className="flex items-center gap-2 truncate">
                              <Video className="w-3.5 h-3.5 shrink-0" />
                              <span className="truncate">{l.sequence_order}. {l.title}</span>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}


                </div>
              );
            })}
          </div>
        </aside>

        {/* ---------------------------------------------------------
           CENTER AREA: VIDEO PLAYER + ABOUT/DESC/OUTCOMES + PDF & MCQ
           --------------------------------------------------------- */}
        <main className="flex-1 bg-slate-900 overflow-y-auto p-4 sm:p-8 space-y-8">
          
          {/* 1. CENTER VIDEO PLAYER VIEWPORT (16:9 HD Simulation) */}
          <div className="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl">
            <div className="relative aspect-video bg-gradient-to-br from-slate-900 via-slate-950 to-black flex flex-col justify-between p-6 group">
              
              {/* Top Video Overlay Bar */}
              <div className="flex items-center justify-between gap-4 z-10">
                <span className="text-[10px] font-extrabold uppercase tracking-wider bg-blue-600 text-white px-2.5 py-1 rounded">
                  iGOT HD Video Player
                </span>
                <span className="text-xs text-slate-300 font-medium bg-black/60 px-3 py-1 rounded-full backdrop-blur-xs">
                  Speaker: Dr. Ramesh Kumar · Senior Statistical Advisor, MoSPI
                </span>
              </div>

              {/* Central Play Indicator */}
              <div className="text-center space-y-3 z-10 my-auto">
                <div className="w-20 h-20 rounded-full bg-blue-600/30 border-2 border-blue-400/60 flex items-center justify-center mx-auto shadow-2xl text-white cursor-pointer hover:scale-105 transition-transform">
                  <Play className="w-8 h-8 fill-current ml-1" />
                </div>
                <div>
                  <h2 className="text-lg sm:text-xl font-extrabold text-white">{currentLesson?.title || "Lesson Lecture"}</h2>
                  <p className="text-xs text-slate-400 mt-1 font-normal">Module {currentModule?.sequence_order}: {currentModule?.title}</p>
                </div>
              </div>

              {/* Bottom Video Control Bar */}
              <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-3 flex items-center justify-between gap-4 text-xs text-white z-10 backdrop-blur-xs">
                <div className="flex items-center gap-3">
                  <button className="p-1.5 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-bold transition-colors">
                    <Play className="w-4 h-4 fill-current" />
                  </button>
                  <span className="font-mono text-xs text-slate-300">04:15 / {currentLesson?.duration_minutes || 15}:00</span>
                </div>

                <div className="flex-1 max-w-md bg-slate-800 h-2 rounded-full overflow-hidden cursor-pointer">
                  <div className="bg-blue-500 h-full w-[40%]" />
                </div>

                <div className="flex items-center gap-2">
                  <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded text-[11px] font-mono">1.0x</span>
                  <span className="bg-emerald-600 text-white px-2 py-0.5 rounded text-[10px] font-bold">1080p HD</span>
                </div>
              </div>

            </div>
          </div>

          {/* 2. BELOW VIDEO: ABOUT, DESCRIPTION & OUTCOME FOR EACH MODULE */}
          <div className="bg-slate-950 rounded-2xl border border-slate-800 p-6 space-y-6">
            
            {/* Header */}
            <div className="border-b border-slate-800 pb-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400 block">
                Module Details & Scope
              </span>
              <h3 className="text-lg font-extrabold text-white mt-0.5">{currentModule?.title}</h3>
            </div>

            {/* About Section */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-400" />
                <span>About This Module</span>
              </h4>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal bg-slate-900 p-4 rounded-xl border border-slate-800">
                This module establishes core operational procedures for {currentModule?.title} under MoSPI standards. Officers learn to execute sampling inquiry schedules, audit auxiliary boundary changes, and maintain rigorous data quality controls.
              </p>
            </div>

            {/* Description Section */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <span>Operational Description</span>
              </h4>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
                {currentLesson?.content || currentModule?.description || "Official capacity building content."}
              </p>
            </div>

            {/* Learning Outcomes Section */}
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-400" />
                <span>Learning Outcomes Mastered</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-300">Design and validate sampling inquiry schedules in accordance with Collection of Statistics rules.</span>
                </div>
                <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-300">Calculate Probability Proportional to Size (PPS) inclusion weights to minimize sample variance.</span>
                </div>
                <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-300">Execute multi-tier supervisory inspections and independent household re-interviews.</span>
                </div>
                <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-xl flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-300">Compute Relative Standard Error (RSE) metrics to audit official report reliability thresholds.</span>
                </div>
              </div>
            </div>

          </div>

          {/* 3. END OF ENTIRE MODULE: PDF NOTES & TRAINER MCQ ASSESSMENT */}
          <div className="bg-slate-950 rounded-2xl border border-blue-900/60 p-6 sm:p-8 space-y-8">
            
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block">
                  End of Module Evaluation & Resources
                </span>
                <h3 className="text-xl font-extrabold text-white mt-0.5">Module Notes & Trainer-Generated Assessment</h3>
              </div>
              <Badge className="bg-blue-600 text-white text-xs font-bold px-3 py-1">
                Final Evaluation
              </Badge>
            </div>

            {/* A. NOTES AS PDF CARD */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-start gap-3.5">
                  <div className="w-12 h-12 rounded-xl bg-rose-500/20 border border-rose-500/30 flex items-center justify-center shrink-0 text-rose-400">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">Official MoSPI Module Reference Notes & Guidelines.pdf</h4>
                    <p className="text-xs text-slate-400 mt-0.5">Comprehensive module summary notes, formulas, and field protocols · 2.4 MB</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setShowPdfModal(true)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700 text-xs font-bold gap-1.5"
                  >
                    <Eye className="w-4 h-4 text-blue-400" />
                    <span>Preview PDF Notes</span>
                  </Button>

                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      alert("Downloading MoSPI Module Reference Notes PDF...");
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 py-2 rounded-lg flex items-center gap-1.5 transition-colors shadow-xs"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download PDF</span>
                  </a>
                </div>
              </div>
            </div>

            {/* B. MCQ ASSESSMENT GENERATED BY TRAINER */}
            <div className="space-y-6 pt-4 border-t border-slate-800">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-base font-extrabold text-white flex items-center gap-2">
                    <HelpCircle className="w-5 h-5 text-amber-400" />
                    <span>Trainer-Generated MCQ Assessment</span>
                  </h4>
                  <p className="text-xs text-slate-400 mt-1">
                    Complete these trainer-authored questions to verify your competency advancement for <strong className="text-slate-200">Sampling Methodology</strong>.
                  </p>
                </div>

                {assessmentSubmitted && (
                  <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                    assessmentScore >= 60 
                      ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" 
                      : "bg-rose-500/20 text-rose-300 border-rose-500/30"
                  }`}>
                    Score: {assessmentScore}% ({assessmentScore >= 60 ? "PASSED" : "NEEDS RETAKE"})
                  </span>
                )}
              </div>

              {/* Questions List */}
              <div className="space-y-6">
                {TRAINER_MCQ_QUESTIONS.map((q, qIdx) => {
                  const selectedOpt = selectedAnswers[q.id];
                  const isCorrect = selectedOpt === q.correctIdx;

                  return (
                    <div key={q.id} className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
                      <div className="flex items-start gap-3">
                        <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0">
                          {qIdx + 1}
                        </span>
                        <h5 className="text-sm font-bold text-white leading-relaxed">{q.question}</h5>
                      </div>

                      {/* Options */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-9">
                        {q.options.map((opt, optIdx) => {
                          const isSelected = selectedOpt === optIdx;
                          let optionStyle = "bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800 hover:border-slate-700";

                          if (assessmentSubmitted) {
                            if (optIdx === q.correctIdx) {
                              optionStyle = "bg-emerald-950/80 border-emerald-500 text-emerald-200 font-bold";
                            } else if (isSelected && !isCorrect) {
                              optionStyle = "bg-rose-950/80 border-rose-500 text-rose-200 font-bold";
                            }
                          } else if (isSelected) {
                            optionStyle = "bg-blue-600/30 border-blue-500 text-white font-bold";
                          }

                          return (
                            <button
                              key={optIdx}
                              disabled={assessmentSubmitted}
                              onClick={() => handleOptionSelect(q.id, optIdx)}
                              className={`p-3 rounded-lg border text-xs text-left transition-all flex items-center justify-between ${optionStyle}`}
                            >
                              <span>{String.fromCharCode(65 + optIdx)}. {opt}</span>
                              {isSelected && !assessmentSubmitted && <Check className="w-4 h-4 text-blue-400" />}
                              {assessmentSubmitted && optIdx === q.correctIdx && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                            </button>
                          );
                        })}
                      </div>

                      {/* Explanation box after submit */}
                      {assessmentSubmitted && (
                        <div className="ml-9 p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-400 space-y-1">
                          <strong className="text-amber-400 block font-semibold">Trainer Explanation:</strong>
                          <p>{q.explanation}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Submit Assessment Action */}
              <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                <p className="text-xs text-slate-400">
                  Passing criteria: 60% or higher required to update Competency Twin.
                </p>

                {!assessmentSubmitted ? (
                  <Button
                    onClick={handleSubmitAssessment}
                    disabled={Object.keys(selectedAnswers).length < TRAINER_MCQ_QUESTIONS.length}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-6 py-2.5 rounded-lg shadow-sm"
                  >
                    <span>Submit Assessment & Verify Competency</span>
                  </Button>
                ) : (
                  <Button
                    onClick={() => {
                      if (isLastModule) {
                        completeCourseMutation.mutate();
                      } else {
                        handleNext();
                      }
                    }}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-6 py-2.5 rounded-lg shadow-sm gap-2"
                  >
                    <span>{isLastModule ? "Complete Course & Update Competency Twin" : "Proceed to Next Module"}</span>
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                )}
              </div>

            </div>

          </div>

        </main>
      </div>

      {/* =========================================================
         PDF PREVIEW MODAL
         ========================================================= */}
      {showPdfModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
            
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-rose-400" />
                <h3 className="text-sm font-bold text-white">Official MoSPI Module Reference Notes & Guidelines.pdf</h3>
              </div>
              <button
                onClick={() => setShowPdfModal(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body - PDF Document Simulation Viewer */}
            <div className="p-6 overflow-y-auto space-y-6 text-slate-300 font-serif text-sm bg-slate-950 leading-relaxed">
              <div className="text-center border-b border-slate-800 pb-4 space-y-1">
                <h2 className="text-lg font-bold text-white font-sans">MINISTRY OF STATISTICS & PROGRAMME IMPLEMENTATION</h2>
                <p className="text-xs text-amber-400 font-sans font-semibold">National Sample Survey Office (NSSO) · Official Field Reference Notes</p>
                <p className="text-[11px] text-slate-500 font-sans">Document Ref: MoSPI/NSS/2026/MOD-01-NOTES</p>
              </div>

              <div className="space-y-4">
                <h4 className="font-sans font-bold text-white text-base">1. Sampling Frame Guidelines & Auxiliary Auditing</h4>
                <p>
                  Official survey inquiries conducted under the Collection of Statistics Act require strict adherence to standardized sampling frames.
                  Urban Sampling Frames utilize Urban Frame Survey (UFS) blocks classified into Commercial, Industrial, and Residential strata.
                  Field teams must verify auxiliary parameters prior to schedule canvassing.
                </p>

                <h4 className="font-sans font-bold text-white text-base">2. Probability Proportional to Size (PPS) Selection</h4>
                <p>
                  In multi-stage designs where Primary Sampling Units (PSUs) exhibit high size variation, PPS selection grants larger clusters inclusion probability proportional to size: \(\pi_i = n \cdot X_i / \sum X_i\).
                </p>

                <h4 className="font-sans font-bold text-white text-base">3. Non-Sampling Error Controls & Inspection Thresholds</h4>
                <p>
                  Supervisory field audits require conducting independent sub-sample re-interviews across a minimum 10% household sample. Relative Standard Error (RSE) metrics must be calculated for all key domain estimators before report release.
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 flex items-center justify-between bg-slate-900">
              <span className="text-xs text-slate-400">Page 1 of 12 · Official MoSPI Document</span>
              <Button
                onClick={() => setShowPdfModal(false)}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-4"
              >
                Close Preview
              </Button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
};
