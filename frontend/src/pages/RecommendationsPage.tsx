import React, { useState } from "react"
import { useSearchParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { 
  HelpCircle, 
  RotateCw, 
  Plus, 
  Check, 
  Search, 
  Info, 
  BookOpen,
  ChevronDown,
  ChevronUp
} from "lucide-react"

import { useAuthStore } from "../store/authStore"
import { recommendationApi } from "../services/recommendationApi"
import { learningPlanApi } from "../services/learningPlanApi"
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Alert, Progress } from "../components/ui/Primitives"
import { formatDuration } from "../lib/utils"

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
  const [expandedExplanation, setExpandedExplanation] = useState<Record<string, boolean>>({});

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

  const toggleExplanation = (resourceId: string) => {
    setExpandedExplanation(prev => ({
      ...prev,
      [resourceId]: !prev[resourceId]
    }));
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
    <div className="space-y-6">
      {/* Top action block */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-950">Personalized Learning Recommendations</h1>
          <p className="text-sm text-slate-500">
            BRIDGING COMPETENCY GAPS FOR ROLE: <strong className="text-gov-blue-500 font-semibold">{data.role}</strong>
          </p>
        </div>
        <div className="flex gap-3 shrink-0">
          <Button 
            variant="outline" 
            onClick={() => refreshMutation.mutate()} 
            isLoading={refreshMutation.isPending || isFetching}
          >
            <RotateCw className="h-4 w-4 mr-2" />
            Refresh gap catalog
          </Button>
          <Button 
            variant="primary" 
            onClick={() => addToPlanMutation.mutate()} 
            isLoading={addToPlanMutation.isPending}
          >
            <Plus className="h-4 w-4 mr-2" />
            Add all to Learning Journey
          </Button>
        </div>
      </div>

      {/* Filter Tabs Block */}
      <Card className="p-4 bg-slate-50 border-slate-200">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-500 uppercase">Provider:</span>
            <div className="flex bg-white border border-slate-200 rounded-md p-1 shadow-2xs">
              <button 
                onClick={() => setProviderFilter("ALL")} 
                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${providerFilter === "ALL" ? "bg-gov-blue-500 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
              >
                All
              </button>
              <button 
                onClick={() => setProviderFilter("IGOT")} 
                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${providerFilter === "IGOT" ? "bg-gov-blue-500 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
              >
                iGOT
              </button>
              <button 
                onClick={() => setProviderFilter("NSSTA")} 
                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${providerFilter === "NSSTA" ? "bg-gov-blue-500 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
              >
                NSSTA
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-slate-500 uppercase">Priority:</span>
            <div className="flex bg-white border border-slate-200 rounded-md p-1 shadow-2xs">
              <button 
                onClick={() => setPriorityFilter("ALL")} 
                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${priorityFilter === "ALL" ? "bg-gov-blue-500 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
              >
                All Gaps
              </button>
              <button 
                onClick={() => setPriorityFilter("HIGH")} 
                className={`px-3 py-1 text-xs font-bold rounded-md transition-all ${priorityFilter === "HIGH" ? "bg-gov-blue-500 text-white shadow-xs" : "text-slate-600 hover:bg-slate-100"}`}
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
              className="block w-full pl-9 pr-3 py-1.5 border border-slate-200 bg-white rounded-md text-xs placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gov-blue-500 focus:border-gov-blue-500 focus:bg-white text-slate-700"
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

      {/* Main Grid View */}
      {data.recommendations.length === 0 ? (
        <div className="text-center py-12 bg-white border border-slate-200 rounded-lg p-6">
          <BookOpen className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-base font-bold text-slate-800">No competency gaps or matching recommendations found.</h3>
          <p className="text-xs text-slate-400 mt-2">Adjust your filters, check active gaps, or reload the gap catalog.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {data.recommendations.map(r => {
            const gap = r.target_competencies[0];
            const isExpanded = !!expandedExplanation[r.resource_id];
            
            return (
              <Card key={r.resource_id} className="relative hover:border-slate-300 transition-all border-l-4 border-l-gov-blue-500 flex flex-col">
                <CardContent className="p-6 space-y-4 flex-1">
                  
                  {/* Title and provider match banner */}
                  <div className="flex justify-between items-start gap-4">
                    <div className="space-y-1 min-w-0">
                      <h3 className="text-base font-bold text-slate-900 leading-snug">{r.title}</h3>
                      <div className="flex flex-wrap items-center gap-3">
                        <Badge variant="secondary" className="px-2 py-0">
                          {r.provider}
                        </Badge>
                        <span className="text-xs text-slate-400 font-semibold uppercase">
                          {r.resource_type}
                        </span>
                        <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />
                        <span className="text-xs text-slate-500 font-medium">
                          {r.difficulty} · {formatDuration(r.estimated_duration_minutes)}
                        </span>
                      </div>
                    </div>
                    
                    <span className="text-xs font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full shrink-0">
                      {Math.round(r.score)}% MATCH
                    </span>
                  </div>

                  {/* Competency indicators mapping */}
                  {gap && (
                    <div className="bg-slate-50 border border-slate-100 rounded-md px-4 py-2.5 flex items-center justify-between gap-4 text-xs">
                      <div>
                        <span className="text-slate-400 font-medium block">Gap Competency</span>
                        <span className="font-bold text-slate-700">{gap.code}</span>
                      </div>
                      <div className="flex gap-4 text-right">
                        <span>Current: <strong className="text-slate-800">{gap.current_level}</strong></span>
                        <span>Required: <strong className="text-slate-800">{gap.required_level}</strong></span>
                        <span className="text-rose-600 font-semibold">Gap: -{(gap.required_level - gap.current_level).toFixed(1)}</span>
                      </div>
                    </div>
                  )}

                  {/* Logic explanation rationale */}
                  <p className="text-xs text-slate-600 leading-relaxed font-medium">
                    {r.reason}
                  </p>

                  {/* Explainability toggle & Score breakdown details block */}
                  <div className="pt-2 border-t border-slate-100">
                    <button
                      onClick={() => toggleExplanation(r.resource_id)}
                      className="flex items-center text-xs font-semibold text-gov-blue-500 hover:text-gov-blue-600 transition-colors"
                    >
                      {isExpanded ? (
                        <>
                          Hide Score Breakdown <ChevronUp className="h-4 w-4 ml-1" />
                        </>
                      ) : (
                        <>
                          Why this recommendation? <ChevronDown className="h-4 w-4 ml-1" />
                        </>
                      )}
                    </button>

                    {isExpanded && r.debug_scores && (
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
              </Card>
            );
          })}
        </div>
      )}
    </div>
  )
}
