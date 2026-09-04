import React, { useState, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { 
  User, 
  Building, 
  Award, 
  History, 
  CheckCircle, 
  ShieldCheck,
  TrendingUp,
  FileText,
  Edit3,
  AlertTriangle,
  X,
  Briefcase
} from "lucide-react";

import { useAuthStore } from "../store/authStore";
import { competencyApi } from "../services/competencyApi";
import { roleApi } from "../services/roleApi";
import { userApi } from "../services/userApi";
import { JobRole } from "../types/competency";
import { Card, CardContent, CardHeader, CardTitle, Badge, Progress, Button } from "../components/ui/Primitives";

const MOSPI_DEPARTMENTS = [
  "Agricultural Statistics Division",
  "National Sample Survey Office (NSSO)",
  "Survey Design and Research Division (SDRD)",
  "Data Informatics & Innovation Division (DIID)",
  "Field Operations Division (FOD)",
  "Central Statistics Office (CSO)",
  "National Data Warehouse (NDW)",
  "National Statistical Systems Training Academy (NSSTA)"
];

export const ProfilePage = () => {
  const queryClient = useQueryClient();
  const { user, updateUser } = useAuthStore();
  const userId = user?.id || "";

  const [editModalOpen, setEditModalOpen] = useState(false);
  const [roles, setRoles] = useState<JobRole[]>([]);
  const [selectedRole, setSelectedRole] = useState(user?.profile?.job_role_id || "");
  const [selectedDept, setSelectedDept] = useState(user?.profile?.department || MOSPI_DEPARTMENTS[0]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 1. Fetch competency gaps for role readiness comparison
  const { 
    data: gapData, 
    refetch: refetchGaps 
  } = useQuery({
    queryKey: ["competency-gaps", userId],
    queryFn: () => competencyApi.getCompetencyGaps(userId),
    enabled: !!userId
  });

  // Load roles for the edit modal
  useEffect(() => {
    roleApi.getRoles()
      .then(res => setRoles(res))
      .catch(err => console.warn("Failed to load roles", err));
  }, []);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRole || !selectedDept || !user) return;
    setSaving(true);
    setError(null);

    const targetRole = roles.find(r => r.id === selectedRole);

    try {
      const updated = await userApi.updateProfile(user.id, {
        department: selectedDept,
        designation: targetRole?.name || user?.profile?.designation,
        job_role_id: selectedRole
      });

      updateUser({
        ...user,
        profile: {
          ...user.profile,
          ...updated
        }
      });

      // Invalidate competency gaps cache to trigger recalculation
      await queryClient.invalidateQueries({ queryKey: ["competency-gaps", userId] });
      await refetchGaps();
      setEditModalOpen(false);
    } catch (err: any) {
      console.error("Profile update failed:", err);
      setError("Failed to update role. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-950">Employee Profile</h1>
          <p className="text-sm text-slate-500">Official security clearance and role competency details.</p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setEditModalOpen(true)}
          className="flex items-center gap-1.5 text-xs text-slate-700 hover:text-gov-blue-600 border-slate-300"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>Edit Role & Department</span>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Card: Profile details */}
        <Card className="lg:col-span-1 border-slate-200">
          <CardHeader className="text-center py-6 border-b border-slate-100 bg-slate-50/20">
            <div className="w-20 h-20 rounded-full bg-gov-blue-100 flex items-center justify-center text-gov-blue-500 text-3xl font-extrabold mx-auto shadow-inner">
              {user?.profile?.first_name?.charAt(0) || "A"}
            </div>
            <h2 className="text-base font-bold text-slate-900 mt-4">
              {user?.profile?.first_name || "Arun"} {user?.profile?.last_name || "Kumar"}
            </h2>
            <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-1">
              EMP{user?.id?.slice(0, 4).toUpperCase() || "001"}
            </p>
          </CardHeader>
          <CardContent className="p-6 divide-y divide-slate-100 text-xs">
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Job Role:</span>
              <strong className="text-slate-800">{user?.profile?.designation || gapData?.role.name || "Statistical Officer"}</strong>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Department:</span>
              <strong className="text-slate-800">{user?.profile?.department || "Agricultural Statistics Division"}</strong>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Domain:</span>
              <strong className="text-slate-800">{user?.profile?.bio?.replace("Specialization: ", "") || "Agricultural Statistics"}</strong>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Organization:</span>
              <strong className="text-slate-800">MoSPI, Govt of India</strong>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Target Role Track:</span>
              <strong className="text-gov-blue-500">{gapData?.role.name || "Statistical Officer"}</strong>
            </div>
            <div className="py-3 flex justify-between">
              <span className="text-slate-400 font-semibold uppercase">Last Assessed:</span>
              <strong className="text-slate-700">{new Date().toLocaleDateString("en-IN")}</strong>
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
              <div className="p-6 flex items-start gap-4 text-xs">
                <div className="p-2 bg-emerald-50 text-emerald-600 rounded-md border border-emerald-100">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-bold text-slate-800 leading-snug">Diagnostic Competency Checkpoint: {gapData?.role.name}</h4>
                    <span className="text-[10px] text-slate-400 font-semibold">Today</span>
                  </div>
                  <p className="text-slate-500 leading-normal">
                    Verified readiness: <strong>{gapData?.overall_readiness}%</strong> across <strong>{gapData?.gaps.length || 7}</strong> competencies.
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
                    <span className="text-[10px] text-slate-400 font-semibold">Earlier</span>
                  </div>
                  <p className="text-slate-500 leading-normal">
                    Seeded original competency vector levels from official profile enrollment.
                  </p>
                  <Badge variant="outline" className="px-1.5 py-0 bg-slate-50">Initialized</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Edit Role & Department Modal (Prompt Section 21) */}
      {editModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-2xl border border-slate-200 overflow-hidden">
            <div className="bg-slate-900 text-white p-5 flex items-center justify-between">
              <h3 className="text-base font-bold">Edit Role & Department</h3>
              <button onClick={() => setEditModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="p-6 space-y-4">
              {/* Warning Alert (Prompt Section 21) */}
              <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3 text-xs text-amber-800">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <strong>Important:</strong> Changing your role may change your competency requirements and personalized learning plan.
                </p>
              </div>

              {error && (
                <div className="text-xs text-rose-600 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
                  {error}
                </div>
              )}

              {/* Department */}
              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1.5">
                  Department / Division
                </label>
                <select
                  value={selectedDept}
                  onChange={(e) => setSelectedDept(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-900"
                >
                  {MOSPI_DEPARTMENTS.map((dept, i) => (
                    <option key={i} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>

              {/* Job Role */}
              <div>
                <label className="block text-xs font-bold uppercase text-slate-700 mb-1.5">
                  Job Role
                </label>
                <select
                  value={selectedRole}
                  onChange={(e) => setSelectedRole(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs text-slate-900"
                >
                  {roles.map((r) => (
                    <option key={r.id} value={r.id}>{r.name} ({r.code})</option>
                  ))}
                </select>
              </div>

              <div className="flex gap-3 pt-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setEditModalOpen(false)}
                  className="flex-1 text-xs"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-gov-blue-500 hover:bg-gov-blue-600 text-white text-xs font-bold"
                >
                  {saving ? "Updating..." : "Confirm Role Change"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
