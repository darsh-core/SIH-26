import React, { useState } from "react"
import { Link, useLocation, useNavigate } from "react-router-dom"
import { 
  LayoutDashboard, 
  Award, 
  BookOpen, 
  Map, 
  User, 
  LogOut, 
  Menu, 
  X, 
  TrendingDown, 
  HelpCircle,
  FileText,
  PlusCircle,
  AlertTriangle,
  ShieldCheck,
  TrendingUp,
  Lock,
  BarChart2,
  Users,
  FileCheck,
  Sparkles,
  Bell
} from "lucide-react"

import { useAuthStore } from "../../store/authStore"
import { cn } from "../../lib/utils"
import { CopilotDrawer } from "../copilot/CopilotDrawer"

import victusLogo from "../../assets/victus11.png"

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell = ({ children }: AppShellProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, clearAuth } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    clearAuth();
    navigate("/login");
  };

  const isTrainerOrStaff = Boolean(
    user?.is_superuser || 
    user?.email?.toLowerCase().includes("trainer") ||
    user?.profile?.designation?.toLowerCase().includes("director") ||
    user?.profile?.designation?.toLowerCase().includes("trainer") ||
    user?.roles?.some(r => 
      ["TRAINER", "ADMIN", "ADMINISTRATOR", "EVALUATOR", "SUPERVISOR", "MANAGER"].includes(r.name?.toUpperCase())
    )
  );

  const isUnassessed = !isTrainerOrStaff && user?.has_completed_assessment === false;

  const navItems = isTrainerOrStaff
    ? [
        { name: "Academy Dashboard", path: "/dashboard", icon: LayoutDashboard },
        { name: "Workforce Analytics", path: "/analytics/workforce", icon: BarChart2 },
        { name: "Employees", path: "/employees", icon: Users },
        { name: "Competency Framework", path: "/competencies", icon: Award },
        { name: "Document Intelligence", path: "/documents", icon: FileText },
        { name: "AI Question Review", path: "/questions/review", icon: FileCheck },
        { name: "Assessments", path: "/assessments/create", icon: PlusCircle },
        { name: "Recommendations", path: "/recommendations", icon: BookOpen },
        { name: "Learning Plans", path: "/learning-plans", icon: Map },
        { name: "Training Effectiveness", path: "/training-effectiveness", icon: TrendingUp },
        { name: "AI Insights", path: "/ai-insights", icon: Sparkles },
        { name: "Alerts", path: "/alerts", icon: Bell },
        { name: "Reports", path: "/reports", icon: FileText },
        { name: "Profile", path: "/profile", icon: User }
      ]

    : isUnassessed
    ? [
        { name: "Diagnostic Assessment", path: "/onboarding/role", icon: ShieldCheck, isRequired: true },
        { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard, isLocked: true },
        { name: "Role Readiness", path: "/role-readiness", icon: ShieldCheck, isLocked: true },
        { name: "Skill Gaps", path: "/skill-gaps", icon: AlertTriangle, isLocked: true },
        { name: "iGOT Recommendations", path: "/recommendations", icon: BookOpen, isLocked: true },
        { name: "Learning Plan", path: "/learning-plan", icon: Map, isLocked: true },
        { name: "Profile", path: "/profile", icon: User }
      ]
    : [
        { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
        { name: "Role Readiness", path: "/role-readiness", icon: ShieldCheck },
        { name: "Skill Gaps", path: "/skill-gaps", icon: AlertTriangle },
        { name: "iGOT Recommendations", path: "/recommendations", icon: BookOpen },
        { name: "Learning Plan", path: "/learning-plan", icon: Map },
        { name: "Assessments & Practice", path: "/assessments/create", icon: PlusCircle },
        { name: "Progress & History", path: "/progress", icon: TrendingUp },
        { name: "My Competencies", path: "/competencies", icon: Award },
        { name: "Profile", path: "/profile", icon: User }
      ];


  return (
    <div className="h-screen bg-slate-50 flex flex-col overflow-hidden">
      {/* Official Govt Strip */}
      <div className="bg-[#1a1a1a] text-slate-200 py-1.5 px-6 text-xs font-semibold flex justify-between items-center z-40 relative shrink-0">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-2">
            <span className="text-white font-bold tracking-wide">भारत सरकार</span>
            <span className="opacity-50">|</span>
            <span className="tracking-wide">GOVERNMENT OF INDIA</span>
          </span>
        </div>
        <div className="hidden md:flex items-center gap-4">
          <span className="tracking-wide">iGOT Karmayogi Competency Intelligence Platform</span>
        </div>
      </div>
      
      <div className="flex-1 flex flex-col md:flex-row relative min-h-0 overflow-hidden">
      {/* 1. Header for mobile */}
      <header className="bg-slate-900 text-white px-5 py-3 flex items-center justify-between md:hidden border-b border-slate-800 shadow-sm z-30 shrink-0">
        <div className="flex items-center gap-2.5">
          <img src={victusLogo} alt="VICTUS 11 Logo" className="h-8 w-auto bg-white p-1 rounded-md shadow-xs" />
          <div>
            <span className="font-bold tracking-tight text-sm uppercase text-white block">VICTUS 11</span>
            <span className="text-[10px] text-slate-400 font-medium block">MoSPI Skill Intelligence</span>
          </div>
        </div>
        <button 
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)} 
          className="p-1.5 hover:bg-slate-800 rounded-lg transition-colors text-slate-300"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </header>

      {/* 2. Drawer Nav for Mobile (overlay) */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-slate-950/60 z-20 md:hidden backdrop-blur-xs" 
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* 3. Navigation Sidebar (Desktop & Mobile Drawer container) */}
      <aside 
        className={cn(
          "bg-slate-900 text-white w-72 flex flex-col border-r border-slate-800 shrink-0 z-20 transition-transform duration-200 fixed md:relative h-full inset-y-0 left-0",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        )}
      >
        {/* Brand block */}
        <div className="p-3.5 border-b border-slate-800/80 hidden md:flex items-center gap-3 bg-slate-950/40 shrink-0">
          <img src={victusLogo} alt="VICTUS 11 Logo" className="h-8 w-auto bg-white p-1 rounded-lg shrink-0 shadow-xs" />
          <div className="min-w-0">
            <h1 className="font-bold leading-tight tracking-wider text-sm uppercase text-white">VICTUS 11</h1>
            <p className="text-[10px] text-slate-400 leading-tight tracking-wide font-medium">MoSPI Competency & Skill Intelligence</p>
          </div>
        </div>

        {/* User context card */}
        {user && (
          <div className="p-3 border-b border-slate-800/80 bg-slate-800/40 shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-blue-600 text-white font-bold text-xs flex items-center justify-center shrink-0 shadow-xs">
                {user.profile?.first_name?.charAt(0) || (user.email?.includes("trainer") ? "S" : "U")}
              </div>
              <div className="min-w-0">
                <h4 className="text-xs font-bold text-white truncate">
                  {user.profile?.first_name ? `${user.profile.first_name} ${user.profile.last_name || ""}` : (user.email?.includes("trainer") ? "Dr. Sunita Sharma" : user.email)}
                </h4>
                <p className="text-[10px] text-slate-400 truncate font-normal">
                  {user.profile?.designation || (user.email?.includes("trainer") ? "Senior Training Director · NSSTA" : "Statistical Staff")}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Nav Links */}
        <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto min-h-0">
          {navItems.map((item: any) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || (item.path !== "/dashboard" && location.pathname.startsWith(item.path));
            
            if (item.isLocked) {
              return (
                <div
                  key={item.name}
                  className="flex items-center justify-between px-3 py-1.5 text-xs font-semibold rounded-lg text-slate-500 bg-slate-800/20 cursor-not-allowed select-none opacity-50"
                  title="Complete initial diagnostic assessment to unlock"
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="h-4 w-4 shrink-0 text-slate-500" />
                    <span>{item.name}</span>
                  </div>
                  <Lock className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                </div>
              );
            }

            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  "flex items-center justify-between px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors group",
                  isActive 
                    ? "bg-blue-600 text-white font-bold shadow-xs" 
                    : "text-slate-300 hover:bg-slate-800/70 hover:text-white"
                )}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={cn("h-4 w-4 shrink-0 transition-colors", isActive ? "text-white" : "text-slate-400 group-hover:text-white")} />
                  <span>{item.name}</span>
                </div>
                {item.isRequired && (
                  <span className="text-[9px] uppercase font-bold tracking-wide px-1.5 py-0.5 rounded bg-amber-400/20 text-amber-300 border border-amber-400/30">
                    Required
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer actions inside Sidebar (100% visible and pinned) */}
        <div className="p-3 border-t border-slate-800/80 space-y-1 shrink-0 bg-slate-950/80">
          <Link
            to="/profile"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2.5 px-3 py-1.5 text-xs font-bold rounded-lg text-slate-300 hover:bg-slate-800/70 hover:text-white transition-colors"
          >
            <HelpCircle className="h-4 w-4 text-slate-400" />
            <span>Help & Support</span>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3 py-1.5 text-xs font-bold rounded-lg text-rose-400 hover:bg-rose-950/40 hover:text-rose-200 transition-colors cursor-pointer"
          >
            <LogOut className="h-4 w-4 text-rose-400" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* 4. Main content viewport */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto bg-slate-50">
        {/* App content views */}
        <div className="flex-1 p-6 md:p-8 max-w-[1600px] w-full mx-auto">
          {children}
        </div>
      </main>

      {/* Global MoSPI AI Copilot Widget */}
      <CopilotDrawer />
      </div>
    </div>
  )
}
