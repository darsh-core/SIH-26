import React, { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { 
  Award, 
  AlertTriangle, 
  TrendingUp, 
  ArrowRight, 
  CheckCircle, 
  Sparkles, 
  Layers, 
  BookOpen, 
  Info,
  ChevronRight,
  ShieldCheck,
  Brain
} from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { competencyApi } from "../services/competencyApi";
import { userApi } from "../services/userApi";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from "../components/ui/Primitives";

export const InitialCompetencyStatusPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const userId = user?.id || "";

  // 1. Fetch real competency gaps and overall readiness from backend
  const { 
    data: gapData, 
    isLoading: gapsLoading, 
    error: gapsError 
  } = useQuery({
    queryKey: ["competency-gaps", userId],
    queryFn: () => competencyApi.getCompetencyGaps(userId),
    enabled: !!userId
  });

  // Calculate status badge text from backend overall readiness
  const getReadinessStatus = (score: number) => {
    if (score >= 80) return { label: "Role Ready", variant: "success" as const, color: "text-emerald-700 bg-emerald-50 border-emerald-200" };
    if (score >= 55) return { label: "Developing", variant: "warning" as const, color: "text-amber-700 bg-amber-50 border-amber-200" };
    return { label: "Needs Development", variant: "error" as const, color: "text-rose-700 bg-rose-50 border-rose-200" };
  };

  // Status for each individual competency
  const getCompetencyStatus = (current: number, required: number, gap: number) => {
    if (gap <= 0.05) return { label: "STRONG", color: "text-emerald-700 bg-emerald-50 border-emerald-200" };
    if (current >= required * 0.85) return { label: "READY", color: "text-blue-700 bg-blue-50 border-blue-200" };
    if (gap > 1.2 || (gap / required) >= 0.35) return { label: "HIGH GAP", color: "text-rose-700 bg-rose-50 border-rose-200" };
    return { label: "DEVELOPING", color: "text-amber-700 bg-amber-50 border-amber-200" };
  };

  if (gapsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-gov-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-semibold text-slate-600">Retrieving your computed competency twin...</p>
      </div>
    );
  }

  if (gapsError || !gapData) {
    return (
      <div className="max-w-md mx-auto my-12 text-center p-6 bg-white rounded-xl border border-slate-200 shadow-xs">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-900">Unable to load Competency Status</h3>
        <p className="text-xs text-slate-500 mt-1">Please ensure the backend service is running.</p>
        <Button onClick={() => navigate("/dashboard")} className="mt-4 bg-gov-blue-500 text-white text-xs">
          Go to Dashboard
        </Button>
      </div>
    );
  }

  const readinessScore = gapData.overall_readiness;
  const readinessStatus = getReadinessStatus(readinessScore);
  const totalEvaluated = gapData.gaps.length;
  const priorityGapsCount = gapData.gaps.filter(g => g.priority === "HIGH" || g.gap > 0.5).length;

  // Sort gaps to find top priorities
  const sortedGaps = [...gapData.gaps].sort((a, b) => b.gap - a.gap);
  const topSkillGaps = sortedGaps.slice(0, 3);

  // Compute strongest areas (gaps <= 0 or lowest gaps)
  const strongAreas = [...gapData.gaps]
    .sort((a, b) => a.gap - b.gap)
    .slice(0, 3)
    .map(g => g.competency_name);

  // Largest growth opportunity
  const largestOpportunity = sortedGaps[0]?.competency_name || "Sampling Methodology";

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      
      {/* 1. Header Information Block (Prompt Section 7) */}
      <div className="border-b border-slate-200 pb-5">
        <div className="flex items-center gap-2 text-gov-blue-600 mb-1.5">
          <Sparkles className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider">Diagnostic Evaluation Completed</span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-950 tracking-tight">
          Your Competency Status
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Your current competency profile for the selected role.
        </p>

        {/* Official Identity Strip */}
        <div className="mt-4 p-4 rounded-xl bg-slate-900 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
          <div>
            <span className="text-[10px] font-bold text-gov-gold uppercase tracking-wider block">Official Assessed</span>
            <h2 className="text-base font-bold uppercase tracking-wide">
              {user?.profile?.first_name || "Arun"} {user?.profile?.last_name || "Kumar"}
            </h2>
          </div>
          <div className="sm:text-right border-t sm:border-t-0 pt-2 sm:pt-0 border-slate-800">
            <span className="text-sm font-semibold text-blue-200 block">
              {gapData.role.name || "Statistical Officer"}
            </span>
            <span className="text-xs text-slate-400">
              {user?.profile?.department || "Agricultural Statistics Division"}
            </span>
          </div>
        </div>
      </div>

      {/* 2. Large Role Readiness Card (Prompt Section 8) */}
      <Card className="border-gov-blue-200/70 shadow-lg overflow-hidden bg-gradient-to-b from-white to-slate-50/60">
        <CardContent className="p-8">
          <div className="flex flex-col items-center text-center">
            <span className="text-xs font-extrabold uppercase tracking-widest text-slate-500 mb-3">
              ROLE READINESS
            </span>

            {/* Circular score gauge */}
            <div className="relative flex items-center justify-center my-2">
              <svg className="w-44 h-44 transform -rotate-90">
                <circle
                  cx="88"
                  cy="88"
                  r="74"
                  className="stroke-slate-200"
                  strokeWidth="12"
                  fill="transparent"
                />
                <circle
                  cx="88"
                  cy="88"
                  r="74"
                  className="stroke-gov-blue-500 transition-all duration-1000 ease-out"
                  strokeWidth="12"
                  fill="transparent"
                  strokeDasharray={2 * Math.PI * 74}
                  strokeDashoffset={2 * Math.PI * 74 * (1 - readinessScore / 100)}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-4xl sm:text-5xl font-extrabold text-gov-blue-500 tracking-tight">
                  {readinessScore}%
                </span>
                <span className={`text-[11px] font-bold px-2.5 py-0.5 mt-1 rounded-full border ${readinessStatus.color}`}>
                  {readinessStatus.label}
                </span>
              </div>
            </div>

            <div className="mt-4 space-y-1">
              <h3 className="text-base font-bold text-slate-900">
                {gapData.role.name}
              </h3>
              <p className="text-xs text-slate-500">
                {user?.profile?.department || "Agricultural Statistics Division"}
              </p>
            </div>

            <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-xs font-semibold text-slate-600 bg-white border border-slate-200 py-2.5 px-6 rounded-full shadow-2xs">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-gov-blue-500" />
                {totalEvaluated} competencies evaluated
              </span>
              <span className="text-slate-300">•</span>
              <span className="flex items-center gap-1.5 text-rose-600">
                <AlertTriangle className="w-4 h-4" />
                {priorityGapsCount} priority gaps identified
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 3. Competency Twin: Visual Horizontal Bars (Prompt Section 9 & 10) */}
      <Card className="border-slate-200 shadow-md">
        <CardHeader className="bg-slate-50/70 border-b border-slate-100 pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Your Competency Twin</CardTitle>
              <p className="text-xs text-slate-500 mt-0.5">
                Current evaluated skill level vs. authoritative requirements for {gapData.role.name}.
              </p>
            </div>
            <span className="text-xs font-mono text-slate-500 bg-white px-2.5 py-1 rounded-md border border-slate-200 font-semibold">
              Scale: 0–5 Levels
            </span>
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-6">
          {gapData.gaps.map((comp, idx) => {
            const currentPct = Math.round((comp.current_level / 5) * 100);
            const requiredPct = Math.round((comp.required_level / 5) * 100);
            const gapPct = Math.max(0, requiredPct - currentPct);
            const compStatus = getCompetencyStatus(comp.current_level, comp.required_level, comp.gap);

            return (
              <div key={idx} className="space-y-2 pb-4 border-b border-slate-100 last:border-0 last:pb-0">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">{comp.competency_name}</span>
                    {comp.mandatory && (
                      <span className="text-[9px] font-bold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                        MANDATORY
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-slate-500">
                      Current: <strong className="text-slate-800 font-bold">{currentPct}%</strong>
                    </span>
                    <span className="text-slate-300">|</span>
                    <span className="text-slate-500">
                      Required: <strong className="text-slate-800 font-bold">{requiredPct}%</strong>
                    </span>
                    <span className="text-slate-300">|</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${compStatus.color}`}>
                      {compStatus.label}
                    </span>
                  </div>
                </div>

                {/* Visual Dual Progress Bars */}
                <div className="space-y-1">
                  <div className="relative h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                    {/* Required Level Track Indicator */}
                    <div 
                      className="absolute top-0 bottom-0 bg-slate-300/80 rounded-full"
                      style={{ width: `${requiredPct}%` }}
                    />
                    {/* Current Level Filled Bar */}
                    <div 
                      className="absolute top-0 bottom-0 bg-gov-blue-500 rounded-full transition-all duration-700"
                      style={{ width: `${currentPct}%` }}
                    />
                  </div>

                  {/* Gap callout */}
                  <div className="flex justify-between text-[11px] text-slate-500 font-medium">
                    <span>Assessed Level: {comp.current_level} / 5</span>
                    <span className={comp.gap > 0 ? "text-rose-600 font-semibold" : "text-emerald-600 font-semibold"}>
                      {comp.gap > 0 ? `Gap: ${gapPct} percentage points (${comp.gap.toFixed(1)} level)` : "Requirement Met ✓"}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* 4. Top Priority Skill Gaps (Prompt Section 11) */}
      <Card className="border-slate-200 shadow-md">
        <CardHeader className="bg-slate-50/70 border-b border-slate-100 pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-500" />
              Your Top Skill Gaps
            </CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/competencies")}
              className="text-xs"
            >
              View All Competencies
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {topSkillGaps.map((gap, i) => {
              const currentPct = Math.round((gap.current_level / 5) * 100);
              const requiredPct = Math.round((gap.required_level / 5) * 100);
              const gapPct = Math.max(0, requiredPct - currentPct);

              return (
                <div 
                  key={i} 
                  className="p-4 rounded-xl bg-white border border-slate-200 hover:border-gov-blue-300 shadow-2xs space-y-2.5 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="w-6 h-6 rounded-full bg-slate-900 text-white text-xs font-bold flex items-center justify-center">
                      {i + 1}
                    </span>
                    <Badge variant={gap.priority === "HIGH" ? "error" : "warning"}>
                      {gap.priority} PRIORITY
                    </Badge>
                  </div>

                  <div>
                    <h4 className="text-sm font-bold text-slate-900 line-clamp-1">{gap.competency_name}</h4>
                    <span className="text-[10px] font-mono text-slate-400">{gap.competency_code}</span>
                  </div>

                  <div className="text-xs text-slate-600 space-y-1 pt-1 border-t border-slate-100">
                    <div className="flex justify-between">
                      <span>Current:</span>
                      <strong className="text-slate-800 font-bold">{currentPct}%</strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Required:</span>
                      <strong className="text-slate-800 font-bold">{requiredPct}%</strong>
                    </div>
                    <div className="flex justify-between text-rose-600 font-bold">
                      <span>Gap:</span>
                      <span>{gapPct}%</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 5. AI Insight Card (Prompt Section 12) */}
      <Card className="border-indigo-200 bg-gradient-to-r from-indigo-50/60 via-blue-50/40 to-white shadow-md">
        <CardContent className="p-6 sm:p-8 space-y-4">
          <div className="flex items-center gap-2 text-indigo-700">
            <Brain className="w-5 h-5" />
            <span className="text-xs font-extrabold uppercase tracking-wider">AI Competency Insight</span>
          </div>

          <p className="text-sm text-slate-800 leading-relaxed">
            "Your strongest areas are <strong>{strongAreas.join(", ")}</strong>. Your largest development opportunity is <strong>{largestOpportunity}</strong>, which has the highest competency gap for your current role."
          </p>

          <div className="p-3.5 rounded-lg bg-white/80 border border-indigo-100 text-xs text-indigo-950 font-medium">
            <strong>Recommended next step:</strong> Strengthen <em>{largestOpportunity}</em> through the prioritized MoSPI learning plan.
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <Button
              onClick={() => navigate("/learning-plan")}
              className="flex items-center justify-center gap-2 bg-gov-blue-500 hover:bg-gov-blue-600 text-white font-bold px-6 py-2.5 rounded-lg shadow-md"
            >
              <span>View My Learning Plan</span>
              <ArrowRight className="w-4 h-4" />
            </Button>

            <Button
              variant="outline"
              onClick={() => navigate("/dashboard")}
              className="border-slate-300 text-slate-700 text-xs"
            >
              Enter Official Dashboard
            </Button>
          </div>
        </CardContent>
      </Card>

    </div>
  );
};
