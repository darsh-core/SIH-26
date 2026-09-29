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
  Video,
  ListOrdered,
  X
} from "lucide-react";
import { learningApi } from "../services/learningApi";
import { Button, Badge } from "../components/ui/Primitives";

// Sample Trainer-Generated MCQ Assessment Questions (Only shown after Module 3 / Final Module)
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
      <div className="fixed inset-0 z-50 bg-slate-50 flex flex-col items-center justify-center gap-4 text-slate-800">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-semibold text-slate-600">Launching iGOT Karmayogi Environment...</span>
      </div>
    );
  }

  if (courseError || !course) {
    return (
      <div className="fixed inset-0 z-50 bg-slate-50 flex flex-col items-center justify-center p-6 text-center text-slate-800 space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h2 className="text-xl font-bold">Learning Resource Unavailable</h2>
        <p className="text-sm text-slate-500 max-w-md">The requested course could not be retrieved.</p>
        <Button variant="outline" className="text-slate-800 bg-white hover:bg-slate-100" onClick={() => navigate("/dashboard")}>
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
    <div className="fixed inset-0 z-50 bg-slate-100 text-slate-800 flex flex-col font-sans overflow-hidden">
      
      {/* =========================================================
         TOP CONTROL HEADER (Light Theme with Centered Course Title & Back Button)
         ========================================================= */}
      <header className="h-16 bg-slate-900 text-white px-4 sm:px-6 flex items-center justify-between shrink-0 z-20 shadow-md">
        
        {/* Left: Back Button */}
        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-xs font-bold text-slate-200 hover:text-white bg-slate-800 hover:bg-slate-700 px-3.5 py-1.5 rounded-lg border border-slate-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back</span>
          </button>
        </div>

        {/* Center: ONLY the Title of the Course */}
        <div className="flex-1 text-center px-4 min-w-0">
          <div className="inline-flex items-center gap-2.5 max-w-xl mx-auto truncate">
            <span className="text-[10px] font-extrabold uppercase tracking-wider bg-blue-600 text-white px-2.5 py-0.5 rounded shrink-0">
              iGOT Karmayogi
            </span>
            <h1 className="text-sm sm:text-base font-extrabold text-white truncate">
              {course.title}
            </h1>
          </div>
        </div>

        {/* Right: Previous & Next Navigation Buttons */}
        <div className="flex items-center gap-2.5 shrink-0">
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
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 h-9 gap-1.5 shadow-xs"
          >
            <span className="hidden sm:inline">Next</span>
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </header>

      {/* =========================================================
         MAIN LIGHT THEME WORKSPACE: LEFT CURRICULUM PANEL + CENTER VIDEO & CONTENT
         ========================================================= */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* ---------------------------------------------------------
           LEFT SIDE PANEL: CURRICULUM CONTENTS LIST (Light Theme)
           --------------------------------------------------------- */}
        <aside className="w-80 sm:w-88 bg-white border-r border-slate-200 flex flex-col shrink-0 overflow-y-auto shadow-2xs">
          
          <div className="p-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <ListOrdered className="w-4 h-4 text-blue-600" />
              <span>Curriculum Outline</span>
            </h3>
            <span className="text-[11px] font-bold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
              {modules.length} Modules
            </span>
          </div>

          <div className="p-3 space-y-3 flex-1">
            {modules.map((m, mIdx) => {
              const isModSelected = mIdx === activeModuleIdx;
              const lessons = m.lessons || [];

              return (
                <div key={m.id} className="rounded-xl border border-slate-200 bg-slate-50/50 overflow-hidden transition-all shadow-2xs">
                  <button
                    onClick={() => {
                      setActiveModuleIdx(mIdx);
                      setActiveLessonIdx(0);
                    }}
                    className={`w-full p-3.5 text-left flex items-start justify-between gap-3 transition-colors ${
                      isModSelected 
                        ? "bg-blue-50/90 border-l-4 border-l-blue-600 text-blue-950 font-bold" 
                        : "hover:bg-slate-100/80 text-slate-700"
                    }`}
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-slate-400 uppercase">
                          Module {m.sequence_order}
                        </span>
                        <span className="text-[10px] text-slate-500">• {m.duration_minutes}m</span>
                      </div>
                      <h4 className="text-xs font-extrabold leading-tight truncate text-slate-900">{m.title}</h4>
                    </div>

                    <div className="shrink-0 mt-1">
                      {isModSelected ? (
                        <Play className="w-4 h-4 text-blue-600 fill-current" />
                      ) : (
                        <Circle className="w-4 h-4 text-slate-300" />
                      )}
                    </div>
                  </button>

                  {/* Sub-Lessons List */}
                  {isModSelected && lessons.length > 0 && (
                    <div className="bg-white border-t border-slate-200 p-2 space-y-1">
                      {lessons.map((l, lIdx) => {
                        const isLessSelected = lIdx === activeLessonIdx;
                        return (
                          <button
                            key={l.id}
                            onClick={() => setActiveLessonIdx(lIdx)}
                            className={`w-full p-2 rounded-lg text-left text-xs flex items-center justify-between transition-all ${
                              isLessSelected
                                ? "bg-blue-600 text-white font-bold shadow-2xs"
                                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                            }`}
                          >
                            <div className="flex items-center gap-2 truncate">
                              <Video className="w-3.5 h-3.5 shrink-0" />
                              <span className="truncate">{l.sequence_order}. {l.title}</span>
                            </div>
                            <span className="text-[10px] opacity-75 ml-2 shrink-0">{l.duration_minutes}m</span>
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
           CENTER AREA: VIDEO PLAYER + ABOUT/DESC/OUTCOMES + (ONLY MODULE 3: PDF & MCQ)
           --------------------------------------------------------- */}
        <main className="flex-1 bg-slate-100 overflow-y-auto p-4 sm:p-8 space-y-6">
          
          {/* 1. CENTER VIDEO PLAYER VIEWPORT (HD Video Player) */}
          <div className="bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden shadow-md">
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

          {/* 2. BELOW VIDEO: ABOUT, DESCRIPTION & OUTCOME FOR EACH MODULE (Light Theme) */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-6 shadow-2xs">
            
            {/* Header */}
            <div className="border-b border-slate-100 pb-4">
              <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 block">
                Module {currentModule?.sequence_order} of {modules.length} · Scope & Details
              </span>
              <h3 className="text-xl font-extrabold text-slate-900 mt-0.5">{currentModule?.title}</h3>
            </div>

            {/* About Section */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-600" />
                <span>About This Module</span>
              </h4>
              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal bg-slate-50 p-4 rounded-xl border border-slate-200">
                This module establishes core operational procedures for {currentModule?.title} under MoSPI standards. Officers learn to execute sampling inquiry schedules, audit auxiliary boundary changes, and maintain rigorous data quality controls.
              </p>
            </div>

            {/* Description Section */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-600" />
                <span>Operational Description</span>
              </h4>
              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal">
                {currentLesson?.content || currentModule?.description || "Official capacity building content."}
              </p>
            </div>

            {/* Learning Outcomes Section */}
            <div className="space-y-3 pt-2 border-t border-slate-100">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                <Award className="w-4 h-4 text-amber-500" />
                <span>Learning Outcomes Mastered</span>
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-700 font-medium">Design and validate sampling inquiry schedules in accordance with Collection of Statistics rules.</span>
                </div>
                <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-700 font-medium">Calculate Probability Proportional to Size (PPS) inclusion weights to minimize sample variance.</span>
                </div>
                <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-700 font-medium">Execute multi-tier supervisory inspections and independent household re-interviews.</span>
                </div>
                <div className="bg-slate-50 border border-slate-200 p-3.5 rounded-xl flex items-start gap-3">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="text-xs text-slate-700 font-medium">Compute Relative Standard Error (RSE) metrics to audit official report reliability thresholds.</span>
                </div>
              </div>
            </div>

            {/* Module Completion / Proceed Button for Module 1 & Module 2 */}
            {!isLastModule && (
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between gap-4">
                <span className="text-xs text-slate-500 font-medium">
                  Completed lessons in Module {activeModuleIdx + 1}? Proceed to the next module.
                </span>
                <Button
                  onClick={() => {
                    if (currentModule) {
                      completeModuleMutation.mutate(currentModule.id);
                    } else {
                      setActiveModuleIdx(prev => prev + 1);
                      setActiveLessonIdx(0);
                    }
                  }}
                  disabled={completeModuleMutation.isPending}
                  className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-5 py-2.5 rounded-lg shadow-2xs flex items-center gap-2"
                >
                  <span>Complete Module {activeModuleIdx + 1} & Proceed to Module {activeModuleIdx + 2}</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>
            )}

          </div>

          {/* 3. ONLY ON MODULE 3 (FINAL MODULE): PDF NOTES & TRAINER MCQ ASSESSMENT */}
          {isLastModule && (
            <div className="bg-white rounded-2xl border border-blue-200 p-6 sm:p-8 space-y-8 shadow-sm">
              
              <div className="flex items-center justify-between border-b border-slate-200 pb-4">
                <div>
                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-blue-600 block">
                    Final Module 3 Evaluation & Course Completion
                  </span>
                  <h3 className="text-xl font-extrabold text-slate-900 mt-0.5">Module Notes & Trainer-Generated Assessment</h3>
                </div>
                <Badge className="bg-amber-400 text-amber-950 text-xs font-extrabold px-3 py-1">
                  Module 3 Final Exam
                </Badge>
              </div>

              {/* A. NOTES AS PDF CARD */}
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-start gap-3.5">
                    <div className="w-12 h-12 rounded-xl bg-rose-100 border border-rose-200 flex items-center justify-center shrink-0 text-rose-600">
                      <FileText className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">Official MoSPI Module Reference Notes & Guidelines.pdf</h4>
                      <p className="text-xs text-slate-500 mt-0.5">Comprehensive module summary notes, formulas, and field protocols · 2.4 MB</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setShowPdfModal(true)}
                      className="bg-white hover:bg-slate-100 text-slate-700 border-slate-300 text-xs font-bold gap-1.5"
                    >
                      <Eye className="w-4 h-4 text-blue-600" />
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
              <div className="space-y-6 pt-4 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                      <HelpCircle className="w-5 h-5 text-amber-500" />
                      <span>Trainer-Generated MCQ Assessment</span>
                    </h4>
                    <p className="text-xs text-slate-500 mt-1">
                      Complete these trainer-authored questions to verify your competency advancement for <strong className="text-slate-800">Sampling Methodology</strong>.
                    </p>
                  </div>

                  {assessmentSubmitted && (
                    <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                      assessmentScore >= 60 
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200" 
                        : "bg-rose-50 text-rose-700 border-rose-200"
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
                      <div key={q.id} className="bg-slate-50 border border-slate-200 rounded-xl p-5 space-y-4">
                        <div className="flex items-start gap-3">
                          <span className="w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center shrink-0">
                            {qIdx + 1}
                          </span>
                          <h5 className="text-sm font-bold text-slate-900 leading-relaxed">{q.question}</h5>
                        </div>

                        {/* Options */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pl-9">
                          {q.options.map((opt, optIdx) => {
                            const isSelected = selectedOpt === optIdx;
                            let optionStyle = "bg-white border-slate-200 text-slate-700 hover:bg-slate-100 hover:border-slate-300";

                            if (assessmentSubmitted) {
                              if (optIdx === q.correctIdx) {
                                optionStyle = "bg-emerald-50 border-emerald-400 text-emerald-900 font-bold";
                              } else if (isSelected && !isCorrect) {
                                optionStyle = "bg-rose-50 border-rose-400 text-rose-900 font-bold";
                              }
                            } else if (isSelected) {
                              optionStyle = "bg-blue-50 border-blue-500 text-blue-900 font-bold";
                            }

                            return (
                              <button
                                key={optIdx}
                                disabled={assessmentSubmitted}
                                onClick={() => handleOptionSelect(q.id, optIdx)}
                                className={`p-3 rounded-lg border text-xs text-left transition-all flex items-center justify-between ${optionStyle}`}
                              >
                                <span>{String.fromCharCode(65 + optIdx)}. {opt}</span>
                                {isSelected && !assessmentSubmitted && <Check className="w-4 h-4 text-blue-600" />}
                                {assessmentSubmitted && optIdx === q.correctIdx && <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                              </button>
                            );
                          })}
                        </div>

                        {/* Explanation box after submit */}
                        {assessmentSubmitted && (
                          <div className="ml-9 p-3 rounded-lg bg-white border border-slate-200 text-xs text-slate-600 space-y-1">
                            <strong className="text-amber-600 block font-semibold">Trainer Explanation:</strong>
                            <p>{q.explanation}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>

                {/* Submit Assessment Action */}
                <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                  <p className="text-xs text-slate-500">
                    Passing criteria: 60% or higher required to update Competency Twin.
                  </p>

                  {!assessmentSubmitted ? (
                    <Button
                      onClick={handleSubmitAssessment}
                      disabled={Object.keys(selectedAnswers).length < TRAINER_MCQ_QUESTIONS.length}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-6 py-2.5 rounded-lg shadow-xs"
                    >
                      <span>Submit Assessment & Verify Competency</span>
                    </Button>
                  ) : (
                    <Button
                      onClick={() => completeCourseMutation.mutate()}
                      className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs px-6 py-2.5 rounded-lg shadow-xs gap-2"
                    >
                      <span>Complete Course & Update Competency Twin</span>
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                  )}
                </div>

              </div>

            </div>
          )}

        </main>
      </div>

      {/* =========================================================
         PDF PREVIEW MODAL
         ========================================================= */}
      {showPdfModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6">
          <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden shadow-2xl">
            
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-3">
                <FileText className="w-5 h-5 text-rose-600" />
                <h3 className="text-sm font-bold text-slate-900">Official MoSPI Module Reference Notes & Guidelines.pdf</h3>
              </div>
              <button
                onClick={() => setShowPdfModal(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body - PDF Document Simulation Viewer */}
            <div className="p-6 overflow-y-auto space-y-6 text-slate-700 font-serif text-sm bg-slate-50 leading-relaxed">
              <div className="text-center border-b border-slate-200 pb-4 space-y-1 font-sans">
                <h2 className="text-lg font-extrabold text-slate-900">MINISTRY OF STATISTICS & PROGRAMME IMPLEMENTATION</h2>
                <p className="text-xs text-amber-600 font-semibold">National Sample Survey Office (NSSO) · Official Field Reference Notes</p>
                <p className="text-[11px] text-slate-400">Document Ref: MoSPI/NSS/2026/MOD-03-NOTES</p>
              </div>

              <div className="space-y-4">
                <h4 className="font-sans font-bold text-slate-900 text-base">1. Sampling Frame Guidelines & Auxiliary Auditing</h4>
                <p>
                  Official survey inquiries conducted under the Collection of Statistics Act require strict adherence to standardized sampling frames.
                  Urban Sampling Frames utilize Urban Frame Survey (UFS) blocks classified into Commercial, Industrial, and Residential strata.
                  Field teams must verify auxiliary parameters prior to schedule canvassing.
                </p>

                <h4 className="font-sans font-bold text-slate-900 text-base">2. Probability Proportional to Size (PPS) Selection</h4>
                <p>
                  In multi-stage designs where Primary Sampling Units (PSUs) exhibit high size variation, PPS selection grants larger clusters inclusion probability proportional to size: \(\pi_i = n \cdot X_i / \sum X_i\).
                </p>

                <h4 className="font-sans font-bold text-slate-900 text-base">3. Non-Sampling Error Controls & Inspection Thresholds</h4>
                <p>
                  Supervisory field audits require conducting independent sub-sample re-interviews across a minimum 10% household sample. Relative Standard Error (RSE) metrics must be calculated for all key domain estimators before report release.
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-200 flex items-center justify-between bg-slate-50">
              <span className="text-xs text-slate-500 font-sans">Page 1 of 12 · Official MoSPI Document</span>
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
