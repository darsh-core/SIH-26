import React from "react"
import { useNavigate } from "react-router-dom"
import { ShieldAlert } from "lucide-react"

import { Button } from "../components/ui/Primitives"

export const NotFoundPage = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] gap-4 text-center">
      <ShieldAlert className="h-16 w-16 text-amber-500 stroke-[1.25]" />
      <div className="space-y-2">
        <h2 className="text-xl font-bold text-slate-800 uppercase tracking-tight">404 - Page Not Found</h2>
        <p className="text-xs text-slate-500 max-w-sm leading-normal">
          The requested page resource is unavailable or has restricted clearance. Please verify the URL path or return to the main dashboard workspace.
        </p>
      </div>
      <Button variant="primary" className="mt-2" onClick={() => navigate("/dashboard")}>
        Return to Dashboard
      </Button>
    </div>
  )
}
