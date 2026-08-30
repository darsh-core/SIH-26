import React from "react"
import { QueryClientProvider } from "@tanstack/react-query"
import { queryClient } from "./queryClient"

interface ProvidersProps {
  children: React.ReactNode;
}

export const Providers = ({ children }: ProvidersProps) => {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}
