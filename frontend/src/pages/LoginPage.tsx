import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { ShieldCheck, Lock, Mail, ShieldAlert } from "lucide-react"

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
    <div className="relative min-h-screen flex flex-col bg-slate-900 overflow-hidden">
      
      {/* Official Govt Strip */}
      <div className="bg-black/80 text-slate-300 py-1.5 px-6 text-[11px] font-medium flex justify-between items-center z-40 border-b border-white/10">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="text-white font-bold tracking-wide">भारत सरकार</span>
            <span className="opacity-50">|</span>
            <span className="tracking-wide">GOVERNMENT OF INDIA</span>
          </span>
        </div>
        <div className="hidden md:flex items-center gap-4 text-[10px] tracking-wider uppercase">
          <span>Ministry of Statistics and Programme Implementation (MoSPI)</span>
        </div>
      </div>

      {/* Background Texture & Gradient */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-800 via-slate-900 to-black" />
        <div 
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `radial-gradient(#ffffff 1.2px, transparent 1.2px)`,
            backgroundSize: "32px 32px"
          }}
        />
        {/* Subtle accent glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-gov-blue-600/20 rounded-full blur-[120px]" />
      </div>

      <div className="flex-1 flex flex-col justify-center py-12 sm:px-6 lg:px-8 z-10">
        
        {/* Header Block */}
        <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-8">
          <div className="inline-flex p-4 rounded-2xl bg-white/5 border border-white/10 shadow-2xl mb-4 backdrop-blur-sm">
            <ShieldCheck className="h-12 w-12 text-gov-gold stroke-[1.5]" />
          </div>
          <h2 className="text-center text-3xl font-extrabold tracking-tight text-white uppercase font-sans drop-shadow-sm">
            SkillStat AI
          </h2>
          <p className="mt-2 text-center text-xs text-slate-400 font-semibold uppercase tracking-[0.15em]">
            Official Statistics Competency Intelligence
          </p>
        </div>

        {/* Login Card */}
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <Card className="border-0 shadow-[0_20px_60px_rgba(0,0,0,0.5)] bg-white rounded-2xl ring-1 ring-black/5">
            <CardContent className="py-8 px-6 sm:px-10">
              {error && (
                <Alert variant="destructive" className="mb-6 bg-red-50 border-red-200 text-red-700 shadow-inner">
                  <div className="flex gap-2 items-start">
                    <ShieldAlert className="h-4 w-4 shrink-0 text-red-500 mt-0.5" />
                    <span className="font-medium text-sm">{error}</span>
                  </div>
                </Alert>
              )}

              <form className="space-y-6" onSubmit={handleSubmit}>
                <div>
                  <label htmlFor="email" className="block text-[11px] font-extrabold text-slate-600 uppercase tracking-wider mb-1.5">
                    Official Email Address
                  </label>
                  <div className="relative rounded-lg shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
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
                      className="block w-full pl-10 pr-3 py-3 border border-slate-300 rounded-lg bg-slate-50 text-slate-900 text-sm font-medium placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gov-blue-500 focus:border-gov-blue-500 focus:bg-white transition-all"
                      placeholder="employee@mospi.gov.in"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="password" className="block text-[11px] font-extrabold text-slate-600 uppercase tracking-wider mb-1.5">
                    Security Password
                  </label>
                  <div className="relative rounded-lg shadow-sm">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
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
                      className="block w-full pl-10 pr-3 py-3 border border-slate-300 rounded-lg bg-slate-50 text-slate-900 text-sm font-medium placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-gov-blue-500 focus:border-gov-blue-500 focus:bg-white transition-all"
                      placeholder="••••••••"
                    />
                  </div>
                </div>

                <div>
                  <Button
                    type="submit"
                    className="w-full py-3 bg-gov-blue-600 hover:bg-gov-blue-700 text-white font-bold rounded-lg shadow-md hover:shadow-lg focus:ring-offset-2 focus:ring-gov-blue-500 transition-all text-sm uppercase tracking-wide"
                    isLoading={loading}
                  >
                    Verify Credentials & Enter
                  </Button>
                </div>
              </form>

              {DEMO_MODE && (
                <div className="mt-8 border-t border-slate-100 pt-6">
                  <div className="relative flex justify-center text-[10px] uppercase tracking-wider font-extrabold mb-4">
                    <span className="bg-white px-3 text-slate-400">Fast-Track Access</span>
                  </div>
                  <div>
                    <button
                      onClick={handleDemoLogin}
                      disabled={loading}
                      className="w-full flex items-center justify-center px-4 py-3 border border-dashed border-gov-blue-300 rounded-lg shadow-sm text-xs font-bold text-gov-blue-700 bg-gov-blue-50/50 hover:bg-gov-blue-50 hover:border-gov-blue-500 focus:outline-none transition-all"
                    >
                      Auto-Login as Ramesh Chandra (Officer)
                    </button>
                    <p className="mt-3 text-center text-[10px] text-slate-500 leading-relaxed font-medium">
                      Loads default demonstration data: 72.4% Readiness, 2.3 Sampling Gap, and matching iGOT recommendations.
                    </p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
          
          <p className="text-center text-[10px] text-slate-500 mt-6 font-medium">
            Protected by MoSPI Security. Unauthorized access is strictly prohibited.
          </p>
        </div>
      </div>
    </div>
  )
}
