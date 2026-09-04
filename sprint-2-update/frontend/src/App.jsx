import React, { useState, useEffect } from 'react';
import { Briefcase, BookOpen, Brain, Activity, UserCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function App() {
  const [step, setStep] = useState('welcome');
  const [roles, setRoles] = useState([]);
  const [formData, setFormData] = useState({ name: '', department: '', experience_years: 0, role_id: '' });
  const [user, setUser] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [answers, setAnswers] = useState({});
  const [dashboard, setDashboard] = useState(null);

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8001/roles')
      .then(res => res.json())
      .then(data => setRoles(data));
  }, []);

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    const res = await fetch('http://localhost:8001/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(formData)
    });
    const data = await res.json();
    setUser(data);
    setStep('assessment');
    
    // Fetch real assessment (may take a few seconds with Ollama)
    const assessRes = await fetch(`http://localhost:8001/users/${data.id}/assessment`);
    const assessData = await assessRes.json();
    setAssessment(assessData);
    setLoading(false);
  };

  const submitAssessment = async () => {
    const formattedAnswers = Object.keys(answers).map(qId => ({
      question_id: parseInt(qId),
      selected_option: answers[qId]
    }));

    await fetch(`http://localhost:8001/users/${user.id}/assessment/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        session_id: assessment.session_id,
        answers: formattedAnswers 
      })
    });

    const res = await fetch(`http://localhost:8001/users/${user.id}/dashboard`);
    const data = await res.json();
    setDashboard(data);
    setStep('dashboard');
  };

  if (step === 'welcome') {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800 p-8 rounded-xl shadow-2xl max-w-md w-full border border-slate-700">
          <div className="flex items-center gap-3 mb-6">
            <Brain className="w-8 h-8 text-blue-400" />
            <h1 className="text-2xl font-bold text-white">SkillStat AI</h1>
          </div>
          <p className="text-slate-400 mb-6">Create your profile to start your MoSPI competency journey.</p>
          
          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Full Name</label>
              <input required type="text" className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white" value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Department</label>
              <input required type="text" className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white" value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Years of Experience</label>
              <input required type="number" className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white" value={formData.experience_years} onChange={e => setFormData({...formData, experience_years: parseInt(e.target.value)})} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Target Role</label>
              <select required className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white" value={formData.role_id} onChange={e => setFormData({...formData, role_id: parseInt(e.target.value)})}>
                <option value="">Select a role...</option>
                {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
              </select>
            </div>
            <button type="submit" className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded-lg mt-4 transition-colors">Start Assessment</button>
          </form>
        </div>
      </div>
    );
  }

  if (step === 'assessment' && !assessment && loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="text-center">
          <Brain className="w-16 h-16 text-blue-400 animate-pulse mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Preparing your personalized assessment...</h2>
          <p className="text-slate-400">Our AI is generating competency questions specifically for your target role.</p>
        </div>
      </div>
    );
  }

  if (step === 'assessment' && assessment) {
    return (
      <div className="min-h-screen bg-slate-900 p-8">
        <div className="max-w-3xl mx-auto bg-slate-800 p-8 rounded-xl border border-slate-700 shadow-xl">
          <div className="flex justify-between items-center mb-8 pb-4 border-b border-slate-700">
            <h2 className="text-2xl font-bold text-white">Competency Discovery</h2>
            <span className="text-blue-400 bg-blue-400/10 px-3 py-1 rounded-full text-sm font-medium">Question 1 of {assessment.questions.length}</span>
          </div>
          
          {assessment.questions.map((q, idx) => (
            <div key={q.id} className="mb-8">
              <div className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">{q.skill}</div>
              <h3 className="text-lg text-white mb-4">{q.question}</h3>
              <div className="space-y-2">
                {q.options.map((opt, index) => (
                  <label key={opt} className="flex items-center gap-3 p-4 border border-slate-700 rounded-lg hover:bg-slate-700/50 cursor-pointer transition-colors text-slate-300">
                    <input type="radio" name={`q_${q.id}`} value={index} onChange={() => setAnswers({...answers, [q.id]: index})} className="w-4 h-4 text-blue-500 bg-slate-800 border-slate-600 focus:ring-blue-500" />
                    <span>{opt}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
          
          <div className="flex justify-end mt-8 pt-6 border-t border-slate-700">
            <button onClick={submitAssessment} className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-6 rounded-lg transition-colors">Submit & Analyze Gaps</button>
          </div>
        </div>
      </div>
    );
  }

  if (step === 'dashboard' && dashboard) {
    const chartData = dashboard.gaps.map(g => ({
      name: g.skill,
      Current: g.current_level,
      Required: g.required_level,
    }));

    return (
      <div className="min-h-screen bg-slate-900 p-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="bg-slate-800 rounded-xl p-6 mb-8 border border-slate-700 shadow-lg flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center">
                <UserCircle className="w-8 h-8 text-blue-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Hello, {dashboard.user_name}</h1>
                <p className="text-slate-400">{dashboard.department}</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium text-slate-400 uppercase tracking-wider">Overall Competency Match</div>
              <div className="text-3xl font-bold text-green-400 mt-1">{dashboard.overall_competency}%</div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column: Gaps & Chart */}
            <div className="lg:col-span-2 space-y-8">
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
                <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-400" /> Competency Gap Analysis
                </h2>
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                      <XAxis dataKey="name" stroke="#94a3b8" />
                      <YAxis stroke="#94a3b8" domain={[0, 5]} ticks={[1, 2, 3, 4, 5]} />
                      <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                      <Legend />
                      <Bar dataKey="Current" fill="#3b82f6" name="Your Level" />
                      <Bar dataKey="Required" fill="#10b981" name="Required Level" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Gap List */}
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg">
                <h2 className="text-xl font-bold text-white mb-6">Priority Focus Areas</h2>
                <div className="space-y-4">
                  {dashboard.gaps.map(gap => (
                    <div key={gap.skill_id} className="flex items-center justify-between p-4 bg-slate-900 rounded-lg border border-slate-700">
                      <div>
                        <div className="font-bold text-white">{gap.skill}</div>
                        <div className="text-sm text-slate-400 mt-1">
                          Gap: Level {gap.current_level} → Level {gap.required_level}
                        </div>
                      </div>
                      <div>
                          <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                            gap.status === 'READY' ? 'bg-green-100 text-green-800' :
                            gap.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {gap.status}
                          </span>
                        {gap.priority === "HIGH" ? (
                          <span className="text-red-400 bg-red-400/10 px-3 py-1 rounded-full text-sm font-bold">🔴 High Priority</span>
                        ) : gap.priority === "MEDIUM" ? (
                          <span className="text-yellow-400 bg-yellow-400/10 px-3 py-1 rounded-full text-sm font-bold">🟡 Medium Priority</span>
                        ) : (
                          <span className="text-green-400 bg-green-400/10 px-3 py-1 rounded-full text-sm font-bold">🟢 Good Standing</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right Column: Recommended Courses */}
            <div className="space-y-8">
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 shadow-lg h-full">
                <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-indigo-400" /> Recommended Learning Path
                </h2>
                
                {dashboard.recommendations.length > 0 ? (
                  <div className="space-y-6">
                    {dashboard.recommendations.map((rec, idx) => (
                      <div key={rec.course_id} className="relative pl-6 pb-6 border-l-2 border-indigo-500/30 last:border-0 last:pb-0">
                        <div className="absolute left-[-9px] top-0 w-4 h-4 rounded-full bg-indigo-500 shadow-[0_0_10px_rgba(99,102,241,0.5)] border-2 border-slate-800"></div>
                        <div className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">Step {idx + 1}</div>
                        <h3 className="text-lg font-bold text-white mb-1">{rec.title}</h3>
                        <div className="text-xs text-slate-400 mb-3 flex items-center gap-2">
                          <Briefcase className="w-3 h-3" /> {rec.provider}
                        </div>
                        <div className="bg-indigo-500/10 border border-indigo-500/20 p-3 rounded-lg text-sm text-indigo-200">
                          <strong>Why this course?</strong><br />
                          {rec.reason}
                        </div>
                        <button className="mt-3 text-sm text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1 transition-colors">
                          Enroll on iGOT <span className="text-lg leading-none">→</span>
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-400 italic">No competency gaps found! You are fully qualified.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default App;
