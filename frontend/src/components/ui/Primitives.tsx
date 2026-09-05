import React from "react"
import { cn } from "../../lib/utils"

// ==========================================
// BUTTON COMPONENT
// ==========================================
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", isLoading, children, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-semibold rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]",
          // Variants
          variant === "primary" && "bg-gov-blue-600 hover:bg-gov-blue-700 text-white focus:ring-gov-blue-500 shadow-sm hover:shadow-md",
          variant === "secondary" && "bg-slate-100 hover:bg-slate-200 text-slate-800 focus:ring-slate-400 border border-slate-200",
          variant === "outline" && "border border-slate-300 bg-white hover:bg-slate-50 hover:border-gov-blue-300 hover:text-gov-blue-700 text-slate-700 focus:ring-gov-blue-500 shadow-sm",
          variant === "ghost" && "hover:bg-slate-100 text-slate-600",
          variant === "destructive" && "bg-red-600 hover:bg-red-700 text-white focus:ring-red-500 shadow-sm hover:shadow-md",
          // Sizes
          size === "sm" && "px-3 py-1.5 text-xs",
          size === "md" && "px-4 py-2 text-sm",
          size === "lg" && "px-6 py-3 text-base",
          className
        )}
        disabled={isLoading}
        {...props}
      >
        {isLoading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)
Button.displayName = "Button"

// ==========================================
// CARD COMPONENT
// ==========================================
export const Card = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("bg-white border border-slate-200/80 rounded-xl shadow-[0_2px_12px_-4px_rgba(0,0,0,0.08)] overflow-hidden", className)} {...props} />
)

export const CardHeader = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("px-6 py-4 border-b border-slate-100 bg-slate-50/50", className)} {...props} />
)

export const CardTitle = ({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={cn("text-base font-semibold text-gov-blue-600 tracking-tight", className)} {...props} />
)

export const CardDescription = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => (
  <p className={cn("text-xs text-slate-500 mt-1", className)} {...props} />
)

export const CardContent = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("px-6 py-4", className)} {...props} />
)

export const CardFooter = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("px-6 py-4 border-t border-slate-100 bg-slate-50/50 flex justify-end gap-2", className)} {...props} />
)

// ==========================================
// BADGE COMPONENT
// ==========================================
export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "outline" | "success" | "warning" | "error" | "info";
}

export const Badge = ({ className, variant = "default", ...props }: BadgeProps) => {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border transition-colors",
        variant === "default" && "bg-slate-100 text-slate-800 border-slate-200",
        variant === "secondary" && "bg-gov-blue-50 text-gov-blue-700 border-gov-blue-200",
        variant === "outline" && "text-slate-600 bg-white border-slate-300",
        variant === "success" && "bg-emerald-50 text-emerald-700 border-emerald-200",
        variant === "warning" && "bg-amber-50 text-amber-700 border-amber-200",
        variant === "error" && "bg-rose-50 text-rose-700 border-rose-200",
        variant === "info" && "bg-sky-50 text-sky-700 border-sky-200",
        className
      )}
      {...props}
    />
  )
}

// ==========================================
// PROGRESS COMPONENT (BAR)
// ==========================================
export interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  colorClassName?: string;
}

export const Progress = ({ className, value, colorClassName = "bg-gov-blue-500", ...props }: ProgressProps) => {
  return (
    <div className={cn("h-2 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200/50", className)} {...props}>
      <div
        className={cn("h-full transition-all duration-300", colorClassName)}
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}

// ==========================================
// ALERT COMPONENT
// ==========================================
export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "warning" | "destructive" | "success";
}

export const Alert = ({ className, variant = "default", children, ...props }: AlertProps) => {
  return (
    <div
      className={cn(
        "p-4 rounded-md border flex gap-3 text-sm leading-relaxed",
        variant === "default" && "bg-slate-50 text-slate-800 border-slate-200",
        variant === "warning" && "bg-amber-50 text-amber-800 border-amber-200",
        variant === "destructive" && "bg-red-50 text-red-800 border-red-200",
        variant === "success" && "bg-emerald-50 text-emerald-800 border-emerald-200",
        className
      )}
      role="alert"
      {...props}
    >
      <div className="flex-1">{children}</div>
    </div>
  )
}

// ==========================================
// SPINNER COMPONENT
// ==========================================
interface SpinnerProps {
  size?: "xs" | "sm" | "md" | "lg";
  className?: string;
}

export const Spinner = ({ size = "md", className }: SpinnerProps) => {
  const sizeClasses = {
    xs: "h-3 w-3 border-2",
    sm: "h-4 w-4 border-2",
    md: "h-6 w-6 border-2",
    lg: "h-8 w-8 border-2"
  };

  return (
    <div className={cn(
      "animate-spin rounded-full border-gov-blue-200 border-t-gov-blue-600",
      sizeClasses[size],
      className
    )} />
  );
};
