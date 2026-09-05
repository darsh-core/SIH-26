import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Building, 
  Briefcase, 
  Sparkles, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft, 
  Layers, 
  ShieldCheck,
  Award,
  AlertCircle
} from "lucide-react";
import { useAuthStore } from "../store/authStore";
import { roleApi } from "../services/roleApi";
import { userApi } from "../services/userApi";
import { assessmentApi } from "../services/assessmentApi";
import { JobRole } from "../types/competency";
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from "../components/ui/Primitives";

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

const MOSPI_DOMAINS = [
  "Agricultural Statistics",
  "Sample Surveys & Field Operations",
  "Price & Labour Statistics",
  "National Accounts & Economic Statistics",
  "Data Science & Statistical Engineering",
  "Survey Methodology & Research",
  "Digital Governance & Data Quality"
];

export const OnboardingRolePage: React.FC = () => {
  const navigate = useNavigate();
  const { user, updateUser } = useAuthStore();

  const [step, setStep] = useState<"form" | "confirm">("form");
  const [roles, setRoles] = useState<JobRole[]>([]);
  const [loadingRoles, setLoadingRoles] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [firstName, setFirstName] = useState(user?.profile?.first_name || "Arun");
  const [lastName, setLastName] = useState(user?.profile?.last_name || "Kumar");
  const [selectedDept, setSelectedDept] = useState(user?.profile?.department || MOSPI_DEPARTMENTS[0]);
  const [selectedRoleId, setSelectedRoleId] = useState(user?.profile?.job_role_id || "");
  const [selectedDomain, setSelectedDomain] = useState(user?.profile?.domain || MOSPI_DOMAINS[0]);

  // Load job roles from backend
  useEffect(() => {
    roleApi.getRoles()
      .then(fetchedRoles => {
        setRoles(fetchedRoles);
        if (!selectedRoleId && fetchedRoles.length > 0) {
          // Pre-select Statistical Officer if found, else first role
          const statOfficer = fetchedRoles.find(r => r.code === "ROLE_STAT_OFFICER" || r.name.toLowerCase().includes("statistical officer"));
          setSelectedRoleId(statOfficer ? statOfficer.id : fetchedRoles[0].id);
        }
      })
      .catch(err => {
        console.error("Failed to load roles:", err);
        setError("Unable to load official job roles. Please try again.");
      })
      .finally(() => setLoadingRoles(false));
  }, []);

  const selectedRole = roles.find(r => r.id === selectedRoleId);

  const handleContinue = (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName.trim() || !lastName.trim() || !selectedRoleId || !selectedDept) {
      setError("Please fill in all role and department fields to proceed.");
      return;
    }
    setError(null);
    setStep("confirm");
  };

  const handleConfirmAndStartAssessment = async () => {
    if (!user || !selectedRole) return;
    setSubmitting(true);
    setError(null);

    try {
      // 1. Update user profile in backend
      const updatedProfile = await userApi.updateProfile(user.id, {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        department: selectedDept,
        designation: selectedRole.name,
        job_role_id: selectedRole.id,
        bio: `Specialization: ${selectedDomain}`
      });

      // Update Zustand state
      updateUser({
        ...user,
        profile: {
          ...user.profile,
          ...updatedProfile,
          domain: selectedDomain
        }
      });

      // 2. Generate or fetch AI Role Diagnostic Assessment
      const diagResult = await assessmentApi.createRoleDiagnostic(selectedRole.id, 6);

      // 3. Navigate to diagnostic assessment page
      navigate(`/diagnostic?assessment_id=${diagResult.assessment_id}&role_name=${encodeURIComponent(selectedRole.name)}&dept=${encodeURIComponent(selectedDept)}`);
    } catch (err: any) {
      console.error("Onboarding failed:", err);
      setError(err?.message || "Failed to initiate AI diagnostic. Please try again.");
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4">
      <div className="max-w-xl w-full">
        {/* Step 1: Tell Us About Your Role */}
        {step === "form" && (
          <Card className="border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="bg-gradient-to-r from-gov-blue-500 via-indigo-900 to-gov-blue-600 text-white p-6 sm:p-8">
              <div className="flex items-center gap-2.5 text-gov-gold mb-2">
                <ShieldCheck className="w-5 h-5" />
                <span className="text-xs font-bold uppercase tracking-wider">MoSPI Baseline Assessment Required</span>
              </div>
              <h1 className="text-2xl font-extrabold tracking-tight">Official Competency Assessment</h1>
              <p className="text-sm text-blue-100/90 mt-1.5 leading-relaxed">
                Welcome{user?.profile?.first_name ? `, ${user.profile.first_name}` : ""}! Before accessing the dashboard, all statistical officers must undergo a baseline competency assessment to evaluate your role readiness and calibrate your personalized twin.
              </p>
            </div>

            <CardContent className="p-6 sm:p-8 space-y-6">
              {error && (
                <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 flex items-center gap-3 text-xs text-rose-700">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleContinue} className="space-y-4">
                {/* Full Name */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      First Name <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      placeholder="e.g. Arun"
                      className="w-full bg-slate-50 focus:bg-white border border-slate-300 focus:border-gov-blue-500 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 outline-hidden transition-all"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                      Last Name <span className="text-rose-500">*</span>
                    </label>
                    <input
                      type="text"
                      required
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      placeholder="e.g. Kumar"
                      className="w-full bg-slate-50 focus:bg-white border border-slate-300 focus:border-gov-blue-500 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 outline-hidden transition-all"
                    />
                  </div>
                </div>

                {/* Department */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Department / Division <span className="text-rose-500">*</span>
                  </label>
                  <div className="relative">
                    <Building className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
                    <select
                      value={selectedDept}
                      onChange={(e) => setSelectedDept(e.target.value)}
                      required
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-50 focus:bg-white border border-slate-300 focus:border-gov-blue-500 rounded-lg text-sm text-slate-900 outline-hidden transition-all cursor-pointer"
                    >
                      {MOSPI_DEPARTMENTS.map((dept, i) => (
                        <option key={i} value={dept}>{dept}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Job Role */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                      Job Role <span className="text-rose-500">*</span>
                    </label>
                    <span className="text-[10px] text-slate-500 font-semibold">Authoritative MoSPI Track</span>
                  </div>
                  <div className="relative">
                    <Briefcase className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
                    <select
                      value={selectedRoleId}
                      onChange={(e) => setSelectedRoleId(e.target.value)}
                      required
                      disabled={loadingRoles}
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-50 focus:bg-white border border-slate-300 focus:border-gov-blue-500 rounded-lg text-sm text-slate-900 outline-hidden transition-all cursor-pointer disabled:opacity-60"
                    >
                      {loadingRoles ? (
                        <option value="">Loading official roles from database...</option>
                      ) : (
                        roles.map((r) => (
                          <option key={r.id} value={r.id}>
                            {r.name} ({r.code})
                          </option>
                        ))
                      )}
                    </select>
                  </div>
                  {selectedRole && (
                    <p className="text-xs text-slate-500 mt-1.5 italic">
                      {selectedRole.description || "Official role mapping evaluated against standard MoSPI competency frameworks."}
                    </p>
                  )}
                </div>

                {/* Domain / Specialization */}
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                    Domain / Specialization
                  </label>
                  <div className="relative">
                    <Layers className="w-4 h-4 text-slate-400 absolute left-3.5 top-3 pointer-events-none" />
                    <select
                      value={selectedDomain}
                      onChange={(e) => setSelectedDomain(e.target.value)}
                      className="w-full pl-10 pr-4 py-2.5 bg-slate-50 focus:bg-white border border-slate-300 focus:border-gov-blue-500 rounded-lg text-sm text-slate-900 outline-hidden transition-all cursor-pointer"
                    >
                      {MOSPI_DOMAINS.map((dom, i) => (
                        <option key={i} value={dom}>{dom}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="pt-4">
                  <Button
                    type="submit"
                    className="w-full flex items-center justify-center gap-2 py-3 bg-gov-blue-500 hover:bg-gov-blue-600 text-white font-bold rounded-lg shadow-md hover:shadow-lg transition-all"
                  >
                    <span>Continue</span>
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Role Confirmation */}
        {step === "confirm" && (
          <Card className="border-slate-200 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="bg-slate-900 text-white p-6 sm:p-8 border-b border-slate-800">
              <span className="text-xs font-bold uppercase tracking-wider text-gov-gold flex items-center gap-1.5 mb-1">
                <Sparkles className="w-4 h-4" />
                Review & Verification
              </span>
              <h2 className="text-xl font-bold tracking-tight">
                You're setting up your competency profile
              </h2>
            </div>

            <CardContent className="p-6 sm:p-8 space-y-6">
              {error && (
                <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 flex items-center gap-3 text-xs text-rose-700">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{error}</span>
                </div>
              )}

              {/* Confirmation Preview Card */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-6 space-y-4">
                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Official Name</span>
                  <h3 className="text-lg font-bold text-slate-900 uppercase tracking-wide">
                    {firstName} {lastName}
                  </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-200/80">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Job Role</span>
                    <strong className="text-sm text-gov-blue-500 font-semibold block mt-0.5">
                      {selectedRole?.name || "Statistical Officer"}
                    </strong>
                  </div>

                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Department</span>
                    <strong className="text-sm text-slate-800 font-semibold block mt-0.5">
                      {selectedDept}
                    </strong>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-200/80">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Domain / Specialization</span>
                  <strong className="text-xs text-slate-700 font-medium block mt-0.5">
                    {selectedDomain}
                  </strong>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-blue-50/80 border border-blue-100 flex items-start gap-3 text-xs text-blue-900">
                <CheckCircle2 className="w-4 h-4 text-gov-blue-500 shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  Your competency profile will be evaluated against the standard requirements of the <strong>{selectedRole?.name}</strong> role. The next step is a 6-question AI diagnostic assessment.
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setStep("form")}
                  disabled={submitting}
                  className="flex-1 flex items-center justify-center gap-2 py-3 border-slate-300"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>Edit Details</span>
                </Button>

                <Button
                  onClick={handleConfirmAndStartAssessment}
                  disabled={submitting}
                  className="flex-1 flex items-center justify-center gap-2 py-3 bg-gov-blue-500 hover:bg-gov-blue-600 text-white font-bold rounded-lg shadow-md"
                >
                  {submitting ? (
                    <span>Generating Diagnostic...</span>
                  ) : (
                    <>
                      <span>Confirm & Start Assessment</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};
