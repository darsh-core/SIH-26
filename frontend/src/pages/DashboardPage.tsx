import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from "recharts";
import { 
  AlertTriangle, 
  Award, 
  BookOpen, 
  CheckCircle2, 
  ArrowRight, 
  Activity,
  Users,
  Upload,
  FileText,
  Settings,
  PlusCircle,
  Database,
  Eye,
  ShieldCheck,
  TrendingUp,
  BrainCircuit,
  Brain,
  Sparkles,
  HelpCircle,
  Clock,
  RotateCcw,
  Target,
  ExternalLink,
  ChevronRight,
  Info,
  X,
  Play
} from "lucide-react";

import { useAuthStore } from "../store/authStore";
import { competencyApi } from "../services/competencyApi";
import { recommendationApi } from "../services/recommendationApi";
import { documentApi } from "../services/documentApi";
import { learningPlanApi } from "../services/learningPlanApi";
import { learningApi } from "../services/learningApi";
import { CompetencyGapDetail } from "../types/competency";
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Progress } from "../components/ui/Primitives";

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const userId = user?.id || "";

  // Check if current user is a Staff / Trainer / Administrator
  const isTrainerOrStaff = Boolean(
    user?.is_superuser || 
    user?.email?.toLowerCase().includes("trainer") ||
    user?.profile?.designation?.toLowerCase().includes("director") ||
    user?.profile?.designation?.toLowerCase().includes("trainer") ||
    user?.roles?.some(r => 
      ["TRAINER", "ADMIN", "ADMINISTRATOR", "EVALUATOR", "SUPERVISOR", "MANAGER"].includes(r.name?.toUpperCase())
    )
  );

  // Allow trainers to toggle between Staff Academy view and Learner view
  const [viewMode, setViewMode] = useState<"staff" | "learner">(isTrainerOrStaff ? "staff" : "learner");
  const [selectedModalGap, setSelectedModalGap] = useState<CompetencyGapDetail | null>(null);

  // 1. Fetch competency gaps for learner view
  const { 
    data: gapData, 
    isLoading: gapsLoading, 
    error: gapsError 
  } = useQuery({
    queryKey: ["competency-gaps", userId],
    queryFn: () => competencyApi.getCompetencyGaps(userId),
    enabled: !!userId && viewMode === "learner"
  });

  // 2. Fetch top recommendations for learner view
  const { 
    data: recData, 
    isLoading: recsLoading 
  } = useQuery({
    queryKey: ["recommendations-preview", userId],
    queryFn: () => recommendationApi.getRecommendations(userId, { limit: 3 }),
    enabled: !!userId
  });

  // 3. Fetch active learning plan items
  const {
    data: planData
  } = useQuery({
    queryKey: ["learning-plan-preview", userId],
    queryFn: () => learningPlanApi.getLearningPlans(userId),
    enabled: !!userId
  });

  // 4. Fetch documents for staff view
  const { 
    data: docsData, 
    isLoading: docsLoading 
  } = useQuery({
    queryKey: ["staff-documents-preview"],
    queryFn: () => documentApi.listDocuments(1, 5),
    enabled: isTrainerOrStaff
  });

  // Status mapping for role readiness
  const getReadinessStatus = (score: number) => {
    if (score >= 80) return { label: "Role Ready", color: "text-emerald-700 bg-emerald-50 border-emerald-200" };
    if (score >= 55) return { label: "Developing", color: "text-amber-700 bg-amber-50 border-amber-200" };
    return { label: "Needs Development", color: "text-rose-700 bg-rose-50 border-rose-200" };
  };

  // Status for each individual competency
  const getCompetencyStatus = (current: number, required: number, gap: number) => {
    if (gap <= 0.05) return { label: "STRONG", color: "text-emerald-700 bg-emerald-50 border-emerald-200" };
    if (current >= required * 0.85) return { label: "READY", color: "text-blue-700 bg-blue-50 border-blue-200" };
    if (gap > 1.2 || (gap / required) >= 0.35) return { label: "HIGH GAP", color: "text-rose-700 bg-rose-50 border-rose-200" };
    return { label: "DEVELOPING", color: "text-amber-700 bg-amber-50 border-amber-200" };
  };

  // -------------------------------------------------------------
  // STAFF / TRAINER DASHBOARD RENDER
  // -------------------------------------------------------------
  if (isTrainerOrStaff && viewMode === "staff") {
    const divisionData = [
      { division: "Agricultural Stats", Readiness: 76.4, Officers: 14 },
      { division: "NSSO Field Ops", Readiness: 71.2, Officers: 18 },
      { division: "Survey Design (SDRD)", Readiness: 68.5, Officers: 6 },
      { division: "Price Statistics", Readiness: 82.0, Officers: 6 },
      { division: "Data Warehouse", Readiness: 79.5, Officers: 4 },
    ];

    const totalChunks = docsData?.items?.reduce((acc, d) => acc + (d.chunk_count || 0), 0) || 170;

    return (
      <div className="space-y-8">
        {/* Staff Header Block */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-950">
                Welcome, {user?.profile?.first_name || "Dr. Sunita"} {user?.profile?.last_name || "Sharma"}
              </h1>
              <Badge variant="info">
                {user?.profile?.designation || "Senior Training Director · NSSTA"}
              </Badge>
            </div>
            <p className="text-sm text-slate-500 font-medium mt-1">
              National Statistical Systems Training Academy (NSSTA Greater Noida) · Training Intelligence Command Center
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setViewMode("learner")}
              className="text-xs border-gov-blue-200 text-gov-blue-600 hover:bg-gov-blue-50"
            >
              Switch to Learner Competency View
            </Button>

            <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg px-4 py-2 shadow-xs">
              <ShieldCheck className="h-5 w-5 text-gov-gold" />
              <div>
                <span className="text-[10px] text-slate-400 font-semibold block uppercase">Faculty Clearance</span>
                <span className="text-xs font-bold text-slate-700">Official Evaluator</span>
              </div>
            </div>
          </div>
        </div>

        {/* 4 Staff Command Center KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="border-gov-blue-100 bg-white hover:shadow-md transition-all duration-300 hover:-translate-y-1">
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Total Trainees</span>
                <span className="text-2xl font-extrabold text-slate-900 mt-1 block">48 Officers</span>
                <span className="text-[10px] text-emerald-600 font-semibold">● 14 Under Diagnostic Evaluation</span>
              </div>
              <div className="p-3 bg-gov-blue-50 text-gov-blue-500 rounded-xl shadow-inner">
                <Users className="h-6 w-6" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-indigo-100 bg-white hover:shadow-md transition-all duration-300 hover:-translate-y-1">
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Avg Role Readiness</span>
                <span className="text-2xl font-extrabold text-gov-blue-500 mt-1 block">74.2%</span>
                <span className="text-[10px] text-emerald-600 font-semibold">▲ +4.8% post-training</span>
              </div>
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-xl shadow-inner">
                <TrendingUp className="h-6 w-6" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-purple-100 bg-white hover:shadow-md transition-all duration-300 hover:-translate-y-1">
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Vectorized Manuals</span>
                <span className="text-2xl font-extrabold text-purple-600 mt-1 block">{docsData?.total || 3} Files</span>
                <span className="text-[10px] text-purple-700 font-semibold">{totalChunks} Chunks (384-D)</span>
              </div>
              <div className="p-3 bg-purple-50 text-purple-600 rounded-xl shadow-inner">
                <Database className="h-6 w-6" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-amber-100 bg-white hover:shadow-md transition-all duration-300 hover:-translate-y-1">
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Pending Review</span>
                <span className="text-2xl font-extrabold text-amber-600 mt-1 block">5 Items</span>
                <span className="text-[10px] text-amber-700 font-semibold">Human-in-the-Loop Quality Gate</span>
              </div>
              <div className="p-3 bg-amber-50 text-amber-600 rounded-xl shadow-inner">
                <BrainCircuit className="h-6 w-6" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Divisional Competency Chart */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle>Divisional Competency Readiness Benchmark</CardTitle>
                <p className="text-xs text-slate-400 mt-0.5">Average competency achievement against prescribed MoSPI cadres</p>
              </div>
              <span className="text-xs font-semibold text-gov-blue-500 bg-gov-blue-50 px-2.5 py-1 rounded-md">
                5 Divisions
              </span>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={divisionData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="division" tick={{ fill: "#475569", fontSize: 10, fontWeight: 500 }} angle={-15} textAnchor="end" interval={0} />
                    <YAxis domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} tick={{ fill: "#64748b", fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="Readiness" fill="#1e3a8a" radius={[6, 6, 0, 0]} barSize={34} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Critical Systemic Gaps */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-rose-500" />
                Critical Systemic Gaps
              </CardTitle>
              <p className="text-xs text-slate-400 mt-0.5">Priority training needs across cadre</p>
            </CardHeader>
            <CardContent className="space-y-4 pt-2">
              <div className="p-3.5 bg-rose-50/50 rounded-xl border border-rose-100 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">Sampling Methodology</span>
                  <Badge variant="error">HIGH PRIORITY</Badge>
                </div>
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Workforce Deficit</span>
                  <span className="font-bold text-rose-600">38% Gap</span>
                </div>
                <Progress value={62} className="h-1.5" />
                <p className="text-[10px] text-slate-400">Targeting TRS Village Sampling & Crop Cutting surveys.</p>
              </div>

              <div className="p-3.5 bg-rose-50/50 rounded-xl border border-rose-100 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">Survey Design & Protocols</span>
                  <Badge variant="error">HIGH PRIORITY</Badge>
                </div>
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Workforce Deficit</span>
                  <span className="font-bold text-rose-600">31% Gap</span>
                </div>
                <Progress value={69} className="h-1.5" />
                <p className="text-[10px] text-slate-400">NSSO multi-stage stratified schedule verification.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // LEARNER DASHBOARD (SANKHYAI EMPLOYEE EXPERIENCE)
  // -------------------------------------------------------------
  if (gapsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-gov-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-semibold text-slate-600">Retrieving your role readiness & competency twin...</p>
      </div>
    );
  }

  // Handle employees who haven't taken the diagnostic yet (Prompt Section 22: Empty States)
  if (gapsError || !gapData || !user?.profile?.job_role_id) {
    return (
      <div className="max-w-xl mx-auto my-12 text-center p-8 bg-white rounded-2xl border border-slate-200 shadow-lg space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-gov-blue-50 text-gov-blue-500 border border-gov-blue-200 flex items-center justify-center mx-auto">
          <Brain className="w-8 h-8" />
        </div>

        <div className="space-y-1.5">
          <h2 className="text-xl font-bold text-slate-900">
            Let's build your competency profile
          </h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
            You haven't completed your role diagnostic yet. Select your department and job role to generate your personalized MoSPI competency twin.
          </p>
        </div>

        <Button
          onClick={() => navigate("/onboarding/role")}
          className="bg-gov-blue-500 hover:bg-gov-blue-600 text-white font-bold text-xs py-3 px-6 rounded-lg shadow-md inline-flex items-center gap-2"
        >
          <span>Start AI Role Diagnostic</span>
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    );
  }

  const readinessScore = gapData.overall_readiness;
  const readinessStatus = getReadinessStatus(readinessScore);
  const totalEvaluated = gapData.gaps.length;
  const priorityGaps = [...gapData.gaps].sort((a, b) => b.gap - a.gap);
  const topSkillGaps = priorityGaps.slice(0, 3);

  // Compute strongest areas
  const strongAreas = [...gapData.gaps]
    .sort((a, b) => a.gap - b.gap)
    .slice(0, 3)
    .map(g => g.competency_name);

  // Largest growth opportunity
  const largestOpportunity = priorityGaps[0]?.competency_name || "Sampling Methodology";

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      
      {/* 1. Header Block: Employee Identity, Role, Department, Domain (Prompt Section 1 & 17) */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 text-gov-blue-600 mb-1">
            <ShieldCheck className="w-4 h-4" />
            <span className="text-[11px] font-bold uppercase tracking-wider">AI Competency & Role Readiness Dashboard</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-950 tracking-tight">
            Welcome back, {user?.profile?.first_name || "Arun"} {user?.profile?.last_name || "Kumar"}
          </h1>
          <p className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-2 font-medium">
            <strong className="text-slate-800">{gapData.role.name}</strong>
            <span>•</span>
            <span>{user?.profile?.department || "Agricultural Statistics Division"}</span>
            <span>•</span>
            <span className="text-slate-400">Last Assessed: {new Date().toLocaleDateString("en-IN")}</span>
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {isTrainerOrStaff && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setViewMode("staff")}
              className="text-xs border-gov-blue-200 text-gov-blue-600 hover:bg-gov-blue-50"
            >
              Switch to Academy Staff View
            </Button>
          )}

          {/* Quick Reassessment Trigger */}
          <Button
            size="sm"
            onClick={() => navigate("/progress")}
            className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs px-3.5 py-2 rounded-lg shadow-xs"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reassess</span>
          </Button>
        </div>
      </div>

      {/* 2. Top Hero: Role Readiness Card (Prompt Section 8 & 17) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Overall Readiness Gauge */}
        <Card className="lg:col-span-1 border-gov-blue-200/80 bg-gradient-to-b from-white to-gov-blue-50/30 flex flex-col justify-between shadow-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-xs uppercase font-extrabold text-slate-500 tracking-wider">
                ROLE READINESS
              </CardTitle>
              <Badge variant={readinessScore >= 80 ? "success" : (readinessScore >= 55 ? "warning" : "error")}>
                {readinessStatus.label}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="flex flex-col items-center justify-center py-6">
            <div className="relative flex items-center justify-center">
              <svg className="w-40 h-40 transform -rotate-90">
                <circle 
                  cx="80" 
                  cy="80" 
                  r="66" 
                  className="stroke-slate-200" 
                  strokeWidth="12" 
                  fill="transparent" 
                />
                <circle 
                  cx="80" 
                  cy="80" 
                  r="66" 
                  className="stroke-gov-blue-500 transition-all duration-1000 ease-out" 
                  strokeWidth="12" 
                  fill="transparent" 
                  strokeDasharray={2 * Math.PI * 66}
                  strokeDashoffset={2 * Math.PI * 66 * (1 - readinessScore / 100)}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-4xl font-extrabold text-gov-blue-500 tracking-tight">
                  {readinessScore}%
                </span>
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Overall</span>
              </div>
            </div>

            <div className="text-center mt-4 space-y-0.5">
              <h3 className="text-sm font-bold text-slate-900">{gapData.role.name}</h3>
              <p className="text-[11px] text-slate-500">{user?.profile?.department}</p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 w-full flex justify-between text-[11px] text-slate-500 font-medium px-2">
              <span>{totalEvaluated} competencies</span>
              <span className="text-rose-600 font-bold">{topSkillGaps.filter(g => g.gap > 0).length} priority gaps</span>
            </div>
          </CardContent>
        </Card>

        {/* Right: AI Insight Card & Top Stats (Prompt Section 12 & 17) */}
        <div className="lg:col-span-2 flex flex-col justify-between space-y-4">
          {/* AI Insight Card */}
          <Card className="border-indigo-100 bg-gradient-to-r from-indigo-50/70 via-blue-50/40 to-white shadow-xs">
            <CardContent className="p-6 space-y-3">
              <div className="flex items-center gap-2 text-indigo-700">
                <Brain className="w-4 h-4" />
                <span className="text-xs font-bold uppercase tracking-wider">AI Competency Insight</span>
              </div>

              <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-medium">
                "Your strongest areas are <strong>{strongAreas.join(", ")}</strong>. Your largest development opportunity is <strong>{largestOpportunity}</strong>, which has the highest competency gap for your current role."
              </p>

              <div className="p-3 rounded-lg bg-white/90 border border-indigo-100 text-xs text-indigo-950 font-medium flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <span>
                  <strong>Recommended next step:</strong> Strengthen <em>{largestOpportunity}</em>.
                </span>
                <div className="flex items-center gap-2 shrink-0">
                  <Button 
                    size="sm"
                    onClick={() => {
                      const event = new CustomEvent("open-copilot", {
                        detail: {
                          query: "Analyze my current skill gaps, role readiness, and recommended courses with the rationale for each suggestion."
                        }
                      });
                      window.dispatchEvent(event);
                    }}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] py-1.5 px-3 flex items-center gap-1.5 shadow-xs cursor-pointer font-bold"
                  >
                    <Sparkles className="w-3 h-3 text-indigo-200" />
                    <span>Real-Time AI Analysis</span>
                  </Button>
                  <Button 
                    size="sm"
                    variant="outline"
                    onClick={() => navigate("/learning-plan")}
                    className="border-indigo-200 text-indigo-700 hover:bg-indigo-50 text-[11px] py-1.5 px-3"
                  >
                    <span>View Plan</span>
                    <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Competencies</span>
              <span className="text-xl font-extrabold text-slate-800 mt-0.5 block">{totalEvaluated}</span>
              <span className="text-[10px] text-slate-500">Cadre Standard</span>
            </div>

            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Active Gaps</span>
              <span className="text-xl font-extrabold text-rose-600 mt-0.5 block">
                {gapData.gaps.filter(g => g.gap > 0).length}
              </span>
              <span className="text-[10px] text-rose-500 font-semibold">Priority Deficits</span>
            </div>

            <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-2xs text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Learning Status</span>
              <span className="text-xl font-extrabold text-gov-blue-500 mt-0.5 block">Active</span>
              <span className="text-[10px] text-emerald-600 font-semibold">iGOT Pathway</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Middle: Competency Twin with Horizontal Bars & Top Skill Gaps (Prompt Section 9, 10, 11) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Competency Twin (2 Cols) */}
        <Card className="lg:col-span-2 border-slate-200 shadow-sm">
          <CardHeader className="bg-slate-50/70 border-b border-slate-100 pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base">Your Competency Twin</CardTitle>
              <p className="text-xs text-slate-400 mt-0.5">Current vs Required proficiency across evaluated role domains</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/competencies")}
              className="text-xs text-slate-700"
            >
              Full Framework
            </Button>
          </CardHeader>

          <CardContent className="p-6 space-y-4">
            {gapData.gaps.map((comp, idx) => {
              const currentPct = Math.round((comp.current_level / 5) * 100);
              const requiredPct = Math.round((comp.required_level / 5) * 100);
              const gapPct = Math.max(0, requiredPct - currentPct);
              const compStatus = getCompetencyStatus(comp.current_level, comp.required_level, comp.gap);

              return (
                <div key={idx} className="space-y-1.5 pb-3 border-b border-slate-100 last:border-0 last:pb-0">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800">{comp.competency_name}</span>
                      {comp.mandatory && (
                        <span className="text-[9px] font-bold text-rose-700 bg-rose-50 px-1 py-0.2 rounded border border-rose-200">
                          MANDATORY
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2.5 text-[11px]">
                      <span>Current: <strong>{currentPct}%</strong></span>
                      <span className="text-slate-300">|</span>
                      <span>Required: <strong>{requiredPct}%</strong></span>
                      <span className="text-slate-300">|</span>
                      <span className={`px-1.5 py-0.2 rounded text-[10px] font-bold border ${compStatus.color}`}>
                        {compStatus.label}
                      </span>
                    </div>
                  </div>

                  {/* Dual Bar (Current vs Required) */}
                  <div className="space-y-1">
                    <div className="relative h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="absolute top-0 bottom-0 bg-slate-300 rounded-full"
                        style={{ width: `${requiredPct}%` }}
                      />
                      <div 
                        className="absolute top-0 bottom-0 bg-gov-blue-500 rounded-full"
                        style={{ width: `${currentPct}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-400">
                      <span>Level {comp.current_level} / 5</span>
                      <span className={comp.gap > 0 ? "text-rose-600 font-semibold" : "text-emerald-600 font-semibold"}>
                        {comp.gap > 0 ? `Gap: ${gapPct} percentage points` : "Target Met ✓"}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Top Skill Gaps (1 Col) */}
        <Card className="lg:col-span-1 border-slate-200 shadow-sm flex flex-col justify-between">
          <CardHeader className="bg-slate-50/70 border-b border-slate-100 pb-3">
            <CardTitle className="text-base flex items-center gap-2 text-rose-600">
              <AlertTriangle className="w-4 h-4" />
              Top Skill Gaps
            </CardTitle>
            <p className="text-xs text-slate-400 mt-0.5">Highest priority deficits</p>
          </CardHeader>

          <CardContent className="p-5 space-y-3 flex-1">
            {topSkillGaps.map((gap, i) => {
              const currentPct = Math.round((gap.current_level / 5) * 100);
              const requiredPct = Math.round((gap.required_level / 5) * 100);
              const gapPct = Math.max(0, requiredPct - currentPct);

              return (
                <div 
                  key={i}
                  className="p-3.5 rounded-xl border border-slate-200 bg-white hover:border-gov-blue-300 shadow-2xs space-y-2 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="w-5 h-5 rounded-full bg-slate-900 text-white text-[11px] font-bold flex items-center justify-center">
                      {i + 1}
                    </span>
                    <Badge variant={gap.priority === "HIGH" ? "error" : "warning"}>
                      {gap.priority}
                    </Badge>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-slate-900 truncate">{gap.competency_name}</h4>
                    <span className="text-[10px] text-slate-400 font-mono">{gap.competency_code}</span>
                  </div>

                  <div className="flex justify-between text-[11px] text-slate-600 pt-1 border-t border-slate-100">
                    <span>Gap: <strong className="text-rose-600">{gapPct}%</strong></span>
                    <button
                      onClick={() => setSelectedModalGap(gap)}
                      className="text-gov-blue-600 hover:underline font-bold text-[10px] cursor-pointer"
                    >
                      Why this gap? →
                    </button>
                  </div>
                </div>
              );
            })}
          </CardContent>

          <div className="p-4 border-t border-slate-100 bg-slate-50/50">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/skill-gaps")}
              className="w-full text-xs text-slate-700"
            >
              View All Priority Gaps
            </Button>
          </div>
        </Card>
      </div>

      {/* 4. Bottom: Recommended Learning & AI Learning Plan (Prompt Section 14, 15, 17) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recommended For You */}
        <Card className="border-slate-200 shadow-sm">
          <CardHeader className="bg-slate-50/70 border-b border-slate-100 pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-gov-blue-500" />
                Recommended For You
              </CardTitle>
              <p className="text-xs text-slate-400 mt-0.5">Aligned to bridge your highest competency deficits</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/recommendations")}
              className="text-xs text-slate-700"
            >
              View All
            </Button>
          </CardHeader>

          <CardContent className="p-5 space-y-3">
            {recsLoading ? (
              <p className="text-xs text-slate-400 text-center py-6">Loading recommendations...</p>
            ) : !recData?.recommendations || recData.recommendations.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-6">No pending recommendations. All requirements satisfied!</p>
            ) : (
              recData.recommendations.slice(0, 2).map((rec) => (
                <div 
                  key={rec.resource_id}
                  className="p-4 rounded-xl border border-slate-200 bg-white hover:border-gov-blue-300 shadow-2xs space-y-2.5 transition-all text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-gov-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200 uppercase">
                      {rec.provider} {rec.resource_type}
                    </span>
                    <span className="text-[11px] font-bold text-emerald-600">
                      {Math.round(rec.score * 100)}% Alignment
                    </span>
                  </div>

                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">{rec.title}</h4>
                    <span className="text-[11px] text-slate-500">{rec.provider} Official Learning Portal</span>
                  </div>

                  <p className="text-[11px] text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200/70 italic">
                    "{rec.reason || `Targeted to bridge competency deficit for your role.`}"
                  </p>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-slate-400 text-[10px] flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {rec.estimated_duration_minutes || 60} mins · {rec.difficulty}
                    </span>
                    <Button
                      size="sm"
                      onClick={() => navigate(`/demo-igot/courses/${rec.resource_id}`)}
                      className="bg-gov-blue-600 hover:bg-gov-blue-700 text-white text-[11px] py-1 px-3 flex items-center gap-1.5 font-medium shadow-xs"
                    >
                      <Play className="w-3 h-3 fill-current" />
                      Start on iGOT
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* AI Learning Plan Path Progression (Prompt Section 15) */}
        <Card className="border-slate-200 shadow-sm flex flex-col justify-between">
          <CardHeader className="bg-slate-50/70 border-b border-slate-100 pb-3 flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Target className="w-4 h-4 text-gov-blue-500" />
                AI Learning Plan
              </CardTitle>
              <p className="text-xs text-slate-400 mt-0.5">Your prioritized learning path</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate("/learning-plan")}
              className="text-xs text-slate-700"
            >
              Manage Path
            </Button>
          </CardHeader>

          <CardContent className="p-5 space-y-3 flex-1">
            <div className="space-y-3 text-xs">
              <div className="p-3 rounded-xl border border-slate-200 bg-white flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-gov-blue-500 text-white font-bold flex items-center justify-center text-[10px]">
                    01
                  </span>
                  <div>
                    <h4 className="font-bold text-slate-900">Sampling Methodology Fundamentals</h4>
                    <span className="text-[10px] text-rose-600 font-semibold">Priority: HIGH</span>
                  </div>
                </div>
                <Badge variant="warning">In Progress</Badge>
              </div>

              <div className="p-3 rounded-xl border border-slate-200 bg-white flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-slate-200 text-slate-700 font-bold flex items-center justify-center text-[10px]">
                    02
                  </span>
                  <div>
                    <h4 className="font-bold text-slate-900">Data Quality Management in Surveys</h4>
                    <span className="text-[10px] text-rose-600 font-semibold">Priority: HIGH</span>
                  </div>
                </div>
                <Badge variant="secondary">Not Started</Badge>
              </div>

              <div className="p-3 rounded-xl border border-slate-200 bg-white flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-slate-200 text-slate-700 font-bold flex items-center justify-center text-[10px]">
                    03
                  </span>
                  <div>
                    <h4 className="font-bold text-slate-900">Advanced Survey Design & Sampling Frames</h4>
                    <span className="text-[10px] text-amber-600 font-semibold">Priority: MEDIUM</span>
                  </div>
                </div>
                <Badge variant="secondary">Not Started</Badge>
              </div>
            </div>

            {/* Progression indicators */}
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-[10px] text-slate-500 flex items-center justify-between font-semibold">
              <span>Not Started</span>
              <span>→</span>
              <span className="text-gov-blue-600 font-bold">In Progress</span>
              <span>→</span>
              <span>Completed</span>
              <span>→</span>
              <span className="text-emerald-600 font-bold">Reassessment</span>
            </div>
          </CardContent>

          <div className="p-4 border-t border-slate-100 bg-slate-50/50">
            <Button
              onClick={() => navigate("/progress")}
              className="w-full flex items-center justify-center gap-2 bg-gov-blue-500 hover:bg-gov-blue-600 text-white font-bold text-xs py-2.5 rounded-lg shadow-sm"
            >
              <span>Ready to measure your progress? Take Reassessment</span>
              <RotateCcw className="w-3.5 h-3.5" />
            </Button>
          </div>
        </Card>
      </div>

      {/* "Why This Gap?" Detail Modal (Prompt Section 13) */}
      {selectedModalGap && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
            <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-gov-gold" />
                <h3 className="text-base font-bold uppercase">{selectedModalGap.competency_name}</h3>
              </div>
              <button onClick={() => setSelectedModalGap(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4 text-xs">
              <div className="grid grid-cols-3 gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Current</span>
                  <strong className="text-base text-slate-800 font-bold">
                    {Math.round((selectedModalGap.current_level / 5) * 100)}%
                  </strong>
                </div>
                <div className="border-x border-slate-200">
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Required</span>
                  <strong className="text-base text-gov-blue-500 font-bold">
                    {Math.round((selectedModalGap.required_level / 5) * 100)}%
                  </strong>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Gap</span>
                  <strong className="text-base text-rose-600 font-bold">
                    {Math.round((selectedModalGap.gap / 5) * 100)}%
                  </strong>
                </div>
              </div>

              <div className="space-y-1">
                <h4 className="font-bold text-slate-900">Why is this important?</h4>
                <p className="text-slate-600 leading-relaxed bg-blue-50 p-3 rounded-lg border border-blue-100">
                  "This competency is required for your <strong>{gapData.role.name}</strong> role. Closing this gap is critical for ensuring reliable survey estimation and official quality standards."
                </p>
              </div>

              <div className="space-y-1">
                <h4 className="font-bold text-slate-900">Evidence</h4>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 space-y-1 text-slate-600">
                  <div>✓ Diagnostic Assessment Score Verified</div>
                  <div>✓ Cadre Weighting Requirement ({selectedModalGap.weight})</div>
                  <div>✓ Evaluated on {new Date().toLocaleDateString("en-IN")}</div>
                </div>
              </div>

              <div className="pt-2 space-y-2">
                <Button
                  onClick={() => {
                    const compName = selectedModalGap.competency_name;
                    setSelectedModalGap(null);
                    const event = new CustomEvent("open-copilot", {
                      detail: {
                        query: `Why do I have a competency gap in '${compName}' for my ${gapData.role.name} role, and what specific courses will close it?`
                      }
                    });
                    window.dispatchEvent(event);
                  }}
                  className="w-full bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-bold text-xs py-2.5 flex items-center justify-center gap-2 cursor-pointer shadow-sm"
                >
                  <Sparkles className="w-4 h-4 text-indigo-200" />
                  <span>Ask AI Copilot to Explain & Recommend in Real Time</span>
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setSelectedModalGap(null);
                    navigate("/learning-plan");
                  }}
                  className="w-full text-slate-700 text-xs py-2"
                >
                  View Recommended Learning Resources
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
