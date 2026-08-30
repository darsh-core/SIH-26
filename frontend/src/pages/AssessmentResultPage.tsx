import React from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { useMutation, useQueryClient } from "@tanstack/react-query"
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
  Award, 
  TrendingUp, 
  RotateCw, 
  CheckCircle, 
  ChevronRight,
  ShieldCheck
} from "lucide-react"

import { useAuthStore } from "../store/authStore"
import { recommendationApi } from "../services/recommendationApi"
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from "../components/ui/Primitives"

export const AssessmentResultPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const userId = user?.id || "";

  // Read response state or fallback to seeded demo values
  const resultData = location.state?.result || {
    attempt_id: "demo-attempt",
    score: 84.0,
    passed: true,
    accuracy_by_competency: {
      "Sampling Methodology": 0.84
    },
    levels_updated: {
      "STAT_SAMPLING": {
        before: 2.3,
        after: 3.6,
        gained: 1.3,
        required: 4.0 // added for visual reference
      }
    }
  };

  const score = resultData.score;
  const passed = resultData.passed;

  // Extract competency updates info
  const updates = Object.entries(resultData.levels_updated).map(([code, val]: [string, any]) => ({
    code,
    before: val.before,
    after: val.after,
    gained: val.gained,
    required: val.required || 4.0
  }));

  // Prepare chart visual data
  const chartData = updates.map(u => ([
    {
      stage: "Before Quiz",
      "Current Level": u.before,
      "Required Level": u.required
    },
    {
      stage: "After Quiz",
      "Current Level": u.after,
      "Required Level": u.required
    }
  ])).flat();

  // 1. Refresh Recommendations mutation
  const refreshMutation = useMutation({
    mutationFn: () => recommendationApi.refreshRecommendations(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recommendations"] });
      queryClient.invalidateQueries({ queryKey: ["competency-gaps"] });
      queryClient.invalidateQueries({ queryKey: ["recommendations-preview"] });
      navigate("/recommendations");
    }
  });

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header banner */}
      <div className="text-center py-6 border-b border-slate-200">
        <ShieldCheck className="mx-auto h-14 w-14 text-emerald-500 stroke-[1.5]" />
        <h1 className="text-2xl font-bold text-slate-950 mt-3">Assessment Submitted Successfully</h1>
        <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-1">Audit verification processed</p>
      </div>

      {/* Main Score Widget */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Card className="border-emerald-100 bg-emerald-50/10">
          <CardContent className="p-6 text-center space-y-2">
            <span className="text-5xl font-extrabold text-emerald-600 tracking-tight">{Math.round(score)}%</span>
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Attempt Score</h4>
            <Badge variant="success" className="bg-emerald-100 text-emerald-800">
              {passed ? "PASSED CHECKPOINT" : "COMPLETED"}
            </Badge>
          </CardContent>
        </Card>

        <Card className="border-gov-blue-100 bg-gov-blue-50/10 flex flex-col justify-center p-6 text-center">
          <CardContent className="p-0 space-y-1">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Audited impact</h4>
            {updates.map(u => (
              <div key={u.code} className="space-y-1">
                <span className="text-sm font-extrabold text-slate-800 block">{u.code}</span>
                <span className="text-xs text-slate-600 block">
                  Level upgraded from <strong className="text-slate-800 font-bold">{u.before}</strong> to <strong className="text-emerald-600 font-bold">{u.after}</strong>
                </span>
                <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block mt-1">
                  +{u.gained.toFixed(1)} Level Gain
                </span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Before / After Gap Comparison visualization */}
      {updates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Competency Gap Improvement Chart</CardTitle>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 5]} ticks={[0, 1, 2, 3, 4, 5]} />
                  <YAxis dataKey="stage" type="category" width={100} tick={{ fill: "#475569", fontSize: 10, fontStyle: "normal", fontWeight: 500 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Current Level" fill="#829ab1" barSize={15} radius={[0, 4, 4, 0]} />
                  <Bar dataKey="Required Level" fill="#102a43" barSize={15} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-6 border-t border-slate-100 pt-4 text-center text-xs leading-relaxed text-slate-600 px-4">
              {updates.map(u => {
                const beforeGap = u.required - u.before;
                const afterGap = Math.max(0.0, u.required - u.after);
                return (
                  <p key={u.code}>
                    Your competency gap in <strong>{u.code}</strong> has successfully reduced from 
                    <span className="text-rose-600 font-bold mx-1">-{beforeGap.toFixed(1)}</span> to 
                    <span className="text-emerald-600 font-bold mx-1">-{afterGap.toFixed(1)}</span>.
                  </p>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* CTA Refresh Block */}
      <Card className="border-dashed border-gov-blue-200 bg-gov-blue-50/5">
        <CardContent className="p-6 text-center space-y-4">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-800">Adaptive Recommendations refresh</h3>
            <p className="text-xs text-slate-500 leading-normal">
              Recalculate personalized matching catalog to reflect your newly updated competency levels.
            </p>
          </div>
          <Button 
            variant="primary" 
            className="w-full py-2.5 font-bold"
            onClick={() => refreshMutation.mutate()}
            isLoading={refreshMutation.isPending}
          >
            <RotateCw className="h-4 w-4 mr-2" />
            Refresh Recommendations
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
