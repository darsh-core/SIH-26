import React, { useState } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { 
  RotateCw, 
  Plus, 
  Minus,
  Check, 
  Search, 
  Info, 
  BookOpen,
  ChevronDown,
  ChevronUp,
  Play,
  Sparkles,
  Brain,
  FileText,
  Video,
  Award,
  Image as ImageIcon
} from "lucide-react"

import { useAuthStore } from "../store/authStore"
import { recommendationApi } from "../services/recommendationApi"
import { learningPlanApi } from "../services/learningPlanApi"
import { learningApi } from "../services/learningApi"
import { Card, CardContent, Badge, Button, Progress } from "../components/ui/Primitives"
import { formatDuration } from "../lib/utils"

// Course banner image mapping based on course codes / topics
const COURSE_IMAGES: Record<string, string> = {
  "IGOT_COMP_STATS_01": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=600&q=80",
  "IGOT_COMP_STATS_03": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=600&q=80",
  "IGOT_COMP_STATS_05": "https://images.unsplash.com/photo-1504868584819-f8e8b4b6d7e3?auto=format&fit=crop&w=600&q=80",
  "IGOT_COMP_TECH_01": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80",
  "DEFAULT": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=600&q=80"
}

// Sample curriculum content modules for the "Content" tab
const COURSE_CURRICULUM_DATA: Record<string, Array<{ id: string; title: string; duration: string; itemsCount: number; lessons: string[] }>> = {
  "default": [
    {
      id: "mod-1",
      title: "1. Introduction to Official Survey & Data Standards",
      duration: "2m",
      itemsCount: 2,
      lessons: [
        "Overview of MoSPI National Framework & Guidelines",
        "Understanding Target Population vs Study Population"
      ]
    },
    {
      id: "mod-2",
      title: "2. Sampling Frame Construction & Validation",
      duration: "2m",
      itemsCount: 2,
      lessons: [
        "Urban Frame Survey (UFS) Blocks & Rural Census Directories",
        "Auxiliary Data Auditing & Stratification Rules"
      ]
    },
    {
      id: "mod-3",
      title: "3. Questionnaire Schedule Design & Pre-testing",
      duration: "2m",
      itemsCount: 2,
      lessons: [
        "Standardized Code Lists (NIC-2008 & NCO-2015)",
        "Cognitive Interviewing & Field Pilot Verification"
      ]
    },
    {
      id: "mod-4",
      title: "4. Fieldwork Supervision & Error Control",
      duration: "2m",
      itemsCount: 2,
      lessons: [
        "Multi-tier Inspection Protocols by Statistical Officers",
        "Non-Response Imputation & Hot-deck Weighting"
      ]
    },
    {
      id: "mod-5",
      title: "5. Planning & Execution of Field Audits",
      duration: "2m",
      itemsCount: 2,
      lessons: [
        "Concurrent Sub-sampling & Field Inspection Routines",
        "Relative Standard Error (RSE) Threshold Calculations"
      ]
    },
    {
      id: "mod-6",
      title: "6. Take Home Summary & Quality Introspection",
      duration: "2m",
      itemsCount: 2,
      lessons: [
        "Six Dimensions of National Statistical Quality Framework",
        "Final Assessment & iGOT Karmayogi Certification"
      ]
    }
  ]
}

export const RecommendationsPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [searchParams] = useSearchParams();
  const userId = user?.id || "";

  // Get active competency filter from URL query if present (e.g. ?competency=STAT_SAMPLING)
  const defaultCompetency = searchParams.get("competency") || "";

  // State filters
  const [providerFilter, setProviderFilter] = useState<"ALL" | "IGOT" | "NSSTA">("ALL");
  const [priorityFilter, setPriorityFilter] = useState<"ALL" | "HIGH">("ALL");
  const [competencyFilter, setCompetencyFilter] = useState<string>(defaultCompetency);
  
  // Expandable state for AI score breakdown
  const [expandedExplanation, setExpandedExplanation] = useState<Record<string, boolean>>({});
  
  // Course Details Expansion State (About & Content tabs)
  const [expandedCourseId, setExpandedCourseId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Record<string, "about" | "content">>({});
  const [showFullDesc, setShowFullDesc] = useState<Record<string, boolean>>({});
  const [showFullOutcomes, setShowFullOutcomes] = useState<Record<string, boolean>>({});
  const [expandedModules, setExpandedModules] = useState<Record<string, boolean>>({});

  // 1. Fetch recommendations
  const { 
    data, 
    isLoading, 
    isFetching,
    error,
    refetch 
  } = useQuery({
    queryKey: ["recommendations", userId, providerFilter, priorityFilter, competencyFilter],
    queryFn: () => {
      const filters: any = { debug: true, limit: 20 };
      if (providerFilter !== "ALL") filters.provider = providerFilter;
      if (priorityFilter !== "ALL") filters.priority = priorityFilter;
      if (competencyFilter) filters.competency = competencyFilter;
      return recommendationApi.getRecommendations(userId, filters);
    },
    enabled: !!userId
  });

  // 2. Refresh Recommendations mutation
  const refreshMutation = useMutation({
    mutationFn: () => recommendationApi.refreshRecommendations(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["competency-gaps"] });
      queryClient.invalidateQueries({ queryKey: ["recommendations-preview"] });
    }
  });

  // 3. Learning Plan generation mutation
  const addToPlanMutation = useMutation({
    mutationFn: () => learningPlanApi.generateLearningPlan(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["learning-plans"] });
      navigate("/learning-plan");
    }
  });

  const [launchingId, setLaunchingId] = useState<string | null>(null);

  const handleLaunch = async (resourceId: string) => {
    try {
      setLaunchingId(resourceId);
      const res = await learningApi.launchCourse(resourceId);
      if (res.launch_url.startsWith("/")) {
        navigate(res.launch_url);
      } else {
        window.open(res.launch_url, "_blank");
      }
    } catch (err) {
      console.error("Failed to launch course:", err);
    } finally {
      setLaunchingId(null);
    }
  };

  const toggleExplanation = (resourceId: string) => {
    setExpandedExplanation(prev => ({
      ...prev,
      [resourceId]: !prev[resourceId]
    }));
  };

  const toggleCourseDetails = (resourceId: string) => {
    setExpandedCourseId(prev => prev === resourceId ? null : resourceId);
    if (!activeTab[resourceId]) {
      setActiveTab(prev => ({ ...prev, [resourceId]: "about" }));
    }
  };

  const setCourseTab = (resourceId: string, tab: "about" | "content") => {
    setActiveTab(prev => ({ ...prev, [resourceId]: tab }));
  };

  const toggleModule = (modId: string) => {
    setExpandedModules(prev => ({ ...prev, [modId]: !prev[modId] }));
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <svg className="animate-spin h-10 w-10 text-gov-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span className="text-sm font-semibold text-slate-500">Retrieving personalized matching catalog...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-bold text-slate-900">Unable to load recommendations.</h3>
        <p className="text-sm text-slate-500 mt-2">Try logging in again or verify the backend server connection.</p>
        <Button variant="outline" className="mt-4" onClick={() => refetch()}>Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Executive Full-Bleed Hero Banner (Inspired by iGOT Karmayogi Hero) */}
      <div className="bg-gradient-to-r from-slate-900 via-blue-950 to-slate-900 text-white rounded-2xl p-6 sm:p-8 shadow-md border border-slate-800/80 relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-blue-600/30 text-blue-300 border border-blue-500/40">
                Competency Gap Remediation
              </span>
              <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-amber-400/20 text-amber-300 border border-amber-400/30">
                iGOT & NSSTA Integrated
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Personalized Learning Recommendations
            </h1>
            <p className="text-xs sm:text-sm text-slate-300 font-medium">
              Bridging Target Competency Deficits for Role: <strong className="text-amber-300 font-bold">{data.role}</strong>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <Button 
              variant="outline" 
              onClick={() => refreshMutation.mutate()} 
              isLoading={refreshMutation.isPending || isFetching}
              className="bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs h-10 px-4 gap-2 backdrop-blur-xs"
            >
              <RotateCw className="h-3.5 w-3.5" />
              <span>Refresh Gap Catalog</span>
            </Button>
            <Button 
              onClick={() => addToPlanMutation.mutate()} 
              isLoading={addToPlanMutation.isPending}
              className="bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold text-xs h-10 px-4 gap-2 shadow-xs transition-colors"
            >
              <Plus className="h-4 w-4 text-slate-950" />
              <span>Add all to Learning Journey</span>
            </Button>
          </div>
        </div>
      </div>

      {/* 2. Real-time AI Gap & Recommendation Assistant Banner */}
      <div className="bg-slate-900 rounded-xl p-5 text-white shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-slate-800">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center shrink-0">
            <Brain className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>Real-Time AI Skill Gap & Recommendation Explainer</span>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-semibold">Live Ollama 3.2</span>
            </h3>
            <p className="text-xs text-slate-400 mt-0.5 font-normal">
              Ask real-time questions, analyze why specific courses were selected for your role, and receive personalized learning guidance.
            </p>
          </div>
        </div>
        <Button
          onClick={() => {
            const event = new CustomEvent("open-copilot", {
              detail: {
                query: "Analyze my current skill gaps, role readiness, and explain why you recommend each course for my cadre."
              }
            });
            window.dispatchEvent(event);
          }}
          className="bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs py-2 px-4 rounded-lg shadow-2xs flex items-center gap-2 shrink-0 cursor-pointer"
        >
          <Sparkles className="w-4 h-4 text-blue-600" />
          <span>Ask AI to Analyze My Gaps</span>
        </Button>
      </div>

      {/* 3. Filter Controls Block */}
      <Card className="p-4 bg-slate-50 border-slate-200/90">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Provider:</span>
            <div className="flex bg-white border border-slate-200 rounded-lg p-1 shadow-2xs">
              <button 
                onClick={() => setProviderFilter("ALL")} 
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${providerFilter === "ALL" ? "bg-blue-600 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
              >
                All
              </button>
              <button 
                onClick={() => setProviderFilter("IGOT")} 
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${providerFilter === "IGOT" ? "bg-blue-600 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
              >
                iGOT
              </button>
              <button 
                onClick={() => setPriorityFilter("ALL")} 
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${providerFilter === "NSSTA" ? "bg-blue-600 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
              >
                NSSTA
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Priority:</span>
            <div className="flex bg-white border border-slate-200 rounded-lg p-1 shadow-2xs">
              <button 
                onClick={() => setPriorityFilter("ALL")} 
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${priorityFilter === "ALL" ? "bg-blue-600 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
              >
                All Gaps
              </button>
              <button 
                onClick={() => setPriorityFilter("HIGH")} 
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${priorityFilter === "HIGH" ? "bg-blue-600 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
              >
                High Priority Gaps Only
              </button>
            </div>
          </div>

          {/* Competency Filter search block */}
          <div className="relative shrink-0 w-full sm:w-64">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <input
              type="text"
              placeholder="Filter by competency code..."
              value={competencyFilter}
              onChange={(e) => setCompetencyFilter(e.target.value)}
              className="block w-full pl-9 pr-3 py-1.5 border border-slate-200 bg-white rounded-lg text-xs placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-blue-600 text-slate-800"
            />
            {competencyFilter && (
              <button 
                onClick={() => setCompetencyFilter("")}
                className="absolute right-2 top-1.5 p-0.5 text-slate-400 hover:text-slate-600 text-xs"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </Card>

      {/* 4. Course Cards Grid View */}
      {data.recommendations.length === 0 ? (
        <div className="text-center py-12 bg-white border border-slate-200 rounded-xl p-6">
          <BookOpen className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-base font-bold text-slate-800">No competency gaps or matching recommendations found.</h3>
          <p className="text-xs text-slate-400 mt-2">Adjust your filters, check active gaps, or reload the gap catalog.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {data.recommendations.map(r => {
            const gap = r.target_competencies[0];
            const isExplanationExpanded = !!expandedExplanation[r.resource_id];
            const isDetailsExpanded = expandedCourseId === r.resource_id;
            const currentTab = activeTab[r.resource_id] || "about";
            const imageUrl = COURSE_IMAGES[r.resource_id] || COURSE_IMAGES["DEFAULT"];

            return (
              <Card key={r.resource_id} className="relative hover:border-slate-300 transition-all border-l-4 border-l-blue-600 flex flex-col bg-white overflow-hidden shadow-xs">
                
                {/* Main Card Body (Split: Left Text & Metadata / Right Course Image Slot) */}
                <CardContent className="p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
                    
                    {/* LEFT COLUMN (Text Content, Metadata, Gap Info, Actions) */}
                    <div className="md:col-span-8 space-y-4 min-w-0">
                      
                      {/* Title & Badges */}
                      <div className="space-y-1.5">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                            {r.provider}
                          </span>
                          <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                            {r.resource_type}
                          </span>
                          <span className="text-xs text-slate-500 font-medium">
                            {r.difficulty} · {formatDuration(r.estimated_duration_minutes)}
                          </span>
                        </div>
                        <h3 className="text-xl font-extrabold text-slate-900 leading-snug">{r.title}</h3>
                      </div>

                      {/* Course Launch Action Row (Positioned ABOVE Duration Bar) */}
                      <div className="flex flex-wrap items-center justify-between gap-3 py-1">
                        <div className="flex items-center gap-3">
                          <Button
                            size="sm"
                            onClick={() => handleLaunch(r.resource_id)}
                            disabled={launchingId === r.resource_id}
                            className="bg-gov-blue-600 hover:bg-gov-blue-700 text-white font-bold flex items-center gap-2 shadow-sm text-xs px-4 py-2 rounded-lg"
                          >
                            {launchingId === r.resource_id ? (
                              <>
                                <RotateCw className="w-3.5 h-3.5 animate-spin" />
                                Launching Player...
                              </>
                            ) : (
                              <>
                                <Play className="w-3.5 h-3.5 fill-current" />
                                Start Course on iGOT
                              </>
                            )}
                          </Button>

                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => toggleCourseDetails(r.resource_id)}
                            className="text-xs font-bold text-blue-700 border-slate-300 hover:bg-blue-50 flex items-center gap-1.5 px-3 py-2 rounded-lg"
                          >
                            <BookOpen className="w-3.5 h-3.5 text-blue-600" />
                            <span>{isDetailsExpanded ? "Hide Course Details" : "View About & Content"}</span>
                            {isDetailsExpanded ? <ChevronUp className="w-3.5 h-3.5 ml-1" /> : <ChevronDown className="w-3.5 h-3.5 ml-1" />}
                          </Button>
                        </div>

                        <span className="text-[11px] text-slate-400 font-medium">
                          {r.provider === "iGOT" ? "Karmayogi Bharat" : "NSSTA Training"}
                        </span>
                      </div>

                      {/* iGOT Metadata Grid / Duration Bar (Unboxed & Increased Font Size) */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-2 text-slate-800">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                            <BookOpen className="w-4 h-4 text-blue-600" />
                          </div>
                          <div>
                            <span className="text-xs text-slate-500 block font-medium">Duration</span>
                            <span className="text-sm font-bold text-slate-900">{formatDuration(r.estimated_duration_minutes)}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                            <Info className="w-4 h-4 text-blue-600" />
                          </div>
                          <div>
                            <span className="text-xs text-slate-500 block font-medium">Provider</span>
                            <span className="text-sm font-bold text-slate-900">{r.provider === "iGOT" ? "Karmayogi Bharat" : "NSSTA Greater Noida"}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0">
                            <Check className="w-4 h-4 text-emerald-600" />
                          </div>
                          <div>
                            <span className="text-xs text-slate-500 block font-medium">Target Level</span>
                            <span className="text-sm font-bold text-slate-900">Level {r.difficulty === "Advanced" ? "4.0" : "3.0"}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center shrink-0">
                            <Sparkles className="w-4 h-4 text-amber-500" />
                          </div>
                          <div>
                            <span className="text-xs text-slate-500 block font-medium">Licensing</span>
                            <span className="text-sm font-bold text-slate-900">Free · CC BY 4.0</span>
                          </div>
                        </div>
                      </div>

                      {/* Competency Gap Details (Unboxed & Increased Font Size) */}
                      {gap && (
                        <div className="py-2.5 space-y-2.5 text-sm border-t border-slate-100">
                          <div className="flex flex-wrap items-center justify-between gap-3">
                            <div className="flex items-center gap-2.5">
                              <span className="text-slate-600 font-semibold text-sm sm:text-base">Gap Competency:</span>
                              <span className="font-extrabold text-blue-900 text-sm sm:text-base">{gap.code}</span>
                            </div>
                            <div className="flex items-center gap-4 text-sm sm:text-base">
                              <span className="text-slate-600">Current: <strong className="text-slate-900 font-bold">{gap.current_level}</strong></span>
                              <span className="text-slate-600">Required: <strong className="text-slate-900 font-bold">{gap.required_level}</strong></span>
                              <span className="text-rose-600 font-extrabold">
                                Gap: -{(gap.required_level - gap.current_level).toFixed(1)}
                              </span>
                            </div>
                          </div>

                          <div className="flex flex-wrap items-center gap-2 pt-1">
                            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Target Competencies:</span>
                            <span className="text-xs font-bold text-slate-800 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
                              Domain · Statistical Methodology
                            </span>
                            <span className="text-xs font-bold text-slate-800 bg-slate-100 px-3 py-1 rounded-full border border-slate-200">
                              MoSPI Cadre · {data.role}
                            </span>
                          </div>
                        </div>
                      )}

                      {/* AI Rationale (Increased Font Size) */}
                      <p className="text-sm sm:text-base text-slate-700 leading-relaxed font-normal pt-1">
                        {r.reason}
                      </p>



                    </div>

                    {/* RIGHT COLUMN (Course Banner Image Slot / Thumbnail Preview) */}
                    <div className="md:col-span-4 flex flex-col items-center justify-center space-y-3">
                      
                      {/* Match percentage badge at top of right column */}
                      <div className="w-full flex justify-end">
                        <span className="text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full shadow-2xs">
                          {Math.round(r.score)}% MATCH
                        </span>
                      </div>

                      {/* Image Thumbnail Slot */}
                      <div className="w-full relative group rounded-xl overflow-hidden border border-slate-200 shadow-sm bg-slate-100 aspect-video md:aspect-4/3">
                        <img 
                          src={imageUrl} 
                          alt={r.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-slate-900/70 via-slate-900/20 to-transparent flex flex-col justify-between p-3 text-white">
                          <div className="flex justify-between items-center">
                            <span className="text-[10px] font-bold uppercase bg-blue-600/90 text-white px-2 py-0.5 rounded backdrop-blur-xs">
                              {r.provider}
                            </span>
                            <span className="text-[10px] font-semibold bg-black/50 text-slate-200 px-2 py-0.5 rounded backdrop-blur-xs">
                              Course Banner
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-1.5 text-slate-200 text-[11px] font-medium">
                            <ImageIcon className="w-3.5 h-3.5 text-amber-300" />
                            <span>iGOT Official Artwork</span>
                          </div>
                        </div>
                      </div>

                      <span className="text-[11px] text-slate-400 text-center font-medium italic">
                        Click "View About & Content" below to inspect curriculum & outcomes.
                      </span>

                    </div>

                  </div>

                  {/* Explainability toggle & Score breakdown details block */}
                  <div className="pt-3 border-t border-slate-100">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <button
                        onClick={() => toggleExplanation(r.resource_id)}
                        className="flex items-center text-xs font-semibold text-slate-500 hover:text-slate-700 transition-colors"
                      >
                        {isExplanationExpanded ? (
                          <>
                            Hide Algorithm Score Breakdown <ChevronUp className="h-4 w-4 ml-1" />
                          </>
                        ) : (
                          <>
                            Algorithm Score Breakdown <ChevronDown className="h-4 w-4 ml-1" />
                          </>
                        )}
                      </button>

                      <button
                        onClick={() => {
                          const event = new CustomEvent("open-copilot", {
                            detail: {
                              query: `Why do you recommend '${r.title}' (${r.provider}) for my role, and what specific skill gaps does it bridge?`
                            }
                          });
                          window.dispatchEvent(event);
                        }}
                        className="flex items-center gap-1.5 text-xs font-bold text-indigo-700 hover:text-indigo-800 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 px-3 py-1.5 rounded-lg transition-all cursor-pointer shadow-2xs"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                        <span>Ask AI Why This Was Suggested</span>
                      </button>
                    </div>

                    {isExplanationExpanded && r.debug_scores && (
                      <div className="mt-4 bg-slate-50/50 border border-slate-200 rounded-md p-5 space-y-4 grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
                        {/* Dimensional scores list */}
                        <div className="space-y-2.5">
                          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">Matching Dimensions</h4>
                          
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-500">Competency Match (40%):</span>
                              <span className="font-semibold text-slate-700">{Math.round(r.debug_scores.competency_match * 100)}%</span>
                            </div>
                            <Progress value={r.debug_scores.competency_match * 100} colorClassName="bg-gov-blue-500" />
                          </div>

                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-500">Semantic Relevance (20%):</span>
                              <span className="font-semibold text-slate-700">{Math.round(r.debug_scores.semantic_similarity * 100)}%</span>
                            </div>
                            <Progress value={r.debug_scores.semantic_similarity * 100} colorClassName="bg-sky-500" />
                          </div>

                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-500">Difficulty Fit (15%):</span>
                              <span className="font-semibold text-slate-700">{Math.round(r.debug_scores.difficulty_fit * 100)}%</span>
                            </div>
                            <Progress value={r.debug_scores.difficulty_fit * 100} colorClassName="bg-amber-500" />
                          </div>

                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-500">Duration Fit (10%):</span>
                              <span className="font-semibold text-slate-700">{Math.round(r.debug_scores.duration_fit * 100)}%</span>
                            </div>
                            <Progress value={r.debug_scores.duration_fit * 100} colorClassName="bg-teal-500" />
                          </div>

                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-500">Provider Quality (10%):</span>
                              <span className="font-semibold text-slate-700">{Math.round(r.debug_scores.provider_quality * 100)}%</span>
                            </div>
                            <Progress value={r.debug_scores.provider_quality * 100} colorClassName="bg-indigo-500" />
                          </div>
                        </div>

                        {/* Gap analysis data block */}
                        <div className="bg-white border border-slate-200 rounded-md p-4 space-y-3">
                          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider border-b border-slate-100 pb-2">Target gap analysis</h4>
                          <div className="grid grid-cols-2 gap-4 text-xs leading-normal">
                            <div>
                              <span className="text-slate-400 block">Current Mastered:</span>
                              <span className="font-bold text-slate-700">{gap?.current_level || 0} / 5.0</span>
                            </div>
                            <div>
                              <span className="text-slate-400 block">Required Level:</span>
                              <span className="font-bold text-slate-700">{gap?.required_level || 0} / 5.0</span>
                            </div>
                            <div>
                              <span className="text-slate-400 block">Course Target Level:</span>
                              <span className="font-bold text-gov-blue-500">Level {r.difficulty === "Advanced" ? "4.0" : r.difficulty === "Intermediate" ? "3.0" : "2.0"}</span>
                            </div>
                            <div>
                              <span className="text-slate-400 block">Recency Bias:</span>
                              <span className="font-semibold text-emerald-600">Fresh Content (+{(r.debug_scores.recency * 5).toFixed(1)}%)</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                </CardContent>

                {/* EXPANDABLE TABBED DETAILS SECTION (About & Content Tabs) */}
                {isDetailsExpanded && (
                  <div className="bg-slate-50/90 border-t border-slate-200 p-6 space-y-6 animate-in fade-in duration-200">
                    
                    {/* Tab Navigation Header (Exact iGOT styling) */}
                    <div className="flex items-center gap-8 border-b border-slate-200">
                      <button
                        onClick={() => setCourseTab(r.resource_id, "about")}
                        className={`pb-3 text-sm font-bold transition-all relative ${
                          currentTab === "about"
                            ? "text-blue-900 border-b-2 border-blue-600"
                            : "text-slate-500 hover:text-slate-800"
                        }`}
                      >
                        About
                      </button>
                      <button
                        onClick={() => setCourseTab(r.resource_id, "content")}
                        className={`pb-3 text-sm font-bold transition-all relative ${
                          currentTab === "content"
                            ? "text-blue-900 border-b-2 border-blue-600"
                            : "text-slate-500 hover:text-slate-800"
                        }`}
                      >
                        Content
                      </button>
                    </div>

                    {/* TAB 1: ABOUT VIEW */}
                    {currentTab === "about" && (
                      <div className="space-y-6 text-slate-800">
                        
                        {/* Description Section */}
                        <div className="space-y-3">
                          <h4 className="text-base font-extrabold text-slate-900">Description</h4>
                          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal">
                            {(r as any).description || `Official capacity building module designed for statistical officers, data analysts, and policy administrators across MoSPI cadres. This curriculum delves into standard operating procedures, sampling error controls, questionnaire design, and field validation protocols required for high-precision national statistical inquiries.`}

                            {!showFullDesc[r.resource_id] && (
                              <span> Healthcare facilities and official statistical systems present unique and complex challenges for field execution. This course equips professionals with critical skills to manage operational risks effectively...</span>
                            )}
                          </p>
                          <button
                            onClick={() => setShowFullDesc(prev => ({ ...prev, [r.resource_id]: !prev[r.resource_id] }))}
                            className="text-xs font-bold text-blue-700 hover:text-blue-950 transition-colors inline-block"
                          >
                            {showFullDesc[r.resource_id] ? "view less" : "view more"}
                          </button>
                        </div>

                        {/* Learning Outcome Section */}
                        <div className="space-y-3 pt-4 border-t border-slate-200">
                          <h4 className="text-base font-extrabold text-slate-900">Learning Outcome</h4>
                          <ul className="space-y-2 text-xs sm:text-sm text-slate-700 font-normal list-disc pl-5">
                            <li>Identify specific survey hazards, risk factors, and sampling error classifications pertinent to official inquiries.</li>
                            <li>Demonstrate the correct operation of sampling calculators and frame validation using standard MoSPI protocols.</li>
                            <li>Develop a comprehensive and effective survey execution plan, including household prioritization and logistical coordination.</li>
                            <li>Analyze key regulatory requirements and operational standards under the Collection of Statistics Act.</li>
                            <li>Plan and execute field mock audits to evaluate and enhance enumerator response accuracy and team coordination.</li>
                            <li>Implement a holistic data quality assurance program to mitigate non-sampling errors and protect microdata integrity.</li>
                          </ul>
                          <button
                            onClick={() => setShowFullOutcomes(prev => ({ ...prev, [r.resource_id]: !prev[r.resource_id] }))}
                            className="text-xs font-bold text-blue-700 hover:text-blue-950 transition-colors inline-block"
                          >
                            {showFullOutcomes[r.resource_id] ? "view less" : "view more"}
                          </button>
                        </div>

                      </div>
                    )}

                    {/* TAB 2: CONTENT VIEW */}
                    {currentTab === "content" && (
                      <div className="space-y-3">
                        {((COURSE_CURRICULUM_DATA as any)[(r as any).code || r.resource_id] || COURSE_CURRICULUM_DATA["default"]).map((mod: any) => {

                          const isModOpen = !!expandedModules[mod.id];
                          return (
                            <div key={mod.id} className="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-2xs transition-all">
                              <button
                                onClick={() => toggleModule(mod.id)}
                                className="w-full p-4 text-left flex items-center justify-between gap-4 hover:bg-slate-50 transition-colors"
                              >
                                <div className="space-y-1">
                                  <h5 className="text-sm font-bold text-slate-900">{mod.title}</h5>
                                  <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                                    <Video className="w-3.5 h-3.5 text-slate-400" />
                                    <span>{mod.duration}</span>
                                    <span>•</span>
                                    <span>{mod.itemsCount} items</span>
                                  </div>
                                </div>
                                <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-blue-600 font-bold shrink-0">
                                  {isModOpen ? <Minus className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                                </div>
                              </button>

                              {isModOpen && (
                                <div className="px-4 pb-4 pt-1 bg-slate-50 border-t border-slate-100 space-y-2 text-xs text-slate-700">
                                  {mod.lessons.map((lesson: string, idx: number) => (
                                    <div key={idx} className="flex items-center justify-between p-2.5 bg-white rounded-lg border border-slate-200">
                                      <div className="flex items-center gap-2.5">
                                        <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                                        <span className="font-semibold text-slate-800">{lesson}</span>
                                      </div>
                                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                                        Verified Lesson
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}

                  </div>
                )}

              </Card>
            );
          })}
        </div>
      )}
    </div>
  )
}
