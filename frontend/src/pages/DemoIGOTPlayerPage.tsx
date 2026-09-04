import React, { useState, useEffect } from "react";
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
  ExternalLink,
  Layers,
  RotateCcw
} from "lucide-react";
import { learningApi, NormalizedLearningResource, LearningProgressDetail } from "../services/learningApi";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from "../components/ui/Primitives";

export const DemoIGOTPlayerPage: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [activeModuleIdx, setActiveModuleIdx] = useState<number>(0);
  const [activeLessonIdx, setActiveLessonIdx] = useState<number>(0);

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

  // 2. Fetch or initialize Progress
  const {
    data: progress,
    isLoading: progressLoading,
    refetch: refetchProgress,
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
      // Advance to next module if available
      if (course && activeModuleIdx < course.modules.length - 1) {
        setActiveModuleIdx(prev => prev + 1);
        setActiveLessonIdx(0);
      }
    },
  });

  // Complete entire course mutation
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
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-gov-blue-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-sm font-semibold text-slate-500">Launching iGOT Karmayogi Learning Environment...</span>
      </div>
    );
  }

  if (courseError || !course) {
    return (
      <div className="max-w-xl mx-auto text-center py-16 space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-900">Learning Resource Unavailable</h2>
        <p className="text-sm text-slate-500">The requested learning resource could not be loaded.</p>
        <Button variant="outline" onClick={() => navigate("/dashboard")}>
          Return to SANKHYAI Dashboard
        </Button>
      </div>
    );
  }

  const modules = course.modules || [];
  const currentModule = modules[activeModuleIdx] || modules[0];
  const currentLessons = currentModule?.lessons || [];
  const currentLesson = currentLessons[activeLessonIdx] || currentLessons[0];

  // Helper to get module status from backend progress
  const getModuleStatus = (modId: string) => {
    const mp = progress?.modules?.find(m => m.module_id === modId);
    return mp?.status || "NOT_STARTED";
  };

  const currentModStatus = currentModule ? getModuleStatus(currentModule.id) : "NOT_STARTED";
  const isCourseCompleted = progress?.status === "COMPLETED" || (progress?.progress_percentage ?? 0) >= 100;

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col -m-6 md:-m-8">
      {/* 1. Official iGOT Government Header */}
      <header className="bg-gov-blue-900 text-white px-6 py-4 border-b border-gov-blue-800 shadow-md flex flex-wrap items-center justify-between gap-4 sticky top-0 z-30">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center text-gov-blue-900 font-extrabold shadow-inner shrink-0">
            <BookOpen className="w-5 h-5 text-gov-blue-600" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-bold tracking-tight text-white">iGOT Karmayogi</span>
              <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-amber-400 text-amber-950 tracking-wider">
                Demo Integration
              </span>
            </div>
            <p className="text-xs text-slate-300">National Programme for Civil Services Capacity Building (NPCSCB)</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:block text-right">
            <span className="text-xs font-semibold text-slate-200 block truncate max-w-xs">{course.title}</span>
            <span className="text-[10px] text-slate-400">{course.difficulty} · {course.duration_minutes} Mins</span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => navigate("/dashboard")}
            className="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs h-8 gap-1.5"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Exit to SANKHYAI</span>
          </Button>
        </div>
      </header>

      {/* 2. Top Progress Tracker Strip */}
      <div className="bg-white border-b border-slate-200 px-6 py-3.5 shadow-2xs">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-4">
            <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
              Course Progress
            </span>
            <span className="font-bold text-gov-blue-600">
              {progress?.progress_percentage?.toFixed(1) || 0}%
            </span>
            <span className="text-slate-400">|</span>
            <span className="text-slate-600 font-medium">
              {progress?.completed_modules || 0} of {modules.length} Modules Completed
            </span>
          </div>

          <div className="w-full sm:w-64">
            <Progress 
              value={progress?.progress_percentage || 0} 
              className="h-2" 
              colorClassName={isCourseCompleted ? "bg-emerald-500" : "bg-gov-blue-500"} 
            />
          </div>
        </div>
      </div>

      {/* 3. Main Workspace Container */}
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* LEFT COLUMN: Modules & Lessons Navigation (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50 border-b border-slate-200 p-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-gov-blue-600" />
                  <span>Curriculum Outline</span>
                </CardTitle>
                <Badge variant={isCourseCompleted ? "success" : "default"} className="text-[10px]">
                  {isCourseCompleted ? "COMPLETED" : "IN PROGRESS"}
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="p-0 divide-y divide-slate-100 max-h-[calc(100vh-280px)] overflow-y-auto">
              {modules.map((m, mIdx) => {
                const status = getModuleStatus(m.id);
                const isSelected = mIdx === activeModuleIdx;

                return (
                  <div key={m.id} className="transition-colors">
                    <button
                      onClick={() => {
                        setActiveModuleIdx(mIdx);
                        setActiveLessonIdx(0);
                      }}
                      className={`w-full text-left p-3.5 flex items-start gap-3 transition-all ${
                        isSelected 
                          ? "bg-gov-blue-50/70 border-l-4 border-l-gov-blue-600" 
                          : "hover:bg-slate-50 border-l-4 border-l-transparent"
                      }`}
                    >
                      <div className="mt-0.5 shrink-0">
                        {status === "COMPLETED" ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : isSelected ? (
                          <Play className="w-4 h-4 text-gov-blue-600 fill-gov-blue-600" />
                        ) : (
                          <Circle className="w-4 h-4 text-slate-300" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-[10px] font-bold text-slate-400 uppercase">
                            Module {m.sequence_order}
                          </span>
                          <span className="text-[10px] text-slate-400">{m.duration_minutes}m</span>
                        </div>
                        <h4 className={`text-xs font-bold leading-snug truncate ${
                          isSelected ? "text-gov-blue-900 font-extrabold" : "text-slate-800"
                        }`}>
                          {m.title}
                        </h4>
                      </div>
                    </button>

                    {/* Sub-lessons list if selected */}
                    {isSelected && m.lessons && m.lessons.length > 0 && (
                      <div className="bg-slate-50/60 pl-9 pr-3 py-1.5 space-y-1">
                        {m.lessons.map((l, lIdx) => (
                          <button
                            key={l.id}
                            onClick={() => setActiveLessonIdx(lIdx)}
                            className={`w-full text-left py-1.5 px-2 rounded text-[11px] flex items-center justify-between ${
                              lIdx === activeLessonIdx 
                                ? "bg-white font-bold text-gov-blue-700 shadow-2xs border border-slate-200" 
                                : "text-slate-600 hover:text-slate-900"
                            }`}
                          >
                            <span className="truncate">{l.sequence_order}. {l.title}</span>
                            <span className="text-[9px] text-slate-400 ml-1 shrink-0">{l.duration_minutes}m</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Competency Mapping Card */}
          <Card className="border-slate-200 shadow-2xs bg-white p-4 space-y-2.5">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-gov-gold" />
              <span>MoSPI Competencies Addressed</span>
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {course.competencies.map(c => (
                <span key={c.code} className="text-[10px] font-bold text-gov-blue-700 bg-gov-blue-50 px-2 py-0.5 rounded border border-gov-blue-200">
                  {c.name} · Level {c.target_level}
                </span>
              ))}
            </div>
          </Card>
        </div>

        {/* RIGHT COLUMN: Interactive Lesson Player & Completion Screen (8 cols) */}
        <div className="lg:col-span-8">
          {isCourseCompleted ? (
            /* ==========================================
               OFFICIAL COMPLETION STATE BANNER & ACTION
               ========================================== */
            <Card className="border-emerald-200 bg-white shadow-md overflow-hidden text-center">
              <div className="bg-emerald-600 text-white py-10 px-6 space-y-3">
                <div className="w-16 h-16 rounded-full bg-white/20 border-2 border-white flex items-center justify-center mx-auto shadow-inner">
                  <ShieldCheck className="w-9 h-9 text-white" />
                </div>
                <h2 className="text-2xl font-extrabold tracking-tight">Course Completed Successfully!</h2>
                <p className="text-emerald-100 text-sm max-w-lg mx-auto leading-relaxed">
                  Congratulations! You have completed all learning modules and practical exercises for <strong>{course.title}</strong>.
                </p>
                <div className="inline-flex items-center gap-2 bg-emerald-700/60 px-3 py-1 rounded-full text-xs font-semibold text-emerald-100">
                  <span>Provider: iGOT Karmayogi — Demo Integration</span>
                  <span>•</span>
                  <span>Completion Status: VERIFIED</span>
                </div>
              </div>

              <CardContent className="p-8 space-y-6">
                <div className="bg-slate-50 p-5 rounded-xl border border-slate-200 max-w-md mx-auto space-y-3 text-left">
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                    Competency Intelligence Update
                  </span>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Completing this learning course updates your training history. To officially verify your skill advancement and update your <strong>Competency Twin</strong>, proceed to the post-learning reassessment.
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                  <Button
                    size="lg"
                    onClick={() => navigate("/progress")}
                    className="bg-gov-blue-600 hover:bg-gov-blue-700 text-white font-bold text-sm px-6 h-11 gap-2 shadow-sm"
                  >
                    <span>View Competency Progress & Reassess</span>
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                  <Button
                    size="lg"
                    variant="outline"
                    onClick={() => navigate("/dashboard")}
                    className="text-xs h-11"
                  >
                    Return to Dashboard
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            /* ==========================================
               INTERACTIVE LESSON CONTENT VIEWER
               ========================================== */
            <Card className="border-slate-200 bg-white shadow-sm flex flex-col justify-between min-h-[560px]">
              <div>
                <CardHeader className="bg-slate-50/70 border-b border-slate-200 p-5 flex flex-row items-center justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-gov-blue-600 uppercase tracking-wider block">
                      Module {currentModule?.sequence_order} of {modules.length} · {currentModule?.title}
                    </span>
                    <h2 className="text-lg font-bold text-slate-900 mt-0.5">
                      {currentLesson?.title || "Lesson Overview"}
                    </h2>
                  </div>

                  <div className="flex items-center gap-2">
                    {currentModStatus === "COMPLETED" ? (
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Completed
                      </span>
                    ) : (
                      <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full border border-slate-200 flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {currentLesson?.duration_minutes || 15} mins
                      </span>
                    )}
                  </div>
                </CardHeader>

                <CardContent className="p-6 md:p-8 space-y-6">
                  {/* Lesson Content Body */}
                  <div className="prose prose-slate max-w-none text-slate-700 text-sm leading-relaxed space-y-4">
                    <p className="text-base text-slate-800 font-medium leading-relaxed bg-blue-50/50 p-4 rounded-xl border border-blue-100">
                      {currentLesson?.content || currentModule?.description || "Welcome to this official learning module."}
                    </p>

                    <div className="space-y-3 pt-2">
                      <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                        Key MoSPI Learning Takeaways:
                      </h4>
                      <ul className="space-y-2 text-xs text-slate-600 pl-4 list-disc">
                        <li>Strict adherence to standardized Ministry procedures and sampling frameworks.</li>
                        <li>Minimizing both sampling variance and non-sampling field collection errors.</li>
                        <li>Verifying metadata integrity in accordance with national statistical data governance rules.</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </div>

              {/* Action Footer */}
              <div className="p-5 border-t border-slate-200 bg-slate-50/70 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={activeLessonIdx === 0 && activeModuleIdx === 0}
                    onClick={() => {
                      if (activeLessonIdx > 0) {
                        setActiveLessonIdx(prev => prev - 1);
                      } else if (activeModuleIdx > 0) {
                        setActiveModuleIdx(prev => prev - 1);
                        setActiveLessonIdx(0);
                      }
                    }}
                    className="text-xs h-9 gap-1"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                    <span>Previous</span>
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    disabled={activeLessonIdx >= currentLessons.length - 1}
                    onClick={() => setActiveLessonIdx(prev => prev + 1)}
                    className="text-xs h-9 gap-1"
                  >
                    <span>Next Lesson</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </Button>
                </div>

                <div className="flex items-center gap-2">
                  {currentModule && currentModStatus !== "COMPLETED" ? (
                    <Button
                      size="sm"
                      onClick={() => completeModuleMutation.mutate(currentModule.id)}
                      disabled={completeModuleMutation.isPending}
                      className="bg-gov-blue-600 hover:bg-gov-blue-700 text-white font-bold text-xs h-9 px-4 gap-1.5 shadow-2xs"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>
                        {completeModuleMutation.isPending ? "Marking Complete..." : "Mark Module Complete & Continue"}
                      </span>
                    </Button>
                  ) : activeModuleIdx < modules.length - 1 ? (
                    <Button
                      size="sm"
                      onClick={() => {
                        setActiveModuleIdx(prev => prev + 1);
                        setActiveLessonIdx(0);
                      }}
                      className="bg-gov-blue-600 hover:bg-gov-blue-700 text-white font-bold text-xs h-9 px-4 gap-1"
                    >
                      <span>Proceed to Next Module</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      onClick={() => completeCourseMutation.mutate()}
                      disabled={completeCourseMutation.isPending}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs h-9 px-4 gap-1.5 shadow-sm"
                    >
                      <ShieldCheck className="w-4 h-4" />
                      <span>{completeCourseMutation.isPending ? "Finalizing..." : "Complete Course & Verify"}</span>
                    </Button>
                  )}
                </div>
              </div>
            </Card>
          )}
        </div>

      </div>
    </div>
  );
};
