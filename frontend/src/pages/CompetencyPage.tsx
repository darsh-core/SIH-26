import React, { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { 
  Award, 
  BookOpen, 
  CheckCircle, 
  HelpCircle, 
  Map, 
  ShieldAlert, 
  ArrowRight,
  TrendingDown,
  ChevronRight
} from "lucide-react"

import { useAuthStore } from "../store/authStore"
import { competencyApi } from "../services/competencyApi"
import { recommendationApi } from "../services/recommendationApi"
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Progress } from "../components/ui/Primitives"

export const CompetencyPage = () => {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const userId = user?.id || "";
  const [selectedCompId, setSelectedCompId] = useState<string | null>(null);

  // 1. Fetch user competencies (includes current levels)
  const { 
    data: userComps, 
    isLoading: compsLoading, 
    error: compsError 
  } = useQuery({
    queryKey: ["user-competencies", userId],
    queryFn: () => competencyApi.getUserCompetencies(userId),
    enabled: !!userId
  });

  // 2. Fetch competency gaps (to get required levels and gaps)
  const { 
    data: gapData 
  } = useQuery({
    queryKey: ["competency-gaps", userId],
    queryFn: () => competencyApi.getCompetencyGaps(userId),
    enabled: !!userId
  });

  // 3. Fetch specific competency-specific recommendations if a competency is selected
  const selectedUserComp = userComps?.find(uc => uc.competency_id === selectedCompId);
  
  const { 
    data: compRecs, 
    isLoading: recsLoading 
  } = useQuery({
    queryKey: ["comp-specific-recommendations", userId, selectedCompId],
    queryFn: () => recommendationApi.getCompetencyRecommendations(userId, selectedCompId!),
    enabled: !!userId && !!selectedCompId
  });

  if (compsLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <svg className="animate-spin h-10 w-10 text-gov-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span className="text-sm font-semibold text-slate-500">Loading competency profiles...</span>
      </div>
    );
  }

  if (compsError || !userComps) {
    return (
      <div className="text-center py-12">
        <ShieldAlert className="h-12 w-12 text-rose-500 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-900">Error loading competency profile</h3>
        <p className="text-sm text-slate-500 mt-2">Try logging in again or verify the backend server connection.</p>
      </div>
    );
  }

  // Create lookup for gap priority and required levels
  const gapMap = gapData ? Object.fromEntries(gapData.gaps.map(g => [g.competency_id, g])) : {};

  // Group competencies by domain framework (STATISTICAL, TECHNICAL, DIGITAL_GOVERNANCE, BEHAVIOURAL)
  const domains: Record<string, typeof userComps> = {
    STATISTICAL: [],
    TECHNICAL: [],
    DIGITAL_GOVERNANCE: [],
    BEHAVIOURAL: []
  };

  userComps.forEach(uc => {
    // Determine domain from competency code prefix or default to STATISTICAL
    const code = uc.competency?.code || "";
    if (code.startsWith("STAT")) domains.STATISTICAL.push(uc);
    else if (code.startsWith("TECH")) domains.TECHNICAL.push(uc);
    else if (code.startsWith("GOV")) domains.DIGITAL_GOVERNANCE.push(uc);
    else domains.BEHAVIOURAL.push(uc);
  });

  const domainNames = {
    STATISTICAL: "Statistical Domain",
    TECHNICAL: "Technical & Computational Domain",
    DIGITAL_GOVERNANCE: "Digital Governance & Security",
    BEHAVIOURAL: "Behavioural & Leadership"
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-950">My Competency Profile</h1>
        <p className="text-sm text-slate-500">
          Detailed metrics, framework mappings, and verified audit logs for your mapped skills.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
        {/* Left: Grouped Competency List */}
        <div className="xl:col-span-2 space-y-6">
          {Object.entries(domains).map(([domainKey, list]) => {
            if (list.length === 0) return null;
            
            return (
              <Card key={domainKey} className="overflow-hidden">
                <CardHeader className="bg-slate-50 border-b border-slate-200 py-3.5">
                  <CardTitle className="text-xs font-bold uppercase tracking-wider text-gov-blue-500">
                    {domainNames[domainKey as keyof typeof domainNames]}
                  </CardTitle>
                </CardHeader>
                <CardContent className="divide-y divide-slate-100 p-0">
                  {list.map(uc => {
                    const gapInfo = gapMap[uc.competency_id];
                    const gap = gapInfo ? gapInfo.gap : 0.0;
                    const req = gapInfo ? gapInfo.required_level : 3.0;
                    const priority = gapInfo ? gapInfo.priority : "NONE";
                    const isSelected = selectedCompId === uc.competency_id;
                    
                    return (
                      <div 
                        key={uc.id} 
                        onClick={() => setSelectedCompId(uc.competency_id)}
                        className={`p-5 flex items-center justify-between gap-4 cursor-pointer hover:bg-slate-50 transition-colors ${isSelected ? "bg-gov-blue-50/30 border-r-4 border-r-gov-blue-500" : ""}`}
                      >
                        <div className="space-y-1 min-w-0">
                          <h4 className="text-sm font-semibold text-slate-900 truncate">{uc.competency?.name}</h4>
                          <span className="text-[10px] text-slate-400 font-bold tracking-wider block uppercase">{uc.competency?.code}</span>
                        </div>

                        <div className="flex items-center gap-6 shrink-0">
                          <div className="flex gap-4 text-xs font-medium text-slate-500">
                            <span>Current: <strong className="text-slate-800">{uc.current_level}</strong></span>
                            <span>Required: <strong className="text-slate-800">{req}</strong></span>
                            {gap > 0 ? (
                              <span className="text-rose-600 font-semibold">Gap: -{gap.toFixed(1)}</span>
                            ) : (
                              <span className="text-emerald-600 font-semibold">Ready</span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {gap > 0 ? (
                              <Badge variant={priority === "HIGH" ? "error" : "warning"}>{priority}</Badge>
                            ) : (
                              <Badge variant="success">Mastered</Badge>
                            )}
                            <ChevronRight className="h-4 w-4 text-slate-300" />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Right: Selected Competency Detail Sidebar */}
        <div className="xl:col-span-1">
          {selectedCompId && selectedUserComp ? (
            <Card className="sticky top-6 border-gov-blue-100 shadow-md">
              <CardHeader className="bg-gov-blue-500 text-white py-5">
                <CardTitle className="text-white text-sm font-bold tracking-tight">Competency Detail</CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-6">
                
                {/* Meta details */}
                <div className="space-y-1">
                  <h3 className="text-base font-extrabold text-slate-900 leading-snug">{selectedUserComp.competency?.name}</h3>
                  <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">{selectedUserComp.competency?.code}</span>
                </div>

                {/* Description */}
                <div>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Description</h4>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {selectedUserComp.competency?.description || "No competency description mapped."}
                  </p>
                </div>

                {/* Level indicators */}
                <div className="bg-slate-50 border border-slate-200/50 rounded-md p-4 space-y-3">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider border-b border-slate-100 pb-2">Status comparison</h4>
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-400 block font-medium">Current level</span>
                      <span className="text-base font-extrabold text-slate-800">{selectedUserComp.current_level} / 5.0</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block font-medium">Required level</span>
                      <span className="text-base font-extrabold text-slate-800">{gapMap[selectedCompId]?.required_level || 3.0} / 5.0</span>
                    </div>
                  </div>
                </div>

                {/* Level 1-5 framework preview */}
                <div>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Level definitions</h4>
                  <div className="space-y-2.5 text-[11px] leading-relaxed text-slate-600 border-l border-slate-200 pl-3">
                    <div>
                      <strong className="text-slate-800 font-bold block">Level 1: Basic Awareness</strong>
                      <span>Understands foundational definitions and principles.</span>
                    </div>
                    <div>
                      <strong className="text-slate-800 font-bold block">Level 2: Guided Application</strong>
                      <span>Executes tasks under supervision with basic tools.</span>
                    </div>
                    <div>
                      <strong className="text-slate-800 font-bold block">Level 3: Independent Application</strong>
                      <span>Coordinates standard processes independently.</span>
                    </div>
                    <div>
                      <strong className="text-slate-800 font-bold block">Level 4: Advanced Audit</strong>
                      <span>Audits quality control and resolves complex estimation anomalies.</span>
                    </div>
                    <div>
                      <strong className="text-slate-800 font-bold block">Level 5: Strategic Vision</strong>
                      <span>Formulates national frameworks and guidelines.</span>
                    </div>
                  </div>
                </div>

                {/* Evidence Certificates logged */}
                <div>
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Logged evidence & audits</h4>
                  {selectedUserComp.evidences && selectedUserComp.evidences.length > 0 ? (
                    <div className="space-y-3">
                      {selectedUserComp.evidences.map(ev => (
                        <div key={ev.id} className="border border-slate-200 rounded-md p-3 bg-slate-50/50 flex gap-2 items-start text-xs">
                          <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                          <div className="space-y-1">
                            <h5 className="font-bold text-slate-800 leading-tight">{ev.title}</h5>
                            <p className="text-[10px] text-slate-400 font-semibold uppercase">{ev.evidence_type} · {new Date(ev.created_at).toLocaleDateString()}</p>
                            {ev.description && <p className="text-[10px] text-slate-500 mt-1 leading-normal">{ev.description}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">No verification evidence certificates logged yet.</p>
                  )}
                </div>

                {/* specific Recommendations link */}
                <div className="pt-4 border-t border-slate-100">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Reaching required level</h4>
                  {recsLoading ? (
                    <span className="text-xs text-slate-400 italic">Finding courses...</span>
                  ) : compRecs && compRecs.length > 0 ? (
                    <div className="space-y-2">
                      <div className="text-xs font-semibold text-slate-700 bg-emerald-50 border border-emerald-100 rounded-md px-3 py-2 flex items-center justify-between">
                        <span>{compRecs[0].title}</span>
                        <span className="text-emerald-700 shrink-0 font-bold">{Math.round(compRecs[0].score)}% Match</span>
                      </div>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        className="w-full text-xs font-bold justify-center"
                        onClick={() => navigate(`/recommendations?competency=${selectedUserComp.competency?.code}`)}
                      >
                        All recommendations for this gap
                      </Button>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 leading-normal">
                      No active gap recommendations required. You have already mapped or exceeded the role requirements.
                    </p>
                  )}
                </div>

              </CardContent>
            </Card>
          ) : (
            <Card className="border-slate-200 border-dashed p-6 text-center text-slate-500 text-xs leading-normal">
              Select a competency from the list to view its description, level definitions, evidence records, and recommended courses.
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
