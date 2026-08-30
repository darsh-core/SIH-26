import React, { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { useNavigate } from "react-router-dom"
import { Upload, FileText, Settings, Eye, HelpCircle } from "lucide-react"

import { documentApi } from "../services/documentApi"
import { Button, Card, Badge, Spinner } from "../components/ui/Primitives"

export const DocumentManagerPage = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["documents", page],
    queryFn: () => documentApi.listDocuments(page, 10),
    refetchInterval: 5000 // Poll every 5 seconds for processing statuses
  });

  const { data: detailsDoc, isLoading: detailsLoading } = useQuery({
    queryKey: ["documentDetails", selectedDocId],
    queryFn: () => documentApi.getDocument(selectedDocId!),
    enabled: !!selectedDocId
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "INDEXED":
        return <Badge variant="success">INDEXED</Badge>;
      case "PROCESSING":
        return <Badge variant="warning">PROCESSING</Badge>;
      case "UPLOADED":
        return <Badge variant="info">UPLOADED</Badge>;
      case "FAILED":
        return <Badge variant="error">FAILED</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gov-blue-900">Document Intelligence Matrix</h1>
          <p className="text-slate-500 mt-1">
            Upload statistics manuals and training handouts to generate grounded assessment questionnaires.
          </p>
        </div>
        <Button onClick={() => navigate("/documents/upload")} className="flex items-center gap-2">
          <Upload className="h-4 w-4" />
          Upload Manual
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table view */}
        <div className="lg:col-span-2">
          <Card className="p-0 overflow-hidden">
            <div className="p-4 bg-slate-50 border-b border-slate-200">
              <h2 className="font-semibold text-slate-700">Available Learning Materials</h2>
            </div>
            
            {isLoading ? (
              <div className="p-8 text-center flex justify-center">
                <Spinner size="lg" />
              </div>
            ) : !data?.items || data.items.length === 0 ? (
              <div className="p-12 text-center text-slate-400">
                <FileText className="h-12 w-12 mx-auto mb-2 text-slate-300" />
                No documents uploaded yet. Upload a PDF to start indexing.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200 text-xs text-slate-500 uppercase">
                    <tr>
                      <th className="p-4">Document Title</th>
                      <th className="p-4">Type</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Chunks</th>
                      <th className="p-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {data.items.map((doc) => (
                      <tr key={doc.id} className="hover:bg-slate-50/50 transition-colors">
                        <td className="p-4 font-medium text-slate-900">{doc.title}</td>
                        <td className="p-4">
                          <span className="px-2 py-0.5 bg-slate-100 rounded text-xs text-slate-600 font-mono">
                            {doc.file_type}
                          </span>
                        </td>
                        <td className="p-4">{getStatusBadge(doc.status)}</td>
                        <td className="p-4 text-slate-600">{doc.chunk_count}</td>
                        <td className="p-4 text-right space-x-2">
                          <Button 
                            variant="secondary" 
                            size="sm"
                            onClick={() => setSelectedDocId(doc.id)}
                            className="inline-flex items-center gap-1"
                          >
                            <Eye className="h-3.5 w-3.5" />
                            View
                          </Button>
                          <Button 
                            variant="primary" 
                            size="sm"
                            disabled={doc.status !== "INDEXED"}
                            onClick={() => navigate(`/documents/${doc.id}/generate`)}
                            className="inline-flex items-center gap-1"
                          >
                            <Settings className="h-3.5 w-3.5" />
                            Generate MCQs
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            
            {data && data.total > 10 && (
              <div className="p-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between">
                <Button 
                  variant="secondary" 
                  size="sm" 
                  disabled={page === 1}
                  onClick={() => setPage(p => p - 1)}
                >
                  Previous
                </Button>
                <span className="text-xs text-slate-500">Page {page} of {Math.ceil(data.total / 10)}</span>
                <Button 
                  variant="secondary" 
                  size="sm" 
                  disabled={page >= Math.ceil(data.total / 10)}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </Card>
        </div>

        {/* Details Panel */}
        <div className="lg:col-span-1">
          <Card className="h-full">
            <h2 className="text-lg font-bold text-gov-blue-900 border-b border-slate-100 pb-3">
              Document Analysis Panel
            </h2>
            
            {!selectedDocId ? (
              <div className="py-20 text-center text-slate-400 text-sm">
                <HelpCircle className="h-10 w-10 mx-auto mb-2 text-slate-300" />
                Select a document from the left list to audit details and mapped competencies.
              </div>
            ) : detailsLoading ? (
              <div className="py-20 text-center flex justify-center">
                <Spinner size="md" />
              </div>
            ) : detailsDoc ? (
              <div className="mt-4 space-y-4 text-sm">
                <div>
                  <span className="text-xs text-slate-400 uppercase tracking-wider block">Title</span>
                  <span className="font-semibold text-slate-800">{detailsDoc.title}</span>
                </div>
                <div>
                  <span className="text-xs text-slate-400 uppercase tracking-wider block">File Name</span>
                  <span className="text-slate-600 font-mono truncate block">{detailsDoc.filename}</span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-slate-400 uppercase tracking-wider block">Status</span>
                    <span className="mt-1 block">{getStatusBadge(detailsDoc.status)}</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 uppercase tracking-wider block">Index count</span>
                    <span className="mt-1 font-semibold text-slate-800">{detailsDoc.chunk_count} Chunks</span>
                  </div>
                </div>
                
                <div className="border-t border-slate-100 pt-4">
                  <h3 className="font-semibold text-gov-blue-800 mb-2">Detected Competencies</h3>
                  
                  {detailsDoc.detected_competencies?.length === 0 ? (
                    <p className="text-slate-400 text-xs">No direct competency frameworks mapped.</p>
                  ) : (
                    <div className="space-y-3">
                      {detailsDoc.detected_competencies?.map((comp) => (
                        <div key={comp.competency_id} className="p-3 bg-slate-50 border border-slate-150 rounded-lg">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-gov-blue-700">{comp.competency_code}</span>
                            <Badge variant={comp.mapping_method === "DETERMINISTIC" ? "info" : "warning"}>
                              {comp.mapping_method}
                            </Badge>
                          </div>
                          <p className="font-medium text-slate-800 text-xs mt-1">{comp.competency_name}</p>
                          <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                            <span>Confidence Mapping:</span>
                            <span className="font-bold text-slate-700">{comp.confidence * 100}%</span>
                          </div>
                          <div className="w-full bg-slate-200 h-1.5 rounded-full mt-1 overflow-hidden">
                            <div className="bg-gov-blue-600 h-full rounded-full" style={{ width: `${comp.confidence * 100}%` }}></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : null}
          </Card>
        </div>
      </div>
    </div>
  );
};
