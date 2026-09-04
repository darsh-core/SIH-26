import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { 
  Award, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowRight, 
  BookOpen, 
  Layers, 
  RotateCcw,
  TrendingUp,
  Building,
  Target
} from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { competencyApi } from "../services/competencyApi";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from "../components/ui/Primitives";

export const RoleReadinessPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const userId = user?.id || "";

  const { 
    data: gapData, 
    isLoading, 
    error 
  } = useQuery({
    queryKey: ["competency-gaps", userId],
    queryFn: () => competencyApi.getCompetencyGaps(userId),
    enabled: !!userId
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-gov-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-semibold text-slate-600">Calculating role readiness index...</p>
      </div>
    );
  }

  if (error || !gapData) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-900">Unable to load Role Readiness</h3>
        <p className="text-xs text-slate-500 mt-1">Please ensure your job role is mapped.</p>
      </div>
    );
  }

  const readiness = gapData.overall_readiness;
  const strongAreas = gapData.gaps.filter(g => g.gap <= 0.2);
  const devAreas = gapData.gaps.filter(g => g.gap > 0.2).sort((a, b) => b.gap - a.gap);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-200 pb-5">
        <div className="flex items-center gap-2 text-gov-blue-600 mb-1">
          <Award className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider">Workforce Capability Benchmarking</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-950 tracking-tight">
          Role Readiness Assessment
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Evaluating organizational readiness against the official standards of <strong>{gapData.role.name}</strong>.
        </p>
      </div>

      {/* Role Summary Hero Banner */}
      <Card className="border-gov-blue-200 bg-gradient-to-r from-gov-blue-500 via-indigo-900 to-gov-blue-600 text-white shadow-lg">
        <CardContent className="p-6 sm:p-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
            {/* Left: Role Details */}
            <div className="md:col-span-2 space-y-3">
              <span className="text-xs font-bold uppercase tracking-wider text-gov-gold flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4" />
                Evaluated Role Track
              </span>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                {gapData.role.name}
              </h2>
              <div className="flex flex-wrap items-center gap-3 text-xs text-blue-100/90 font-medium">
                <span className="flex items-center gap-1">
                  <Building className="w-3.5 h-3.5" />
                  {user?.profile?.department || "Agricultural Statistics Division"}
                </span>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Layers className="w-3.5 h-3.5" />
                  {gapData.gaps.length} Competencies Evaluated
                </span>
              </div>
            </div>

            {/* Right: Readiness Score Badge */}
            <div className="p-4 rounded-xl bg-white/10 backdrop-blur-sm border border-white/20 text-center flex flex-col items-center justify-center">
              <span className="text-[10px] uppercase font-extrabold text-blue-100 tracking-wider">
                Overall Role Readiness
              </span>
              <span className="text-4xl sm:text-5xl font-extrabold text-gov-gold tracking-tight my-1">
                {readiness}%
              </span>
              <Badge variant={readiness >= 80 ? "success" : (readiness >= 55 ? "warning" : "error")}>
                {readiness >= 80 ? "ROLE READY" : (readiness >= 55 ? "DEVELOPING" : "NEEDS DEVELOPMENT")}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strong Areas vs Development Areas (Prompt Section 20) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strong Areas */}
        <Card className="border-emerald-200">
          <CardHeader className="bg-emerald-50/50 border-b border-emerald-100 pb-3">
            <CardTitle className="text-base text-emerald-950 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              Strong Areas (Requirement Met)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-3">
            {strongAreas.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No competencies currently exceed the baseline.</p>
            ) : (
              strongAreas.map((s, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-emerald-50/30 border border-emerald-100 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-emerald-600 font-bold">✓</span>
                    <strong className="text-slate-900">{s.competency_name}</strong>
                  </div>
                  <span className="font-bold text-emerald-700">
                    {Math.round((s.current_level / 5) * 100)}% (Level {s.current_level})
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Development Areas */}
        <Card className="border-rose-200">
          <CardHeader className="bg-rose-50/50 border-b border-rose-100 pb-3">
            <CardTitle className="text-base text-rose-950 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
              Development Areas (Competency Deficit)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-3">
            {devAreas.length === 0 ? (
              <p className="text-xs text-emerald-600 font-semibold">All competency requirements are fully satisfied!</p>
            ) : (
              devAreas.map((d, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-rose-50/30 border border-rose-100 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-rose-600 font-bold">⚠</span>
                    <strong className="text-slate-900">{d.competency_name}</strong>
                  </div>
                  <span className="font-bold text-rose-700">
                    {Math.round((d.gap / 5) * 100)}% Gap ({d.priority})
                  </span>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Actions to Improve Role Readiness (Prompt Section 20) */}
      <Card className="border-slate-200 shadow-sm">
        <CardHeader className="bg-slate-50/70 border-b border-slate-100">
          <CardTitle className="text-base flex items-center gap-2 text-slate-900">
            <Target className="w-5 h-5 text-gov-blue-500" />
            Actions to Improve Role Readiness
          </CardTitle>
        </CardHeader>

        <CardContent className="p-6 space-y-3">
          {devAreas.slice(0, 3).map((area, idx) => (
            <div 
              key={idx}
              className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-slate-200 bg-white hover:border-gov-blue-300 transition-all text-xs"
            >
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center shrink-0">
                  {idx + 1}
                </span>
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">
                    Complete {area.competency_name} Fundamentals
                  </h4>
                  <p className="text-slate-500 mt-0.5">
                    Target gap: {Math.round((area.gap / 5) * 100)} percentage points. Recommended iGOT/NSSTA curriculum.
                  </p>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate("/learning-plan")}
                className="text-xs text-gov-blue-600 border-gov-blue-200 hover:bg-gov-blue-50 shrink-0"
              >
                <span>View Course</span>
                <ArrowRight className="w-3.5 h-3.5 ml-1" />
              </Button>
            </div>
          ))}

          {/* Action to take reassessment */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-indigo-200 bg-indigo-50/40 text-xs mt-2">
            <div className="flex items-center gap-3">
              <span className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center shrink-0">
                ★
              </span>
              <div>
                <h4 className="font-bold text-indigo-950 text-sm">
                  Take Reassessment to Verify Improvement
                </h4>
                <p className="text-indigo-800/80 mt-0.5">
                  Re-evaluate your skills and automatically update your official Role Readiness score.
                </p>
              </div>
            </div>

            <Button
              size="sm"
              onClick={() => navigate("/progress")}
              className="bg-gov-blue-500 hover:bg-gov-blue-600 text-white text-xs shrink-0"
            >
              <span>Take Reassessment</span>
              <RotateCcw className="w-3.5 h-3.5 ml-1" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
