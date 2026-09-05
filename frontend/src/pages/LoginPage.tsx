import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Award, Lock, Mail, ShieldAlert } from "lucide-react"

import { authApi } from "../services/authApi"
import { useAuthStore } from "../store/authStore"
import { Button, Card, CardContent, Alert } from "../components/ui/Primitives"
import { DEMO_MODE, DEMO_CREDENTIALS } from "../lib/constants"

export const LoginPage = () => {
  const navigate = useNavigate();
  const { setAuth, isAuthenticated, user } = useAuthStore();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // If already authenticated, redirect based on assessment completion
  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.has_completed_assessment) {
        navigate("/dashboard");
      } else {
        navigate("/onboarding/role");
      }
    }
  }, [isAuthenticated, user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await authApi.login(email, password);
      setAuth(data.access_token, data.refresh_token, {} as any);
      const userProfile = await authApi.getMe();
      setAuth(data.access_token, data.refresh_token, userProfile);
      
      if (userProfile.has_completed_assessment) {
        navigate("/dashboard");
      } else {
        navigate("/onboarding/role");
      }
    } catch (err: any) {
      console.error("Login error:", err);
      setError(err.message || "Invalid credentials. Please verify your email and password.");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setEmail(DEMO_CREDENTIALS.email);
    setPassword(DEMO_CREDENTIALS.password);
    
    setLoading(true);
    setError(null);
    try {
      const data = await authApi.login(DEMO_CREDENTIALS.email, DEMO_CREDENTIALS.password);
      setAuth(data.access_token, data.refresh_token, {} as any);
      const userProfile = await authApi.getMe();
      setAuth(data.access_token, data.refresh_token, userProfile);
      navigate("/dashboard");
    } catch (err: any) {
      console.error("Demo login error:", err);
      setError(err.message || "Demo login failed. Make sure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="relative min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 overflow-hidden animate-gradient-shift"
      style={{
        backgroundImage: "linear-gradient(-45deg, #eef2ff, #e0f2fe, #fef3c7, #e0e7ff, #ecfdf5, #f0f9ff)",
        backgroundSize: "300% 300%"
      }}
    >
      {/* Dynamic drifting ambient glowing liquid orbs */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-24 left-1/4 w-[600px] h-[450px] bg-blue-300/35 rounded-full blur-3xl animate-float-1" />
        <div className="absolute top-1/3 -right-20 w-[450px] h-[450px] bg-amber-200/40 rounded-full blur-3xl animate-float-2" />
        <div className="absolute -bottom-24 left-1/3 w-[550px] h-[400px] bg-teal-200/35 rounded-full blur-3xl animate-float-3" />
        <div className="absolute top-2/3 -left-20 w-[400px] h-[400px] bg-purple-200/30 rounded-full blur-3xl animate-float-1" />
        
        {/* Subtle geometric dot grid texture */}
        <div 
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage: `radial-gradient(#0f172a 1.2px, transparent 1.2px)`,
            backgroundSize: "24px 24px"
          }}
        />
      </div>

      <div className="relative z-10 sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex p-3 rounded-2xl bg-white/90 backdrop-blur-md border border-white/80 shadow-md mb-2">
          <Award className="h-12 w-12 text-amber-500 stroke-[1.5]" />
        </div>
        <h2 className="mt-2 text-center text-2xl font-black tracking-tight text-slate-900 uppercase font-sans">
          MoSPI Competency Platform
        </h2>
        <p className="mt-1 text-center text-xs text-slate-500 font-medium uppercase tracking-wider">
          Official Statistics Learning & Performance Audit Portal
        </p>
      </div>

      <div className="relative z-10 mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="border-white/80 shadow-[0_20px_60px_rgba(15,23,42,0.08)] bg-white/85 backdrop-blur-2xl rounded-2xl ring-1 ring-white/60">
          <CardContent className="py-8 px-6 sm:px-10">
            {error && (
              <Alert variant="destructive" className="mb-6 bg-red-50 border-red-200 text-red-700">
                <div className="flex gap-2 items-start">
                  <ShieldAlert className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
                  <span>{error}</span>
                </div>
              </Alert>
            )}

            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Official Email Address
                </label>
                <div className="relative rounded-md shadow-2xs">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-4 w-4 text-slate-400" />
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg bg-slate-50/70 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gov-blue-500 focus:border-gov-blue-500 focus:bg-white transition-all"
                    placeholder="employee@mospi.gov.in"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Security Password
                </label>
                <div className="relative rounded-md shadow-2xs">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-4 w-4 text-slate-400" />
                  </div>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg bg-slate-50/70 text-slate-900 text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gov-blue-500 focus:border-gov-blue-500 focus:bg-white transition-all"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <div>
                <Button
                  type="submit"
                  className="w-full py-2.5 bg-gov-blue-500 hover:bg-gov-blue-600 text-white font-bold rounded-lg shadow-md hover:shadow-lg focus:ring-gov-blue-500 transition-all"
                  isLoading={loading}
                >
                  Verify Credentials & Enter
                </Button>
              </div>
            </form>

            {DEMO_MODE && (
              <div className="mt-8 border-t border-slate-200 pt-6">
                <div className="relative flex justify-center text-xs uppercase tracking-wider font-semibold">
                  <span className="bg-white px-3 text-slate-400">Fast-Track Demo Access</span>
                </div>
                <div className="mt-4">
                  <button
                    onClick={handleDemoLogin}
                    disabled={loading}
                    className="w-full flex items-center justify-center px-4 py-2.5 border border-dashed border-gov-blue-300 rounded-lg shadow-2xs text-xs font-bold text-gov-blue-600 bg-gov-blue-50/60 hover:bg-gov-blue-50 hover:border-gov-blue-400 focus:outline-none transition-colors"
                  >
                    Auto-Login as Ramesh Chandra (Statistical Officer)
                  </button>
                  <p className="mt-2 text-center text-[10px] text-slate-500 leading-normal">
                    Loads default data: 72.4% Readiness, 2.3 Sampling Gap, and iGOT recommendations matching gaps.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
