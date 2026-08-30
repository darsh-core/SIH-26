import React, { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import { Award, Lock, Mail, ShieldAlert } from "lucide-react"

import { authApi } from "../services/authApi"
import { useAuthStore } from "../store/authStore"
import { Button, Card, CardContent, Alert } from "../components/ui/Primitives"
import { DEMO_MODE, DEMO_CREDENTIALS } from "../lib/constants"

export const LoginPage = () => {
  const navigate = useNavigate();
  const { setAuth, isAuthenticated } = useAuthStore();
  
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // If already authenticated, redirect to dashboard immediately
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard");
    }
  }, [isAuthenticated, navigate]);

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
      navigate("/dashboard");
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
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-cover bg-center" style={{ backgroundImage: "linear-gradient(rgba(15, 23, 42, 0.95), rgba(15, 23, 42, 0.98))" }}>
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Award className="mx-auto h-16 w-16 text-amber-500 stroke-[1.5]" />
        <h2 className="mt-4 text-center text-2xl font-bold tracking-tight text-white uppercase">
          MoSPI Competency Platform
        </h2>
        <p className="mt-2 text-center text-xs text-slate-400 font-medium uppercase tracking-wider">
          Official Statistics Learning & Performance Audit Portal
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <Card className="border-slate-800 shadow-2xl bg-slate-950/70 backdrop-blur-md">
          <CardContent className="py-8 px-6 sm:px-10">
            {error && (
              <Alert variant="destructive" className="mb-6 bg-red-950/20 border-red-900 text-red-200">
                <div className="flex gap-2 items-start">
                  <ShieldAlert className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
                  <span>{error}</span>
                </div>
              </Alert>
            )}

            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="email" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Official Email Address
                </label>
                <div className="mt-1 relative rounded-md shadow-xs">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Mail className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2.5 border border-slate-800 rounded-md bg-slate-900 text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 focus:bg-slate-900"
                    placeholder="employee@mospi.gov.in"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Security Password
                </label>
                <div className="mt-1 relative rounded-md shadow-xs">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-4 w-4 text-slate-500" />
                  </div>
                  <input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2.5 border border-slate-800 rounded-md bg-slate-900 text-white text-sm placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 focus:bg-slate-900"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <div>
                <Button
                  type="submit"
                  className="w-full py-2.5 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold focus:ring-amber-500"
                  isLoading={loading}
                >
                  Verify Credentials & Enter
                </Button>
              </div>
            </form>

            {DEMO_MODE && (
              <div className="mt-8 border-t border-slate-800 pt-6">
                <div className="relative flex justify-center text-xs uppercase tracking-wider font-semibold">
                  <span className="bg-slate-950 px-2 text-slate-500">Fast-Track Demo Access</span>
                </div>
                <div className="mt-4">
                  <button
                    onClick={handleDemoLogin}
                    disabled={loading}
                    className="w-full flex items-center justify-center px-4 py-2 border border-dashed border-amber-500/50 rounded-md shadow-xs text-xs font-bold text-amber-500 bg-amber-500/5 hover:bg-amber-500/10 focus:outline-none transition-colors"
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
