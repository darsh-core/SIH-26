import React from "react"
import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from "recharts"
import { 
  AlertTriangle, 
  Award, 
  BookOpen, 
  CheckCircle, 
  ArrowRight, 
  Activity 
} from "lucide-react"

import { useAuthStore } from "../store/authStore"
import { competencyApi } from "../services/competencyApi"
import { recommendationApi } from "../services/recommendationApi"
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Progress } from "../components/ui/Primitives"

export const DashboardPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  
  const userId = user?.id || "";

  // 1. Fetch competency gaps
  const { 
    data: gapData, 
    isLoading: gapsLoading, 
    error: gapsError 
  } = useQuery({
    queryKey: ["competency-gaps", userId],
    queryFn: () => competencyApi.getCompetencyGaps(userId),
    enabled: !!userId
  });

  // 2. Fetch top 3 recommendations
  const { 
    data: recData, 
    isLoading: recsLoading 
  } = useQuery({
    queryKey: ["recommendations-preview", userId],
    queryFn: () => recommendationApi.getRecommendations(userId, { limit: 3 }),
    enabled: !!userId
  });

  if (gapsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <svg className="animate-spin h-10 w-10 text-gov-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span className="text-sm font-semibold text-slate-500">Calculating your competency profile...</span>
      </div>
    );
  }

  if (gapsError || !gapData) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-rose-500 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-900">Unable to load competency gaps</h3>
        <p className="text-sm text-slate-500 mt-2">Make sure the backend dev server is running on port 8000.</p>
      </div>
    );
  }

  // Count priorities
  const highGaps = gapData.gaps.filter(g => g.priority === "HIGH").length;
  const mediumGaps = gapData.gaps.filter(g => g.priority === "MEDIUM").length;
  
  // Format data for Recharts
  const chartData = gapData.gaps.map(g => ({
    name: g.competency_name.length > 20 ? g.competency_name.slice(0, 20) + "..." : g.competency_name,
    "Current Level": g.current_level,
    "Required Level": g.required_level
  }));

  // Find top priority gaps for the widgets list
  const priorityGaps = gapData.gaps
    .filter(g => g.gap > 0)
    .sort((a, b) => b.gap - a.gap);

  return (
    <div className="space-y-8">
      {/* Header Block */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-950">Good morning, {user?.profile?.first_name || "Ramesh"}</h1>
          <p className="text-sm text-slate-500 font-medium">
            {user?.profile?.designation || "Statistical Officer"} · EMP{user?.profile?.user_id?.slice(0, 4) || "001"}
          </p>
        </div>
        <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg px-4 py-2 shadow-xs">
          <Activity className="h-5 w-5 text-emerald-500" />
          <div>
            <span className="text-[10px] text-slate-400 font-semibold block uppercase">Security clearance</span>
            <span className="text-xs font-bold text-slate-700">Official Access Granted</span>
          </div>
        </div>
      </div>

      {/* Hero Performance Block */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Overall Readiness Gauge */}
        <Card className="lg:col-span-1 border-gov-blue-100 bg-gov-blue-50/20 flex flex-col justify-between">
          <CardHeader>
            <CardTitle>Role Readiness Index</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center py-6">
            <div className="relative flex items-center justify-center">
              {/* Circular Gauge visualization */}
              <svg className="w-36 h-36 transform -rotate-90">
                <circle 
                  cx="72" 
                  cy="72" 
                  r="60" 
                  className="stroke-slate-200" 
                  strokeWidth="10" 
                  fill="transparent" 
                />
                <circle 
                  cx="72" 
                  cy="72" 
                  r="60" 
                  className="stroke-gov-blue-500 transition-all duration-1000 ease-out" 
                  strokeWidth="10" 
                  fill="transparent" 
                  strokeDasharray={2 * Math.PI * 60}
                  strokeDashoffset={2 * Math.PI * 60 * (1 - gapData.overall_readiness / 100)}
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-3xl font-extrabold text-gov-blue-500 tracking-tight">{gapData.overall_readiness}%</span>
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider">Ready</span>
              </div>
            </div>
            <p className="text-center text-xs text-slate-500 mt-6 max-w-xs leading-normal">
              Based on assessed competency weightage mappings for the **{gapData.role.name}** designation.
            </p>
          </CardContent>
        </Card>

        {/* Right: Metrics Grid */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card className="border-red-100">
            <CardContent className="p-6 flex items-start gap-4">
              <div className="p-3 bg-red-50 text-red-600 rounded-lg border border-red-100">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div>
                <span className="text-2xl font-bold text-slate-900">{highGaps}</span>
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">High Priority Gaps</h4>
                <p className="text-[10px] text-slate-400 mt-2 leading-relaxed">Gaps targeting mandatory role requirements.</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-amber-100">
            <CardContent className="p-6 flex items-start gap-4">
              <div className="p-3 bg-amber-50 text-amber-600 rounded-lg border border-amber-100">
                <Activity className="h-6 w-6" />
              </div>
              <div>
                <span className="text-2xl font-bold text-slate-900">{mediumGaps}</span>
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Medium Priority Gaps</h4>
                <p className="text-[10px] text-slate-400 mt-2 leading-relaxed">Secondary required competencies gaps.</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-emerald-100">
            <CardContent className="p-6 flex items-start gap-4">
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg border border-emerald-100">
                <CheckCircle className="h-6 w-6" />
              </div>
              <div>
                <span className="text-2xl font-bold text-slate-900">{gapData.gaps.length}</span>
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Skills Assessed</h4>
                <p className="text-[10px] text-slate-400 mt-2 leading-relaxed">Total competencies mapped to your profile.</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-gov-blue-100">
            <CardContent className="p-6 flex items-start gap-4">
              <div className="p-3 bg-gov-blue-50 text-gov-blue-600 rounded-lg border border-gov-blue-100">
                <BookOpen className="h-6 w-6" />
              </div>
              <div>
                {/* Simulated learning completion metrics */}
                <span className="text-2xl font-bold text-slate-900">45%</span>
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mt-1">Learning Progress</h4>
                <p className="text-[10px] text-slate-400 mt-2 leading-relaxed">Courses completed on iGOT/NSSTA plans.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Competency Gap Comparison Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Competency Gap Analysis (Current vs Required)</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" domain={[0, 5]} ticks={[0, 1, 2, 3, 4, 5]} />
                <YAxis dataKey="name" type="category" width={120} tick={{ fill: "#475569", fontSize: 10, fontWeight: 500 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="Current Level" fill="#829ab1" barSize={12} radius={[0, 4, 4, 0]} />
                <Bar dataKey="Required Level" fill="#102a43" barSize={12} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Priority Gaps & Recommendations Preview split row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Priority Gaps */}
        <Card>
          <CardHeader>
            <CardTitle>Priority Skill Gaps</CardTitle>
          </CardHeader>
          <CardContent className="divide-y divide-slate-100 p-0">
            {priorityGaps.length === 0 ? (
              <div className="p-6 text-center text-slate-500 text-sm">
                No active competency gaps found! You are fully prepared for this role.
              </div>
            ) : (
              priorityGaps.map(g => (
                <div key={g.competency_id} className="p-6 flex items-center justify-between gap-4">
                  <div className="space-y-1 min-w-0">
                    <h4 className="text-sm font-semibold text-slate-900 truncate">{g.competency_name}</h4>
                    <div className="flex gap-4 text-xs text-slate-500">
                      <span>Current: <strong className="text-slate-800">{g.current_level}</strong></span>
                      <span>Required: <strong className="text-slate-800">{g.required_level}</strong></span>
                      <span>Gap: <strong className="text-rose-600">{g.gap.toFixed(1)}</strong></span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <Badge variant={g.priority === "HIGH" ? "error" : g.priority === "MEDIUM" ? "warning" : "info"}>
                      {g.priority}
                    </Badge>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => navigate(`/recommendations?competency=${g.competency_code}`)}
                    >
                      View recommendations
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Recommendations Preview */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Top Recommendations</CardTitle>
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-gov-blue-500 hover:text-gov-blue-600 font-semibold"
              onClick={() => navigate("/recommendations")}
            >
              View all <ArrowRight className="h-4 w-4 ml-1 inline" />
            </Button>
          </CardHeader>
          <CardContent className="divide-y divide-slate-100 p-0">
            {recsLoading ? (
              <div className="p-6 text-center text-slate-500 text-xs">Loading recommendations...</div>
            ) : !recData || recData.recommendations.length === 0 ? (
              <div className="p-6 text-center text-slate-500 text-sm">No recommendations available. Please refresh.</div>
            ) : (
              recData.recommendations.map(r => (
                <div key={r.resource_id} className="p-6 space-y-3">
                  <div className="flex justify-between items-start gap-4">
                    <div className="min-w-0">
                      <h4 className="text-sm font-semibold text-slate-900 truncate leading-snug">{r.title}</h4>
                      <div className="flex gap-2 items-center mt-1">
                        <Badge variant="secondary" className="px-1.5 py-0">
                          {r.provider}
                        </Badge>
                        <span className="text-[10px] text-slate-400 font-medium">({r.difficulty} · {r.estimated_duration_minutes}m)</span>
                      </div>
                    </div>
                    <span className="text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full shrink-0">
                      {Math.round(r.score)}% MATCH
                    </span>
                  </div>
                  
                  <p className="text-xs text-slate-500 leading-normal line-clamp-2">
                    {r.reason}
                  </p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
