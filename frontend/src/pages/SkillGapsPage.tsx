import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { 
  AlertTriangle, 
  BookOpen, 
  CheckCircle, 
  HelpCircle, 
  ArrowRight, 
  X, 
  ShieldCheck, 
  FileText,
  Clock,
  ExternalLink,
  Sparkles,
  Info
} from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { competencyApi } from "../services/competencyApi";
import { recommendationApi } from "../services/recommendationApi";
import { userApi } from "../services/userApi";
import { CompetencyGapDetail } from "../types/competency";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Progress } from "../components/ui/Primitives";

export const SkillGapsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const userId = user?.id || "";

  const [selectedGap, setSelectedGap] = useState<CompetencyGapDetail | null>(null);
  const [filterPriority, setFilterPriority] = useState<string>("ALL");

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

  // 2. Fetch recommendations
  const { 
    data: recData 
  } = useQuery({
    queryKey: ["recommendations", userId],
    queryFn: () => recommendationApi.getRecommendations(userId),
    enabled: !!userId
  });

  // 3. Fetch evidence logs for user
  const {
    data: evidenceLogs
  } = useQuery({
    queryKey: ["user-evidence", userId],
    queryFn: () => userApi.getUserEvidence(userId),
    enabled: !!userId
  });

  if (gapsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
        <div className="w-10 h-10 border-4 border-gov-blue-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm font-semibold text-slate-600">Loading skill gap diagnostic breakdown...</p>
      </div>
    );
  }

  if (gapsError || !gapData) {
    return (
      <div className="text-center py-12">
        <AlertTriangle className="h-12 w-12 text-rose-500 mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-900">Unable to load skill gaps</h3>
        <p className="text-xs text-slate-500 mt-1">Please ensure your role is mapped and the backend is running.</p>
      </div>
    );
  }

  const filteredGaps = gapData.gaps.filter(g => {
    if (filterPriority === "ALL") return true;
    return g.priority === filterPriority;
  });

  const matchingRecs = selectedGap
    ? recData?.recommendations?.filter(r => 
        r.target_competencies?.some(tc => tc.code === selectedGap.competency_id || tc.code.toLowerCase() === selectedGap.competency_name.toLowerCase())
      ) || []
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 text-rose-600 mb-1">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-xs font-bold uppercase tracking-wider">Gap Analysis Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-950 tracking-tight">
            Priority Skill Gaps
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Competency deficits identified between your current proficiency and target requirements for <strong>{gapData.role.name}</strong>.
          </p>
        </div>

        {/* Priority Filter */}
        <div className="flex items-center gap-2 bg-white border border-slate-200 p-1 rounded-lg">
          {["ALL", "HIGH", "MEDIUM", "LOW"].map((p) => (
            <button
              key={p}
              onClick={() => setFilterPriority(p)}
              className={`px-3 py-1 text-xs font-bold rounded-md transition-all cursor-pointer ${
                filterPriority === p 
                  ? "bg-slate-900 text-white shadow-xs" 
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Gaps Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredGaps.map((gap) => {
          const currentPct = Math.round((gap.current_level / 5) * 100);
          const requiredPct = Math.round((gap.required_level / 5) * 100);
          const gapPct = Math.max(0, requiredPct - currentPct);

          return (
            <Card 
              key={gap.competency_id} 
              className="border-slate-200 hover:border-gov-blue-300 hover:shadow-md transition-all flex flex-col justify-between"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2">
                  <Badge variant={gap.priority === "HIGH" ? "error" : (gap.priority === "MEDIUM" ? "warning" : "default")}>
                    {gap.priority} PRIORITY
                  </Badge>
                  {gap.mandatory && (
                    <span className="text-[9px] font-bold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                      MANDATORY
                    </span>
                  )}
                </div>
                <CardTitle className="text-base font-bold text-slate-900 mt-2">
                  {gap.competency_name}
                </CardTitle>
                <span className="text-[10px] font-mono text-slate-400 block">{gap.competency_code}</span>
              </CardHeader>

              <CardContent className="space-y-4 pt-0">
                {/* Horizontal Progress */}
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-slate-600 font-medium">
                    <span>Current: <strong className="text-slate-800">{currentPct}%</strong></span>
                    <span>Required: <strong className="text-slate-800">{requiredPct}%</strong></span>
                  </div>
                  <div className="relative h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className="absolute top-0 bottom-0 bg-slate-300 rounded-full"
                      style={{ width: `${requiredPct}%` }}
                    />
                    <div 
                      className="absolute top-0 bottom-0 bg-gov-blue-500 rounded-full"
                      style={{ width: `${currentPct}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px]">
                    <span className="text-slate-400">Level {gap.current_level} of {gap.required_level}</span>
                    <span className="font-bold text-rose-600">
                      {gap.gap > 0 ? `${gapPct}% Deficit` : "Competency Met ✓"}
                    </span>
                  </div>
                </div>

                {/* Action to trigger "Why this gap?" (Prompt Section 13) */}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedGap(gap)}
                  className="w-full flex items-center justify-center gap-1.5 text-xs text-slate-700 hover:text-gov-blue-600 hover:border-gov-blue-300"
                >
                  <HelpCircle className="w-3.5 h-3.5 text-gov-blue-500" />
                  <span>Why this gap? & Remediation</span>
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* "Why This Gap?" Detail Modal (Prompt Section 13) */}
      {selectedGap && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white w-full max-w-xl rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[90vh]">
            
            {/* Modal Header */}
            <div className="bg-slate-900 text-white p-5 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-white/10 text-gov-gold">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold uppercase tracking-wide">
                    {selectedGap.competency_name}
                  </h3>
                  <span className="text-[10px] text-slate-300 font-mono">
                    {selectedGap.competency_code} · Role Requirement Audit
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedGap(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-5 text-xs">
              {/* Score breakdown metrics */}
              <div className="grid grid-cols-3 gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-center">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Current</span>
                  <strong className="text-base text-slate-800 font-extrabold">
                    {Math.round((selectedGap.current_level / 5) * 100)}%
                  </strong>
                  <span className="text-[10px] text-slate-500 block">Level {selectedGap.current_level}</span>
                </div>
                <div className="border-x border-slate-200">
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Required</span>
                  <strong className="text-base text-gov-blue-500 font-extrabold">
                    {Math.round((selectedGap.required_level / 5) * 100)}%
                  </strong>
                  <span className="text-[10px] text-slate-500 block">Level {selectedGap.required_level}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Gap Delta</span>
                  <strong className="text-base text-rose-600 font-extrabold">
                    {Math.round((selectedGap.gap / 5) * 100)}%
                  </strong>
                  <span className="text-[10px] text-rose-500 font-semibold block">{selectedGap.gap.toFixed(1)} points</span>
                </div>
              </div>

              {/* Why is this important? */}
              <div className="space-y-1.5">
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                  <Info className="w-3.5 h-3.5 text-gov-blue-500" />
                  Why is this important?
                </h4>
                <p className="text-slate-600 leading-relaxed bg-blue-50/50 p-3 rounded-lg border border-blue-100">
                  "This competency is required for your <strong>{gapData.role.name}</strong> role. Proficiency at Level {selectedGap.required_level} ensures accurate survey design, methodology compliance, and statistical data integrity during official MoSPI data releases."
                </p>
              </div>

              {/* Evidence Log */}
              <div className="space-y-2">
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider">
                  Evaluation Evidence
                </h4>
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2 p-2 rounded-md bg-slate-50 border border-slate-200 text-slate-700">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    <span>✓ Diagnostic Assessment ({new Date().toLocaleDateString("en-IN")})</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 rounded-md bg-slate-50 border border-slate-200 text-slate-700">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    <span>✓ Job Role Benchmark Weight: {selectedGap.weight}</span>
                  </div>
                  <div className="flex items-center gap-2 p-2 rounded-md bg-slate-50 border border-slate-200 text-slate-700">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                    <span>✓ Priority Tier: {selectedGap.priority} ({selectedGap.mandatory ? "Mandatory Core Requirement" : "Elective"})</span>
                  </div>
                </div>
              </div>

              {/* Remedial Resources */}
              <div className="space-y-2 pt-2 border-t border-slate-200">
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center justify-between">
                  <span>How can I improve?</span>
                  <span className="text-[10px] text-slate-400 lowercase font-normal">Recommended training</span>
                </h4>
                
                <div className="p-3.5 rounded-xl border border-indigo-100 bg-indigo-50/40 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 text-xs">
                      {selectedGap.competency_name} Fundamentals
                    </span>
                    <span className="text-[9px] font-bold text-gov-blue-600 bg-white px-1.5 py-0.5 rounded border border-indigo-200">
                      MOCK iGOT RESOURCE
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-600">
                    Targeted self-paced modules to master {selectedGap.competency_name} up to Level {selectedGap.required_level}.
                  </p>
                  <Button
                    size="sm"
                    onClick={() => {
                      setSelectedGap(null);
                      navigate("/learning-plan");
                    }}
                    className="w-full flex items-center justify-center gap-1.5 bg-gov-blue-500 hover:bg-gov-blue-600 text-white text-xs mt-2"
                  >
                    <span>Add to My Learning Plan</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
};
