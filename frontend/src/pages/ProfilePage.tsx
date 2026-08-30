import React from "react"
import { useQuery } from "@tanstack/react-query"
import { 
  User, 
  Building, 
  Award, 
  History, 
  CheckCircle, 
  ShieldCheck,
  TrendingUp,
  FileText
} from "lucide-react"

import { useAuthStore } from "../store/authStore"
import { competencyApi } from "../services/competencyApi"
import { Card, CardContent, CardHeader, CardTitle, Badge, Progress } from "../components/ui/Primitives"

export const ProfilePage = () => {
  const { user } = useAuthStore();
  const userId = user?.id || "";

  // 1. Fetch competency gaps for role readiness comparison
  const { 
    data: gapData 
  } = useQuery({
    queryKey: ["competency-gaps", userId],
    queryFn: () => competencyApi.getCompetencyGaps(userId),
    enabled: !!userId
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-950">Employee Profile</h1>
        <p className="text-sm text-slate-500">Official security clearance and role competency details.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Card: Profile details */}
        <Card className="lg:col-span-1 border-slate-200">
          <CardHeader className="text-center py-6 border-b border-slate-100 bg-slate-50/20">
            <div className="w-20 h-20 rounded-full bg-gov-blue-100 flex items-center justify-center text-gov-blue-500 text-3xl font-extrabold mx-auto shadow-inner">
              {user?.profile?.first_name?.charAt(0) || "U"}
            </div>
            <h2 className="text-base font-bold text-slate-900 mt-4">
              {user?.profile?.first_name} {user?.profile?.last_name}
            </h2>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-1">
              EMP{user?.profile?.user_id?.slice(0, 4) || "001"}
            </p>
          </CardHeader>
          <CardContent className="p-6 divide-y divide-slate-100 text-xs">
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Designation:</span>
              <strong className="text-slate-800">{user?.profile?.designation || "Statistical Officer"}</strong>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Department:</span>
              <strong className="text-slate-800">{user?.profile?.department || "Field Surveys Division"}</strong>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Organization:</span>
              <strong className="text-slate-800">MoSPI, Govt of India</strong>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Target Role Track:</span>
              <strong className="text-gov-blue-500">{gapData?.role.name || "Statistical Officer"}</strong>
            </div>
          </CardContent>
        </Card>

        {/* Right Cards: Readiness Summary & Audit History */}
        <div className="lg:col-span-2 space-y-6">
          {/* Readiness Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Role Readiness Summary</CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-slate-50 border border-slate-200/50 rounded-lg p-5">
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Weighted Readiness Index</span>
                  <p className="text-3xl font-extrabold text-gov-blue-500 tracking-tight">{gapData?.overall_readiness || 72.4}%</p>
                </div>
                <div className="w-full sm:w-64 space-y-2">
                  <div className="flex justify-between text-xs text-slate-500 font-medium">
                    <span>Current Readiness Level</span>
                    <span>Target 100%</span>
                  </div>
                  <Progress value={gapData?.overall_readiness || 72.4} colorClassName="bg-gov-blue-500" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Audit History Card */}
          <Card>
            <CardHeader>
              <CardTitle>Assessment & Level Audit History</CardTitle>
            </CardHeader>
            <CardContent className="p-0 divide-y divide-slate-100">
              {/* Dummy history entries for visual verification */}
              <div className="p-6 flex items-start gap-4 text-xs">
                <div className="p-2 bg-emerald-50 text-emerald-600 rounded-md border border-emerald-100">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-slate-800 leading-snug">Sampling Methodology Core Assessment</h4>
                    <span className="text-[10px] text-slate-400 font-semibold">2 hours ago</span>
                  </div>
                  <p className="text-slate-500 leading-normal">
                    Verified score: <strong>84%</strong>. Competency <strong>STAT_SAMPLING</strong> upgraded from <strong>2.3</strong> to <strong>3.6</strong>.
                  </p>
                  <Badge variant="success" className="px-1.5 py-0">Verified Audit Log Created</Badge>
                </div>
              </div>

              <div className="p-6 flex items-start gap-4 text-xs">
                <div className="p-2 bg-slate-50 text-slate-400 rounded-md border border-slate-200">
                  <History className="h-5 w-5" />
                </div>
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-slate-800 leading-snug">Initial System Skill Mappings</h4>
                    <span className="text-[10px] text-slate-400 font-semibold">3 days ago</span>
                  </div>
                  <p className="text-slate-500 leading-normal">
                    Seeded original competency vector levels from user profile enrollment.
                  </p>
                  <Badge variant="outline" className="px-1.5 py-0 bg-slate-50">Initialized</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
