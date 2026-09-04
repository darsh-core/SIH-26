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
  TrendingUp
} from "lucide-react"

import { useAuthStore } from "../../store/authStore"
import { cn } from "../../lib/utils"
import { CopilotDrawer } from "../copilot/CopilotDrawer"

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

  const navItems = isTrainerOrStaff
    ? [
        { name: "Academy Dashboard", path: "/dashboard", icon: LayoutDashboard },
        { name: "Competency Framework", path: "/competencies", icon: Award },
        { name: "Document Matrix", path: "/documents", icon: FileText },
        { name: "Create Assessment", path: "/assessments/create", icon: PlusCircle },
        { name: "Recommendations", path: "/recommendations", icon: BookOpen },
        { name: "Profile", path: "/profile", icon: User }
      ]
    : [
        { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
        { name: "Role Readiness", path: "/role-readiness", icon: ShieldCheck },
        { name: "Skill Gaps", path: "/skill-gaps", icon: AlertTriangle },
        { name: "iGOT Recommendations", path: "/recommendations", icon: BookOpen },
        { name: "Learning Plan", path: "/learning-plan", icon: Map },
        { name: "Progress & History", path: "/progress", icon: TrendingUp },
        { name: "My Competencies", path: "/competencies", icon: Award },
        { name: "Profile", path: "/profile", icon: User }
      ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* 1. Header for mobile */}
      <header className="bg-gov-blue-500 text-white px-4 py-3 flex items-center justify-between md:hidden border-b border-gov-blue-600 shadow-sm z-30">
        <div className="flex items-center gap-2">
          <Award className="h-6 w-6 text-gov-gold" />
          <span className="font-bold tracking-tight text-sm uppercase">MoSPI Competency platform</span>
        </div>
        <button 
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)} 
          className="p-1 hover:bg-gov-blue-600 rounded-md transition-colors"
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </header>

      {/* 2. Drawer Nav for Mobile (overlay) */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/40 z-20 md:hidden backdrop-blur-xs" 
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* 3. Navigation Sidebar (Desktop & Mobile Drawer container) */}
      <aside 
        className={cn(
          "bg-gov-blue-500 text-white w-64 flex flex-col border-r border-gov-blue-600 flex-shrink-0 z-20 transition-all duration-300 md:translate-x-0 fixed md:static inset-y-0 left-0",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Brand block */}
        <div className="p-6 border-b border-gov-blue-600 hidden md:flex items-center gap-3">
          <Award className="h-8 w-8 text-gov-gold shrink-0" />
          <div>
            <h1 className="font-bold leading-tight tracking-tight text-sm uppercase">MoSPI</h1>
            <p className="text-[10px] text-slate-300 tracking-wider font-semibold uppercase">Official Statistics platform</p>
          </div>
        </div>

        {/* User context card */}
        {user && (
          <div className="p-6 border-b border-gov-blue-600 bg-gov-blue-600/20">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gov-blue-100 flex items-center justify-center text-gov-blue-500 font-bold shrink-0 shadow-inner">
                {user.profile?.first_name?.charAt(0) || (user.email?.includes("trainer") ? "S" : "U")}
              </div>
              <div className="min-w-0">
                <h4 className="text-sm font-semibold truncate">
                  {user.profile?.first_name ? `${user.profile.first_name} ${user.profile.last_name || ""}` : (user.email?.includes("trainer") ? "Dr. Sunita Sharma" : user.email)}
                </h4>
                <p className="text-xs text-slate-300 truncate">
                  {user.profile?.designation || (user.email?.includes("trainer") ? "Senior Training Director · NSSTA" : "Statistical Staff")}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Nav Links */}
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || (item.path !== "/dashboard" && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.name}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md transition-all group",
                  isActive 
                    ? "bg-gov-gold text-gov-blue-800 shadow-sm font-semibold" 
                    : "text-slate-200 hover:bg-gov-blue-600 hover:text-white"
                )}
              >
                <Icon className={cn("h-4 w-4 shrink-0", isActive ? "text-gov-blue-800" : "text-slate-300 group-hover:text-white")} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer actions inside Sidebar */}
        <div className="p-4 border-t border-gov-blue-600 space-y-1">
          <Link
            to="/profile"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-slate-200 hover:bg-gov-blue-600 hover:text-white transition-colors"
          >
            <HelpCircle className="h-4 w-4 text-slate-300" />
            <span>Help Support</span>
          </Link>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-md text-rose-300 hover:bg-rose-950/20 hover:text-rose-200 transition-colors"
          >
            <LogOut className="h-4 w-4 text-rose-300" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* 4. Main content viewport */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Desktop Top Header Bar */}
        <header className="bg-white border-b border-slate-200 px-8 py-4 hidden md:flex items-center justify-between shrink-0 shadow-xs">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-semibold tracking-wider uppercase">Official statistics competency intelligence platform</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <span className="text-xs font-semibold text-slate-500 block">Logged in as</span>
              <span className="text-xs font-bold text-gov-blue-500">{user?.email}</span>
            </div>
            <div className="w-[1px] h-6 bg-slate-200" />
            <button 
              onClick={handleLogout}
              className="text-slate-400 hover:text-rose-600 transition-colors"
              title="Sign Out"
            >
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </header>

        {/* App content views */}
        <div className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          {children}
        </div>
      </main>

      {/* Global MoSPI AI Copilot Widget */}
      <CopilotDrawer />
    </div>
  )
}
