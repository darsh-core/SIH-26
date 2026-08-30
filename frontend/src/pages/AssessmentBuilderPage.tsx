import React, { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { FileText, ArrowLeft, BrainCircuit } from "lucide-react"

import { documentApi } from "../services/documentApi"
import { Button, Card, Spinner } from "../components/ui/Primitives"

export const AssessmentBuilderPage = () => {
  const navigate = useNavigate();
  const [selectedDocId, setSelectedDocId] = useState<string>("");

  const { data, isLoading } = useQuery({
    queryKey: ["documentsList"],
    queryFn: () => documentApi.listDocuments(1, 50)
  });

  const handleProceed = () => {
    if (selectedDocId) {
      navigate(`/documents/${selectedDocId}/generate`);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={() => navigate("/dashboard")}>
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>
        <h1 className="text-2xl font-bold text-gov-blue-900">Assessment Builder Portal</h1>
      </div>

      <Card className="p-6 space-y-6">
        <div className="flex items-start gap-4">
          <BrainCircuit className="h-10 w-10 text-gov-blue-500 flex-shrink-0" />
          <div>
            <h2 className="font-semibold text-slate-800 text-base">Select Base Learning Material</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Select an indexed reference handbook to extract grounded evaluation questions.
            </p>
          </div>
        </div>

        {isLoading ? (
          <div className="py-8 text-center flex justify-center">
            <Spinner size="md" />
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="text-xs font-bold text-slate-500 block mb-1">Indexed Source Document</label>
              <select 
                className="w-full border border-slate-350 rounded-md p-2 text-sm bg-white"
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
              >
                <option value="">Choose a manual...</option>
                {data?.items?.filter(d => d.status === "INDEXED").map(d => (
                  <option key={d.id} value={d.id}>{d.title} ({d.file_type})</option>
                ))}
              </select>
            </div>

            <Button 
              onClick={handleProceed} 
              className="w-full flex items-center justify-center gap-2"
              disabled={!selectedDocId}
            >
              Configure Question Generation
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
};
