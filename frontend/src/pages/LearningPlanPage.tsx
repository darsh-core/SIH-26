import React from "react"
import { useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { 
  Map, 
  Plus, 
  Trash2, 
  ExternalLink, 
  CheckCircle, 
  Clock, 
  BookOpen, 
  Lock, 
  FileText,
  HelpCircle,
  Play
} from "lucide-react"

import { useAuthStore } from "../store/authStore"
import { learningPlanApi } from "../services/learningPlanApi"
import { assessmentApi } from "../services/assessmentApi"
import { Card, CardContent, CardHeader, CardTitle, Badge, Button, Progress } from "../components/ui/Primitives"
import { formatDuration } from "../lib/utils"

export const LearningPlanPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const userId = user?.id || "";

  // 1. Fetch user's learning plans
  const { 
    data: plans, 
    isLoading: plansLoading, 
    error: plansError, 
    refetch 
  } = useQuery({
    queryKey: ["learning-plans", userId],
    queryFn: () => learningPlanApi.getLearningPlans(userId),
    enabled: !!userId
  });

  // 2. Fetch assessments list to find the seeded Sampling Assessment
  const { 
    data: assessments 
  } = useQuery({
    queryKey: ["assessments-list"],
    queryFn: () => assessmentApi.getAssessments()
  });

  // 3. Generate plan mutation
  const generatePlanMutation = useMutation({
    mutationFn: () => learningPlanApi.generateLearningPlan(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["learning-plans"] });
    }
  });

  // 4. Delete item mutation
  const deleteItemMutation = useMutation({
    mutationFn: ({ planId, itemId }: { planId: string, itemId: string }) => 
      learningPlanApi.deletePlanItem(planId, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["learning-plans"] });
    }
  });

  if (plansLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <svg className="animate-spin h-10 w-10 text-gov-blue-500" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
        <span className="text-sm font-semibold text-slate-500">Loading your learning roadmap...</span>
      </div>
    );
  }

  const activePlan = plans && plans.length > 0 ? plans[0] : null;

  // Find the seeded Sampling assessment
  const samplingQuiz = assessments?.items?.find(a => 
    a.title.includes("Sampling") || a.description?.includes("Sampling")
  );

  return (
    <div className="space-y-6">
      {/* Header Block */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-950">My Learning Plan</h1>
          <p className="text-sm text-slate-500">
            Sequenced week-by-week learning roadmap generated to cover critical competency gaps.
          </p>
        </div>
        {activePlan && (
          <Badge variant="success" className="px-3 py-1 font-bold text-xs shrink-0 self-start md:self-auto">
            {activePlan.status} ROADMAP ACTIVE
          </Badge>
        )}
      </div>

      {!activePlan ? (
        /* Empty State CTA */
        <Card className="border-dashed border-slate-300 p-12 text-center max-w-2xl mx-auto my-8">
          <CardContent className="space-y-6">
            <Map className="h-16 w-16 text-slate-300 mx-auto stroke-[1.25]" />
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-slate-800">No active learning plan</h3>
              <p className="text-sm text-slate-500 leading-normal">
                An active plan coordinates your study path week-by-week, addressing your priority competency gaps with course modules and verified assessments.
              </p>
            </div>
            <Button 
              variant="primary" 
              className="px-6 py-2.5 font-bold"
              onClick={() => generatePlanMutation.mutate()}
              isLoading={generatePlanMutation.isPending}
            >
              <Plus className="h-5 w-5 mr-2" />
              Generate Skill Development Plan
            </Button>
          </CardContent>
        </Card>
      ) : (
        /* Active Plan View */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Left: Journey Timeline Steps */}
          <div className="lg:col-span-2 space-y-6">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Learning Journey Path</h2>
            
            <div className="space-y-8 relative before:absolute before:inset-y-0 before:left-6 before:w-[2px] before:bg-slate-200">
              
              {/* Iterating course items */}
              {activePlan.items.map((item, index) => {
                const title = item.item_type === "COURSE" ? item.course?.title : item.training_program?.title;
                const provider = item.item_type === "COURSE" ? "iGOT" : "NSSTA";
                const durationVal = item.item_type === "COURSE" 
                  ? item.course?.duration_minutes || 0 
                  : (item.training_program?.duration_days || 0) * 8 * 60;
                
                const difficulty = item.item_type === "COURSE" ? item.course?.difficulty : "Intermediate";
                const isCompleted = item.status === "COMPLETED";

                return (
                  <div key={item.id} className="relative pl-12 flex gap-4 items-start group">
                    {/* Circle Node Icon */}
                    <div className={`absolute left-2.5 w-7 h-7 rounded-full border-2 flex items-center justify-center font-bold text-xs shadow-xs z-10 transition-colors ${
                      isCompleted 
                        ? "bg-emerald-500 border-emerald-600 text-white" 
                        : "bg-white border-gov-blue-500 text-gov-blue-500"
                    }`}>
                      {isCompleted ? <CheckCircle className="h-4 w-4" /> : index + 1}
                    </div>

                    {/* Step Card Content */}
                    <Card className="flex-1 hover:border-slate-300 transition-all">
                      <CardContent className="p-5 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                        <div className="space-y-1.5 min-w-0">
                          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">
                            STEP {index + 1} · {item.item_type}
                          </span>
                          <h4 className="text-sm font-bold text-slate-900 leading-snug truncate">{title}</h4>
                          <div className="flex items-center gap-3 text-xs text-slate-500">
                            <Badge variant="outline" className="px-1.5 py-0 bg-slate-50">
                              {provider}
                            </Badge>
                            <span>{difficulty}</span>
                            <div className="w-1 h-1 rounded-full bg-slate-300" />
                            <span className="flex items-center gap-1">
                              <Clock className="h-3.5 w-3.5" /> {formatDuration(durationVal)}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto">
                          <button
                            onClick={() => deleteItemMutation.mutate({ planId: activePlan.id, itemId: item.id })}
                            disabled={deleteItemMutation.isPending}
                            className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors"
                            title="Remove from Journey"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                          
                          {item.item_type === "COURSE" ? (
                            <Button
                              size="sm"
                              onClick={() => navigate(`/demo-igot/courses/${item.course_id}`)}
                              className="bg-gov-blue-600 hover:bg-gov-blue-700 text-white font-medium flex items-center gap-1.5 text-xs h-8 px-3"
                            >
                              <Play className="h-3 w-3 fill-current" />
                              Open in iGOT Player
                            </Button>
                          ) : (
                            <a
                              href={`https://nssta.gov.in/programs/${item.training_program?.code}`}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <Button variant="outline" size="sm" className="text-xs h-8 px-3">
                                Open Resource <ExternalLink className="h-3 w-3 ml-1" />
                              </Button>
                            </a>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                );
              })}

              {/* Assessment Checkpoint node */}
              <div className="relative pl-12 flex gap-4 items-start">
                <div className="absolute left-2.5 w-7 h-7 rounded-full bg-amber-500 border-2 border-amber-600 text-white flex items-center justify-center font-bold text-xs shadow-xs z-10">
                  <FileText className="h-4 w-4" />
                </div>
                
                <Card className="flex-1 border-amber-200 bg-amber-50/10">
                  <CardContent className="p-5 flex flex-col sm:flex-row justify-between sm:items-center gap-4">
                    <div className="space-y-1.5 min-w-0">
                      <span className="text-[10px] text-amber-600 font-bold uppercase tracking-wider">
                        FINAL STEP · CHECKPOINT
                      </span>
                      <h4 className="text-sm font-bold text-slate-900 leading-snug">
                        {samplingQuiz?.title || "Sampling Methodology Core Assessment"}
                      </h4>
                      <p className="text-xs text-slate-500 leading-normal">
                        Submit this quiz to verify your skill improvements and close your competency gap.
                      </p>
                    </div>

                    <div className="shrink-0 self-end sm:self-auto">
                      {samplingQuiz ? (
                        <Button 
                          variant="primary" 
                          className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold border-amber-600"
                          onClick={() => navigate(`/assessments/${samplingQuiz.id}`)}
                        >
                          <Play className="h-3.5 w-3.5 mr-1.5 stroke-[3]" />
                          Start Quiz
                        </Button>
                      ) : (
                        <span className="text-xs text-slate-400 italic">No quiz found</span>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

            </div>
          </div>

          {/* Right: Summary Roadmap progress panel */}
          <div className="lg:col-span-1 space-y-6">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Roadmap Summary</h2>
            
            <Card className="bg-white border-slate-200">
              <CardContent className="p-6 space-y-6">
                <div className="space-y-2">
                  <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Title</h3>
                  <p className="text-sm font-semibold text-slate-900 leading-snug">{activePlan.title}</p>
                  <p className="text-xs text-slate-500 leading-relaxed">{activePlan.description}</p>
                </div>

                <div className="space-y-2.5">
                  <div className="flex justify-between text-xs font-semibold text-slate-500">
                    <span>Journey Items Completeness</span>
                    <span>0 / {activePlan.items.length + 1} Steps</span>
                  </div>
                  <Progress value={0} />
                </div>

                <div className="bg-slate-50 border border-slate-200/50 rounded-md p-4 space-y-3 text-xs leading-normal">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider border-b border-slate-100 pb-2">Roadmap Stats</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-slate-400 block">Total Courses:</span>
                      <span className="font-bold text-slate-700">
                        {activePlan.items.filter(i => i.item_type === "COURSE").length} Online
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-400 block">Academy Programs:</span>
                      <span className="font-bold text-slate-700">
                        {activePlan.items.filter(i => i.item_type === "TRAINING_PROGRAM").length} Offline
                      </span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-slate-400 block">Assessment Target:</span>
                      <span className="font-bold text-gov-blue-500">STAT_SAMPLING Level 4.0 Verification</span>
                    </div>
                  </div>
                </div>

              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
