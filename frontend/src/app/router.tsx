import React from "react"
import { createBrowserRouter, Navigate, Outlet, useLocation } from "react-router-dom"

import { useAuthStore } from "../store/authStore"
import { AppShell } from "../components/layout/AppShell"
import { LoginPage } from "../pages/LoginPage"
import { DashboardPage } from "../pages/DashboardPage"
import { CompetencyPage } from "../pages/CompetencyPage"
import { RecommendationsPage } from "../pages/RecommendationsPage"
import { LearningPlanPage } from "../pages/LearningPlanPage"
import { AssessmentPage } from "../pages/AssessmentPage"
import { AssessmentResultPage } from "../pages/AssessmentResultPage"
import { ProfilePage } from "../pages/ProfilePage"
import { NotFoundPage } from "../pages/NotFoundPage"
import { DocumentManagerPage } from "../pages/DocumentManagerPage"
import { DocumentUploadPage } from "../pages/DocumentUploadPage"
import { QuestionGeneratorPage } from "../pages/QuestionGeneratorPage"
import { AssessmentBuilderPage } from "../pages/AssessmentBuilderPage"
import { OnboardingRolePage } from "../pages/OnboardingRolePage"
import { DiagnosticAssessmentPage } from "../pages/DiagnosticAssessmentPage"
import { InitialCompetencyStatusPage } from "../pages/InitialCompetencyStatusPage"
import { SkillGapsPage } from "../pages/SkillGapsPage"
import { RoleReadinessPage } from "../pages/RoleReadinessPage"
import { ProgressPage } from "../pages/ProgressPage"
import { DemoIGOTPlayerPage } from "../pages/DemoIGOTPlayerPage"

// ==========================================
// ROUTE GUARD (AUTHENTICATED ONLY + ASSESSMENT GATING)
// ==========================================
const ProtectedLayout = () => {
  const { isAuthenticated, user } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check if learner must complete baseline assessment before viewing dashboard
  const isTrainerOrStaff = Boolean(
    user?.is_superuser ||
    user?.roles?.some(r => ["TRAINER", "ADMIN", "ADMINISTRATOR"].includes(r.name?.toUpperCase()))
  );

  const isAssessmentRoute = 
    location.pathname.startsWith("/onboarding") ||
    location.pathname.startsWith("/diagnostic") ||
    location.pathname.startsWith("/initial-status") ||
    location.pathname.startsWith("/assessments") ||
    location.pathname.startsWith("/profile");

  if (!isTrainerOrStaff && user && user.has_completed_assessment === false && !isAssessmentRoute) {
    return <Navigate to="/onboarding/role" replace />;
  }

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
};

export const router = createBrowserRouter([
  // Public Route
  {
    path: "/login",
    element: <LoginPage />
  },
  
  // Protected Routes wrapped with AppShell
  {
    element: <ProtectedLayout />,
    children: [
      {
        path: "/",
        element: <Navigate to="/dashboard" replace />
      },
      {
        path: "/dashboard",
        element: <DashboardPage />
      },
      {
        path: "/onboarding/role",
        element: <OnboardingRolePage />
      },
      {
        path: "/diagnostic",
        element: <DiagnosticAssessmentPage />
      },
      {
        path: "/initial-status",
        element: <InitialCompetencyStatusPage />
      },
      {
        path: "/competencies",
        element: <CompetencyPage />
      },
      {
        path: "/skill-gaps",
        element: <SkillGapsPage />
      },
      {
        path: "/role-readiness",
        element: <RoleReadinessPage />
      },
      {
        path: "/recommendations",
        element: <RecommendationsPage />
      },
      {
        path: "/learning-plan",
        element: <LearningPlanPage />
      },
      {
        path: "/progress",
        element: <ProgressPage />
      },
      {
        path: "/demo-igot/courses/:courseId",
        element: <DemoIGOTPlayerPage />
      },
      {
        path: "/documents",
        element: <DocumentManagerPage />
      },
      {
        path: "/documents/upload",
        element: <DocumentUploadPage />
      },
      {
        path: "/documents/:id/generate",
        element: <QuestionGeneratorPage />
      },
      {
        path: "/assessments/create",
        element: <AssessmentBuilderPage />
      },
      {
        path: "/assessments/:id",
        element: <AssessmentPage />
      },
      {
        path: "/assessments/:id/result",
        element: <AssessmentResultPage />
      },
      {
        path: "/profile",
        element: <ProfilePage />
      },
      {
        path: "*",
        element: <NotFoundPage />
      }
    ]
  }
]);
