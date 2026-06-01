import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  X, MessageSquare, Briefcase, FileText, Share2, 
  Send, ExternalLink, RefreshCw, Check, Copy, AlertCircle 
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const IdeaPlaygroundDrawer = ({ idea, onClose }) => {
  const [activeTab, setActiveTab] = useState('details'); // details | chat | landing | export
  const [showOriginalPost, setShowOriginalPost] = useState(false);
  
  // Chat state
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Landing page state
  const [landingPageCopy, setLandingPageCopy] = useState(null);
  const [landingLoading, setLandingLoading] = useState(false);
  const [landingError, setLandingError] = useState(null);

  // Export states
  const [copied, setCopied] = useState(false);

  // Auto scroll chat
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatHistory, chatLoading]);

  // Reset states when idea changes
  useEffect(() => {
    setChatHistory([]);
    setLandingPageCopy(null);
    setLandingError(null);
    setActiveTab('details');
  }, [idea]);

  if (!idea) return null;

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatMessage.trim() || chatLoading) return;

    const userMsg = { role: 'user', content: chatMessage };
    setChatHistory(prev => [...prev, userMsg]);
    setChatMessage('');
    setChatLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/ideas/${idea.id}/chat`, {
        message: userMsg.content,
        history: chatHistory
      });

      const systemMsg = { role: 'assistant', content: response.data.reply };
      setChatHistory(prev => [...prev, systemMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      setChatHistory(prev => [
        ...prev, 
        { role: 'assistant', content: '⚠️ Error generating response. Please check your backend connection.' }
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleGenerateLandingPage = async () => {
    setLandingLoading(true);
    setLandingError(null);
    try {
      const response = await axios.post(`${API_BASE_URL}/ideas/${idea.id}/landing-page`);
      setLandingPageCopy(response.data);
    } catch (err) {
      console.error('Landing page error:', err);
      setLandingError('Failed to generate landing page copy. Please make sure the AI API keys are configured correctly.');
    } finally {
      setLandingLoading(false);
    }
  };

  const generateMarkdown = () => {
    let md = `# Startup Proposal: Solving Pain Point on ${idea.source.toUpperCase()}\n\n`;
    md += `**Problem Statement:** ${idea.problem_summary}\n`;
    md += `**Target Audience:** ${idea.target_audience}\n`;
    md += `**Original Discussion:** [View Thread](${idea.original_url})\n\n`;
    md += `## Market Opportunity Scoring\n`;
    md += `- Urgency: ${idea.urgency_score}/10\n`;
    md += `- Frequency: ${idea.frequency_score}/10\n`;
    md += `- Monetization Potential: ${idea.monetization_score}/10\n`;
    md += `- **Total Opportunity Score:** ${idea.total_score}/30\n\n`;
    md += `## Proposed Digital Product Ideas\n\n`;
    idea.product_ideas.forEach((p, idx) => {
      md += `### ${idx + 1}. ${p.idea} (${p.type})\n`;
      md += `${p.description}\n\n`;
    });

    if (landingPageCopy) {
      md += `## Draft Landing Page Copy (AI-Generated)\n\n`;
      md += `### Headline: ${landingPageCopy.headline}\n`;
      md += `*${landingPageCopy.subheadline}*\n\n`;
      md += `**Call to Action:** ${landingPageCopy.hero_cta}\n\n`;
      md += `### Key Features:\n`;
      landingPageCopy.features.forEach(f => {
        md += `- **${f.title}**: ${f.description}\n`;
      });
      md += `\n### Validation & Launch Plan:\n${landingPageCopy.launch_plan}\n`;
    }

    return md;
  };

  const handleCopyMarkdown = () => {
    const text = generateMarkdown();
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getScoreBadge = (val) => {
    if (val >= 8) return 'text-emerald-400 bg-emerald-950/40 border-emerald-900/50';
    if (val >= 5) return 'text-amber-400 bg-amber-950/40 border-amber-900/50';
    return 'text-slate-400 bg-slate-900/40 border-slate-800';
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-slate-950 border-l border-slate-850 shadow-2xl z-50 flex flex-col h-full animate-in slide-in-from-right duration-300">
      
      {/* Drawer Header */}
      <div className="p-6 border-b border-slate-900 flex justify-between items-center bg-slate-900/50 backdrop-blur">
        <div>
          <span className="text-[10px] font-bold uppercase bg-indigo-600/20 text-indigo-400 px-2.5 py-0.5 rounded border border-indigo-900/30">
            {idea.category}
          </span>
          <h2 className="text-lg font-extrabold text-white mt-2 line-clamp-1">
            {idea.post_title}
          </h2>
        </div>
        <button 
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-900 px-6 bg-slate-950">
        {[
          { id: 'details', label: 'Idea Specs', icon: FileText },
          { id: 'chat', label: 'Co-founder Chat', icon: MessageSquare },
          { id: 'landing', label: 'Landing Page', icon: Briefcase },
          { id: 'export', label: 'Export / Actions', icon: Share2 }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center space-x-2 px-4 py-3 border-b-2 text-xs font-bold transition-colors ${
              activeTab === tab.id 
                ? 'border-indigo-500 text-indigo-400' 
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        
        {/* Tab 1: Details & Specs */}
        {activeTab === 'details' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {/* Score Grid */}
            <div className="bg-slate-900 border border-slate-850 rounded-xl p-5 space-y-4">
              <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest">Validation Metrics</h3>
              <div className="grid grid-cols-3 gap-3">
                <div className={`p-3 rounded-lg border text-center ${getScoreBadge(idea.urgency_score)}`}>
                  <p className="text-[10px] uppercase font-bold text-slate-500">Urgency</p>
                  <p className="text-xl font-extrabold mt-1">{idea.urgency_score}/10</p>
                </div>
                <div className={`p-3 rounded-lg border text-center ${getScoreBadge(idea.frequency_score)}`}>
                  <p className="text-[10px] uppercase font-bold text-slate-500">Frequency</p>
                  <p className="text-xl font-extrabold mt-1">{idea.frequency_score}/10</p>
                </div>
                <div className={`p-3 rounded-lg border text-center ${getScoreBadge(idea.monetization_score)}`}>
                  <p className="text-[10px] uppercase font-bold text-slate-500">Monetization</p>
                  <p className="text-xl font-extrabold mt-1">{idea.monetization_score}/10</p>
                </div>
              </div>
              <div className="pt-2 flex justify-between items-center border-t border-slate-850">
                <span className="text-xs text-slate-400 font-bold">Total Validation Score:</span>
                <span className="text-sm font-black text-indigo-400">{idea.total_score}/30</span>
              </div>
            </div>

            {/* Pain Point Summary */}
            <div className="space-y-2">
              <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest">Identified Pain Point</h3>
              <p className="text-slate-200 text-sm font-semibold leading-relaxed p-4 bg-slate-900/30 border border-slate-900 rounded-xl">
                {idea.problem_summary}
              </p>
            </div>

            {/* Suggested Solutions */}
            <div className="space-y-3">
              <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest">AI Suggested Incubations</h3>
              <div className="space-y-3">
                {idea.product_ideas.map((p, idx) => (
                  <div key={idx} className="bg-slate-900 border border-slate-850 rounded-xl p-4 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-bold text-white">{p.idea}</span>
                      <span className="text-[10px] font-black uppercase text-indigo-400 bg-indigo-950/40 px-2 py-0.5 rounded border border-indigo-900/30">
                        {p.type}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{p.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Collapsible Original Post Content */}
            <div className="border border-slate-900 rounded-xl overflow-hidden bg-slate-900/20">
              <button
                onClick={() => setShowOriginalPost(!showOriginalPost)}
                className="w-full flex justify-between items-center p-4 text-xs font-bold text-slate-400 hover:text-white hover:bg-slate-900/50 transition-colors"
              >
                <span>Original Discussion Post Content</span>
                <span className="text-[10px] text-slate-500 uppercase">{showOriginalPost ? 'Hide' : 'Show'}</span>
              </button>
              {showOriginalPost && (
                <div className="p-4 border-t border-slate-900 text-xs text-slate-400 leading-relaxed font-mono max-h-60 overflow-y-auto whitespace-pre-wrap">
                  {idea.post_body || "No text body available."}
                </div>
              )}
            </div>

            {/* Target Audience */}
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="p-3 bg-slate-900/30 border border-slate-900 rounded-xl">
                <span className="text-slate-500 font-bold block mb-1">Target Customer Profile</span>
                <span className="text-slate-300 font-semibold">{idea.target_audience}</span>
              </div>
              <div className="p-3 bg-slate-900/30 border border-slate-900 rounded-xl">
                <span className="text-slate-500 font-bold block mb-1">Original Source Thread</span>
                <a 
                  href={idea.original_url} 
                  target="_blank" 
                  rel="noreferrer" 
                  className="text-indigo-400 hover:underline flex items-center space-x-1 font-semibold"
                >
                  <span>Link to {idea.source}</span>
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>

          </div>
        )}

        {/* Tab 2: Co-founder AI Chat */}
        {activeTab === 'chat' && (
          <div className="flex flex-col h-[calc(100vh-250px)] animate-in fade-in duration-200">
            {/* Chat Log */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-1">
              <div className="bg-slate-900/40 border border-slate-900 p-4 rounded-xl text-xs text-slate-400 leading-relaxed">
                🤖 <strong>Co-founder Advisor:</strong> I can help you scope features, estimate tech stack requirements, identify potential business models, or formulate 48-hour customer discovery strategies. What are you thinking?
              </div>

              {chatHistory.map((msg, idx) => (
                <div 
                  key={idx} 
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[85%] rounded-xl p-4 text-xs leading-relaxed ${
                    msg.role === 'user' 
                      ? 'bg-indigo-600 text-white font-semibold' 
                      : 'bg-slate-900 border border-slate-850 text-slate-200 whitespace-pre-wrap'
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}

              {chatLoading && (
                <div className="flex justify-start">
                  <div className="bg-slate-900 border border-slate-850 rounded-xl p-4 text-xs text-slate-400 flex items-center space-x-2">
                    <RefreshCw className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                    <span>Thinking...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Input Form */}
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                placeholder="Ask co-founder AI: 'What would a simple MVP tech stack be?'..."
                value={chatMessage}
                onChange={(e) => setChatMessage(e.target.value)}
                className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              />
              <button
                type="submit"
                disabled={chatLoading}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors flex items-center justify-center shrink-0"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        )}

        {/* Tab 3: Landing Page Generator */}
        {activeTab === 'landing' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            {landingError && (
              <div className="bg-red-950/20 border border-red-900/30 text-red-400 p-4 rounded-xl flex items-start space-x-3 text-xs">
                <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                <span>{landingError}</span>
              </div>
            )}

            {!landingPageCopy ? (
              <div className="text-center py-12 bg-slate-900/30 border border-slate-900 rounded-xl p-6 space-y-4">
                <h3 className="text-sm font-bold text-white">Generate High-Converting SaaS Landing Page Copy</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                  Let the AI position your product copy properly. Generate headlines, hero section copies, call-to-actions, features, and key FAQs instantly.
                </p>
                <button
                  onClick={handleGenerateLandingPage}
                  disabled={landingLoading}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg transition-colors inline-flex items-center space-x-2 text-xs font-bold"
                >
                  {landingLoading ? (
                    <>
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      <span>Writing Copy...</span>
                    </>
                  ) : (
                    <>
                      <Briefcase className="h-4 w-4" />
                      <span>Generate Landing Copy</span>
                    </>
                  )}
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                
                {/* Clean HTML Mockup */}
                <div className="bg-slate-900 border border-slate-850 rounded-xl overflow-hidden">
                  <div className="bg-slate-850/80 px-4 py-2 border-b border-slate-800 flex items-center justify-between text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    <span>SaaS Landing Page Canvas</span>
                    <button 
                      onClick={handleGenerateLandingPage} 
                      className="text-indigo-400 hover:underline flex items-center space-x-1"
                    >
                      <RefreshCw className="h-3 w-3" />
                      <span>Regenerate</span>
                    </button>
                  </div>
                  
                  {/* Hero mockup */}
                  <div className="p-6 text-center border-b border-slate-800 space-y-3">
                    <h1 className="text-lg font-black text-white leading-tight">
                      {landingPageCopy.headline}
                    </h1>
                    <p className="text-xs text-slate-400 max-w-md mx-auto leading-relaxed">
                      {landingPageCopy.subheadline}
                    </p>
                    <div className="pt-2">
                      <button className="bg-indigo-600 text-white text-xs font-extrabold px-6 py-2.5 rounded-md hover:bg-indigo-700">
                        {landingPageCopy.hero_cta || 'Get Started Now'}
                      </button>
                    </div>
                  </div>

                  {/* Features section */}
                  <div className="p-6 border-b border-slate-800 space-y-4">
                    <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest text-center">Core Features</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                      {landingPageCopy.features?.map((f, idx) => (
                        <div key={idx} className="bg-slate-950 p-4 rounded-lg border border-slate-850 space-y-1">
                          <p className="text-xs font-bold text-white">{f.title}</p>
                          <p className="text-[10px] text-slate-500 leading-relaxed">{f.description}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* FAQs section */}
                  <div className="p-6 border-b border-slate-800 space-y-4">
                    <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest text-center">Frequently Asked Questions</h3>
                    <div className="space-y-3">
                      {landingPageCopy.faq?.map((q, idx) => (
                        <div key={idx} className="space-y-1">
                          <p className="text-xs font-bold text-slate-200">Q: {q.question}</p>
                          <p className="text-xs text-slate-400 leading-relaxed">A: {q.answer}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Launch Validation section */}
                  <div className="p-5 bg-indigo-950/20 text-center">
                    <p className="text-[10px] font-black uppercase text-indigo-400 tracking-wider mb-1">48h Validation Pitch</p>
                    <p className="text-xs text-indigo-300/80 italic leading-relaxed max-w-md mx-auto">
                      "{landingPageCopy.launch_plan}"
                    </p>
                  </div>
                </div>

              </div>
            )}
          </div>
        )}

        {/* Tab 4: Export & Webhook Triggers */}
        {activeTab === 'export' && (
          <div className="space-y-6 animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-slate-850 p-5 rounded-xl space-y-4">
              <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest">Share Opportunity</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Save the copy, copy it as formatted markdown to paste in Notion/emails, or dispatch webhook pings.
              </p>
              
              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <button
                  onClick={handleCopyMarkdown}
                  className="flex-1 bg-slate-800 hover:bg-slate-750 text-white font-bold px-4 py-2.5 rounded-lg transition-colors flex items-center justify-center space-x-2 text-xs"
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 text-emerald-400" />
                      <span>Copied Markdown!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 text-indigo-450" />
                      <span>Copy Proposal Markdown</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-850 p-5 rounded-xl space-y-4">
              <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest">Webhook Integration</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Webhooks allow pushing high-potential ideas instantly to team workspaces. Slack & Discord channels receive automated, rich cards.
              </p>
              <div className="text-[11px] bg-slate-950 p-3 border border-slate-850 rounded-lg text-slate-500 font-mono">
                DISCORD_WEBHOOK_URL: {idea.total_score >= 25 ? 'Configured & Dispatched on discovery' : 'Not triggered (score < 25)'}
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default IdeaPlaygroundDrawer;
