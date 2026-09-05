import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { 
  Sparkles, 
  X, 
  Send, 
  RotateCcw, 
  BookOpen, 
  ChevronDown, 
  ChevronUp, 
  Bot, 
  User, 
  ShieldCheck,
  Wheat,
  TrendingUp,
  Layers,
  HelpCircle,
  ExternalLink,
  Info,
  Brain,
  Target,
  Copy,
  Check,
  Maximize2,
  Minimize2
} from "lucide-react";
import { copilotApi, ChatMessage, CopilotCitation, QuickPrompt } from "../../services/copilotApi";
import { useAuthStore } from "../../store/authStore";
import { cn } from "../../lib/utils";

export const CopilotDrawer: React.FC = () => {
  const { user } = useAuthStore();
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Array<{
    role: "user" | "assistant";
    content: string;
    citations?: CopilotCitation[];
    grounded?: boolean;
    timestamp: Date;
  }>>([]);
  const [quickPrompts, setQuickPrompts] = useState<QuickPrompt[]>([]);
  const [expandedCitationIdx, setExpandedCitationIdx] = useState<string | null>(null);
  const [isWide, setIsWide] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch quick prompts on mount
  useEffect(() => {
    copilotApi.getQuickPrompts()
      .then(res => setQuickPrompts(res))
      .catch(err => console.warn("Failed to fetch quick prompts", err));
  }, []);

  // Auto-scroll on new messages
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading, isOpen]);

  // Listen for external open events (e.g. from Recommendation cards or Dashboard "Ask Copilot")
  useEffect(() => {
    const handleOpenCopilot = (e: any) => {
      setIsOpen(true);
      if (e.detail?.query) {
        setTimeout(() => {
          handleSend(e.detail.query);
        }, 250);
      }
    };
    window.addEventListener("open-copilot", handleOpenCopilot);
    return () => window.removeEventListener("open-copilot", handleOpenCopilot);
  }, [user]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen]);

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend || inputMessage).trim();
    if (!query || loading) return;

    const userTimestamp = new Date();
    const newHistory: ChatMessage[] = messages.map(m => ({ role: m.role, content: m.content }));

    setMessages(prev => [...prev, {
      role: "user",
      content: query,
      timestamp: userTimestamp
    }]);

    setInputMessage("");
    setLoading(true);

    try {
      const response = await copilotApi.chat({
        message: query,
        user_id: user?.id,
        history: newHistory,
        session_id: `mospi_copilot_${user?.id || "guest"}`
      });

      setMessages(prev => [...prev, {
        role: "assistant",
        content: response.reply,
        citations: response.citations,
        grounded: response.grounded,
        timestamp: new Date()
      }]);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "⚠️ **Offline / Inference Notice:** I could not reach the local Llama engine right now. Please ensure Ollama is active on port 11434 with `llama3.2` installed.",
        grounded: false,
        timestamp: new Date()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setExpandedCitationIdx(null);
  };

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const renderIcon = (iconName?: string) => {
    switch (iconName) {
      case "Brain": return <Brain className="w-3.5 h-3.5 text-indigo-500" />;
      case "Target": return <Target className="w-3.5 h-3.5 text-rose-500" />;
      case "Wheat": return <Wheat className="w-3.5 h-3.5 text-amber-500" />;
      case "TrendingUp": return <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />;
      case "Layers": return <Layers className="w-3.5 h-3.5 text-blue-500" />;
      case "ShieldCheck": return <ShieldCheck className="w-3.5 h-3.5 text-purple-500" />;
      default: return <HelpCircle className="w-3.5 h-3.5 text-indigo-500" />;
    }
  };

  return (
    <>
      {/* 1. Global Floating Launcher Button */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 z-40 flex items-center gap-2 animate-bounce-subtle">
          <button
            onClick={() => setIsOpen(true)}
            className="group relative flex items-center gap-2.5 px-4 py-3 bg-gradient-to-r from-gov-blue-500 via-indigo-600 to-blue-600 text-white rounded-full shadow-xl hover:shadow-indigo-500/40 hover:scale-105 active:scale-95 transition-all duration-300 border border-white/20 backdrop-blur-sm cursor-pointer"
            aria-label="Open MoSPI AI Copilot"
          >
            <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-emerald-500 border-2 border-white"></span>
            </span>

            <div className="p-1 rounded-full bg-white/15 group-hover:bg-white/25 transition-colors">
              <Sparkles className="w-5 h-5 text-gov-gold animate-pulse" />
            </div>

            <div className="text-left pr-1">
              <div className="text-xs font-bold tracking-tight text-white flex items-center gap-1.5">
                Vivi AI
                <span className="text-[9px] uppercase px-1.5 py-0.2 bg-white/20 rounded font-semibold text-slate-100">
                  MoSPI Copilot
                </span>
              </div>
              <p className="text-[10px] text-blue-100/90 font-medium">Ask Statistical Mentor</p>
            </div>
          </button>
        </div>
      )}

      {/* 2. Slide-Over Copilot Window */}
      {isOpen && (
        <div className={cn(
          "fixed bottom-4 right-4 sm:bottom-6 sm:right-6 h-[640px] max-h-[90vh] z-50 flex flex-col rounded-2xl bg-white shadow-2xl border border-slate-200/90 overflow-hidden backdrop-blur-xl transition-all duration-300 animate-in fade-in slide-in-from-bottom-4",
          isWide ? "w-[95vw] sm:w-[680px] md:w-[740px]" : "w-[95vw] sm:w-[440px]"
        )}>
          
          {/* Header */}
          <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white px-4 py-3.5 flex items-center justify-between border-b border-indigo-900/50 shrink-0">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-blue-400 p-0.5 shadow-md flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-slate-900"></span>
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white tracking-tight">Vivi • MoSPI Copilot</h3>
                  <span className="text-[9px] font-semibold bg-indigo-500/30 text-indigo-200 border border-indigo-400/30 px-1.5 py-0.5 rounded">
                    NSSTA AI
                  </span>
                </div>
                <p className="text-[10px] text-slate-300 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3 text-emerald-400" />
                  100% Local • Llama 3.2 • Air-Gapped
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsWide(!isWide)}
                title={isWide ? "Collapse view (440px)" : "Expand view for tables (740px)"}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800/80 rounded-lg transition-colors hidden sm:inline-flex cursor-pointer"
                aria-label="Toggle wide view"
              >
                {isWide ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={handleClear}
                title="Reset conversation"
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800/80 rounded-lg transition-colors cursor-pointer"
                aria-label="Clear chat"
              >
                <RotateCcw className="w-4 h-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800/80 rounded-lg transition-colors cursor-pointer"
                aria-label="Close copilot"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Grounding Info Strip */}
          <div className="bg-indigo-50/70 border-b border-indigo-100 px-3 py-1.5 flex items-center justify-between text-[11px] text-indigo-800 shrink-0">
            <span className="flex items-center gap-1.5 font-medium">
              <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
              Grounded on MoSPI Guidelines (pgvector 384-D)
            </span>
            <span className="text-[10px] font-mono text-indigo-500 font-semibold bg-white/80 px-1.5 py-0.5 rounded border border-indigo-200/60">
              RAG Active
            </span>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/40">
            {messages.length === 0 && (
              <div className="py-2 space-y-4">
                {/* Welcome Card */}
                <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-xs space-y-2">
                  <div className="flex items-center gap-2 text-indigo-600">
                    <Sparkles className="w-4 h-4" />
                    <span className="text-xs font-bold uppercase tracking-wider">Namaste, Statistical Officer!</span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    I am <strong>Vivi</strong>, your AI Statistical Mentor. You can ask me to explain survey methodologies, clarify sampling errors, calculate index numbers, or quiz you on MoSPI manuals.
                  </p>
                </div>

                {/* Quick Prompts */}
                {quickPrompts.length > 0 && (
                  <div className="space-y-2">
                    <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider px-1">
                      Suggested Official Inquiries
                    </p>
                    <div className="grid grid-cols-1 gap-1.5">
                      {quickPrompts.map((qp, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSend(qp.prompt)}
                          className="text-left p-2.5 rounded-lg bg-white hover:bg-indigo-50/80 border border-slate-200/90 hover:border-indigo-200 text-xs text-slate-700 hover:text-indigo-900 transition-all flex items-start gap-2.5 group cursor-pointer shadow-2xs"
                        >
                          <div className="mt-0.5 p-1 rounded bg-slate-100 group-hover:bg-indigo-100 transition-colors">
                            {renderIcon(qp.icon)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-[11px] text-slate-800 group-hover:text-indigo-900">
                              {qp.title}
                            </div>
                            <div className="text-[10px] text-slate-500 truncate">
                              {qp.prompt}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Render Messages */}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={cn(
                  "flex flex-col space-y-1.5",
                  msg.role === "user" ? "items-end" : "items-start w-full"
                )}
              >
                <div
                  className={cn(
                    "rounded-2xl px-3.5 py-2.5 text-xs leading-relaxed shadow-xs transition-all",
                    msg.role === "user"
                      ? "max-w-[85%] bg-gradient-to-r from-gov-blue-500 to-indigo-600 text-white rounded-br-xs font-medium"
                      : "w-full max-w-[98%] bg-white text-slate-800 border border-slate-200/90 rounded-bl-xs shadow-xs"
                  )}
                >
                  {msg.role === "user" ? (
                    <div className="whitespace-pre-wrap">
                      {msg.content}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between pb-1.5 border-b border-slate-100 text-[10px]">
                        <span className="font-semibold text-indigo-950 flex items-center gap-1.5">
                          <Bot className="w-3.5 h-3.5 text-indigo-600" />
                          MoSPI Advisory
                        </span>
                        <button
                          onClick={() => handleCopy(msg.content, idx)}
                          className="flex items-center gap-1 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 px-1.5 py-0.5 rounded transition-colors cursor-pointer"
                          title="Copy response"
                        >
                          {copiedIdx === idx ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-600" />
                              <span className="text-[9px] text-emerald-600 font-medium">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span className="text-[9px]">Copy</span>
                            </>
                          )}
                        </button>
                      </div>

                      <div className="text-slate-800 text-xs">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            table: ({ node, ...props }) => (
                              <div className="my-2.5 overflow-x-auto rounded-xl border border-slate-200/90 bg-white shadow-2xs">
                                <table className="w-full text-left border-collapse text-[11px]" {...props} />
                              </div>
                            ),
                            thead: ({ node, ...props }) => (
                              <thead className="bg-slate-50 text-slate-900 font-semibold border-b border-slate-200" {...props} />
                            ),
                            th: ({ node, ...props }) => (
                              <th className="px-3 py-2 text-[10.5px] font-bold text-slate-800 bg-slate-100/80 border-b border-slate-200 text-left whitespace-nowrap" {...props} />
                            ),
                            tbody: ({ node, ...props }) => (
                              <tbody className="divide-y divide-slate-100 bg-white" {...props} />
                            ),
                            tr: ({ node, ...props }) => (
                              <tr className="hover:bg-indigo-50/30 transition-colors" {...props} />
                            ),
                            td: ({ node, ...props }) => (
                              <td className="px-3 py-2 text-[11px] text-slate-700 align-middle leading-snug border-b border-slate-100 last:border-b-0" {...props} />
                            ),
                            h1: ({ node, ...props }) => (
                              <h1 className="text-sm font-bold text-slate-900 mt-3 mb-1.5 flex items-center gap-1.5" {...props} />
                            ),
                            h2: ({ node, ...props }) => (
                              <h2 className="text-xs font-bold text-indigo-950 mt-3 mb-1.5 pb-1 border-b border-indigo-100 flex items-center gap-1.5 tracking-tight" {...props} />
                            ),
                            h3: ({ node, ...props }) => (
                              <h3 className="text-[11.5px] font-bold text-slate-800 mt-2.5 mb-1 flex items-center gap-1 text-indigo-900" {...props} />
                            ),
                            h4: ({ node, ...props }) => (
                              <h4 className="text-[11px] font-semibold text-slate-700 mt-2 mb-0.5" {...props} />
                            ),
                            p: ({ node, ...props }) => (
                              <p className="mb-2 last:mb-0 leading-relaxed text-xs text-slate-700" {...props} />
                            ),
                            ul: ({ node, ...props }) => (
                              <ul className="list-disc list-outside ml-4 space-y-1 my-2 text-xs text-slate-700" {...props} />
                            ),
                            ol: ({ node, ...props }) => (
                              <ol className="list-decimal list-outside ml-4 space-y-1 my-2 text-xs text-slate-700" {...props} />
                            ),
                            li: ({ node, ...props }) => (
                              <li className="leading-relaxed pl-0.5" {...props} />
                            ),
                            strong: ({ node, ...props }) => (
                              <strong className="font-semibold text-slate-900" {...props} />
                            ),
                            em: ({ node, ...props }) => (
                              <em className="italic text-slate-800" {...props} />
                            ),
                            blockquote: ({ node, ...props }) => (
                              <blockquote className="border-l-2 border-indigo-500 bg-indigo-50/60 pl-3 pr-2 py-1.5 my-2 text-xs italic text-indigo-950 rounded-r-md" {...props} />
                            ),
                            code: ({ node, inline, className, children, ...props }: any) => {
                              if (inline) {
                                return (
                                  <code className="px-1.5 py-0.5 rounded bg-slate-100 font-mono text-[10.5px] text-indigo-700 border border-slate-200/80 font-medium" {...props}>
                                    {children}
                                  </code>
                                );
                              }
                              return (
                                <pre className="my-2 p-3 rounded-lg bg-slate-900 text-slate-100 font-mono text-[10.5px] overflow-x-auto border border-slate-800 leading-normal">
                                  <code {...props}>{children}</code>
                                </pre>
                              );
                            },
                            hr: ({ node, ...props }) => (
                              <hr className="my-2.5 border-slate-200" {...props} />
                            ),
                            a: ({ node, ...props }) => (
                              <a className="text-indigo-600 hover:text-indigo-800 underline font-medium" target="_blank" rel="noopener noreferrer" {...props} />
                            )
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}

                  {/* Citations block for Assistant */}
                  {msg.role === "assistant" && msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 pt-2.5 border-t border-slate-100 space-y-1.5">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 flex items-center gap-1">
                        <BookOpen className="w-3 h-3" />
                        Grounded References ({msg.citations.length})
                      </div>

                      <div className="space-y-1">
                        {msg.citations.map((cite, cIdx) => {
                          const citeKey = `${idx}-${cIdx}`;
                          const isExpanded = expandedCitationIdx === citeKey;
                          const locText = cite.page ? `Page ${cite.page}` : (cite.slide ? `Slide ${cite.slide}` : "Manual");

                          return (
                            <div 
                              key={cIdx}
                              className="rounded-md border border-indigo-100 bg-indigo-50/50 p-1.5 text-[10px] text-slate-700"
                            >
                              <div 
                                onClick={() => setExpandedCitationIdx(isExpanded ? null : citeKey)}
                                className="flex items-center justify-between cursor-pointer font-medium text-indigo-900 select-none"
                              >
                                <span className="truncate max-w-[240px]">
                                  📄 {cite.document_title} ({locText})
                                </span>
                                <div className="flex items-center gap-1 text-[9px] text-indigo-600">
                                  <span>{Math.round(cite.similarity * 100)}% match</span>
                                  {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                </div>
                              </div>

                              {isExpanded && (
                                <div className="mt-1.5 pt-1 border-t border-indigo-200/50 text-[10px] text-slate-600 italic bg-white/70 p-1.5 rounded">
                                  "{cite.text_snippet}"
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                <span className="text-[9px] text-slate-400 px-1">
                  {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </span>
              </div>
            ))}

            {/* Thinking / Loading indicator */}
            {loading && (
              <div className="flex items-start gap-2 max-w-[85%]">
                <div className="w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5 text-indigo-600 animate-spin" />
                </div>
                <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-xs px-3.5 py-2.5 shadow-2xs space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium">
                    <span>Vivi is reviewing official manuals...</span>
                  </div>
                  <div className="flex gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.2s]"></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce [animation-delay:0.4s]"></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Footer Input Bar */}
          <div className="p-3 bg-white border-t border-slate-200 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <input
                ref={inputRef}
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask Vivi about statistical methods, manuals, CPI..."
                disabled={loading}
                className="flex-1 bg-slate-100/90 hover:bg-slate-100 focus:bg-white border border-slate-200 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 rounded-xl px-3.5 py-2 text-xs text-slate-800 placeholder:text-slate-400 outline-hidden transition-all"
              />
              <button
                type="submit"
                disabled={loading || !inputMessage.trim()}
                className="p-2 bg-gradient-to-r from-gov-blue-500 to-indigo-600 hover:from-gov-blue-600 hover:to-indigo-700 disabled:opacity-40 text-white rounded-xl shadow-xs transition-all cursor-pointer disabled:cursor-not-allowed shrink-0"
                aria-label="Send message"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>

            <div className="mt-1.5 flex items-center justify-between text-[9px] text-slate-400 px-1">
              <span>On-premise Llama 3.2</span>
              <span>MoSPI DIID Smart Education</span>
            </div>
          </div>

        </div>
      )}
    </>
  );
};
