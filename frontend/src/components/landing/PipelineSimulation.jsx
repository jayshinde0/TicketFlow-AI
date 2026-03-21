import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GitCommit, Database, BrainCircuit, Activity, UserCog, Bot, Send, ShieldCheck, RefreshCw, TerminalSquare, Play, RefreshCcw } from 'lucide-react';

const NODES = {
  // Phase 1: Engine
  classification: { id: 'classification', title: 'Intelligent Classification', desc: 'Category · Priority · SLA risk', tech: 'HuggingFace / NLP', icon: BrainCircuit },
  kb: { id: 'kb', title: 'Knowledge Base Lookup', desc: 'Semantic search past tickets', tech: 'FAISS + ChromaDB', icon: Database },
  eval: { id: 'eval', title: 'Confidence + Risk Eval', desc: 'SLA breach prob · RSI score', tech: 'Rules Engine', icon: Activity },
  
  // Phase 2: Branches
  hitl: { id: 'hitl', title: 'HITL Escalation', desc: 'Low confidence / Risky', tech: 'Workspace UI', icon: UserCog, isHuman: true },
  human_review: { id: 'human_review', title: 'Human Review', desc: 'Approve / Override', tech: 'Agent Dashboard', icon: ShieldCheck, isHuman: true },
  auto_resolve: { id: 'auto_resolve', title: 'Auto Resolver', desc: 'High confidence ticket', tech: 'Generative AI', icon: Bot, isHuman: false },
  
  // Phase 3: Resolution & Learning
  res_sent: { id: 'res_sent', title: 'Resolution Sent', desc: 'Customer receives answer', tech: 'Email / Webhook', icon: Send },
  audit: { id: 'audit', title: 'Audit Logging', desc: 'Confidence scores · traceability', tech: 'PostgreSQL', icon: TerminalSquare },
  feedback: { id: 'feedback', title: 'Feedback Loop', desc: 'Human corrections storage', tech: 'Data Lake', icon: GitCommit },
  retrain: { id: 'retrain', title: 'Model Retraining', desc: 'Weights updated continuously', tech: 'PyTorch', icon: RefreshCw },
};

const LOG_MESSAGES = {
  classification: "[SYS] Analyzing unstructured text... \\n> Intent: Password Reset (98%)\\n> Priority: Medium\\n> SLA Risk: Low\\n> Est Resolution: < 5m",
  kb: "[DB] Querying ChromaDB Vector Store...\\n> FAISS index scanned...\\n> 3 similar closed tickets found.\\n> Embedding distance: 0.12 (Highly Relevant)",
  eval: "[EVAL] Computing risk matrix...\\n> Novelty: Low\\n> Confidence Score: ", // Appended dynamically
  hitl: "[ROUTER] Confidence below threshold (82% < 90%).\\n> Escalating to HITL Queue...\\n> Assigned to Agent: Sarah J.",
  human_review: "[AGENT] Human reviewing AI draft...\\n> Draft Approved without edits.\\n> Triggering dispatch...",
  auto_resolve: "[ROUTER] Confidence exceeds threshold (96% >= 90%).\\n> Triggering Auto-Resolution workflow...\\n> Generating comprehensive reply...",
  res_sent: "[SYS] Payload dispatched successfully to Customer channel.\\n> Status updated to 'Resolved'.",
  audit: "[LOG] Writing trace telemetry to DB...\\n> Transaction ID: tk_9921_abc\\n> All system decisions securely retained.",
  feedback: "[ETL] Processing resolution metadata...\\n> Added to fine-tuning dataset queue.\\n> Feedback parsed: POSITIVE.",
  retrain: "[ML] Triggering continuous learning hook...\\n> Model weights shifted.\\n> Pipeline efficiency optimized for next run."
};

export default function PipelineSimulation() {
  const [activeNode, setActiveNode] = useState(null);
  const [logs, setLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [pathChosen, setPathChosen] = useState(null); // 'auto' or 'human'

  const addLog = (nodeId, forcedScore = null) => {
    let msg = LOG_MESSAGES[nodeId];
    if (nodeId === 'eval') {
      const score = forcedScore !== null ? forcedScore : (Math.random() > 0.5 ? 96 : 82);
      msg += `${score}%`;
      setPathChosen(score >= 90 ? 'auto' : 'human');
    }
    setLogs(prev => [...prev, msg]);
  };

  const runSimulation = async () => {
    if (isRunning) return;
    setIsRunning(true);
    setLogs([]);
    setPathChosen(null);
    setActiveNode(null);

    // Initial wait
    await new Promise(r => setTimeout(r, 500));

    // Determine path randomly beforehand so we can format the log correctly
    const isAutoPath = Math.random() > 0.4; // 60% chance for auto resolve
    const score = isAutoPath ? Math.floor(Math.random() * 10) + 90 : Math.floor(Math.random() * 20) + 70;

    const sequence = [
      'classification', 
      'kb', 
      'eval',
      ...isAutoPath ? ['auto_resolve'] : ['hitl', 'human_review'],
      'res_sent',
      'audit',
      'feedback',
      'retrain'
    ];

    for (const node of sequence) {
      setActiveNode(node);
      addLog(node, node === 'eval' ? score : null);
      // Wait for reading effect
      await new Promise(r => setTimeout(r, node === 'eval' ? 2000 : 1500));
    }

    setActiveNode('DONE');
    setIsRunning(false);
  };

  const NodeCard = ({ nodeKey, active }) => {
    const data = NODES[nodeKey];
    if (!data) return null;
    
    return (
      <div className={`relative p-5 rounded-2xl border transition-all duration-500 flex flex-col items-start gap-4 ${
        active 
          ? 'bg-brand-900/30 border-brand-500 shadow-[0_0_30px_rgba(65,105,255,0.3)] scale-[1.02] z-10' 
          : 'bg-surface-card border-surface-border opacity-70 scale-100 z-0'
      }`}>
        {/* Glow behind icon when active */}
        {active && (
           <div className="absolute top-4 left-4 w-10 h-10 bg-brand-500/50 blur-xl rounded-full pointer-events-none" />
        )}
        
        <div className={`p-3 rounded-xl flex items-center justify-center shrink-0 border ${
          active ? 'bg-brand-600 border-brand-400 text-white' : 'bg-surface border-surface-border text-gray-400'
        } transition-colors duration-500`}>
          <data.icon className="w-5 h-5 relative z-10" />
        </div>
        
        <div className="text-left w-full">
          <h4 className={`font-bold tracking-tight mb-1 transition-colors duration-500 ${active ? 'text-white' : 'text-gray-300'}`}>
            {data.title}
          </h4>
          <p className="text-xs text-gray-500 mb-3">{data.desc}</p>
          <div className="inline-block mt-auto px-2 py-1 bg-surface rounded text-[10px] font-mono text-gray-400 border border-surface-border">
            TECH: {data.tech}
          </div>
        </div>
      </div>
    );
  };

  return (
    <section className="py-24 bg-surface border-t border-surface-border relative overflow-hidden">
      
      {/* Background Gradients */}
      <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-brand-600/5 rounded-full blur-[150px] pointer-events-none -translate-y-1/2 translate-x-1/2" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-base font-semibold tracking-wide text-brand-400 uppercase mb-2">
            Inside the Engine
          </h2>
          <p className="text-3xl md:text-5xl font-extrabold tracking-tight text-white mb-6">
            Interactive Architecture
          </p>
          <p className="text-lg text-gray-400 mb-8">
            Experience the exact logical flow a ticket undergoes from ingestion to resolution. 
            Watch our vector databases, confidence evaluators, and escalation nodes interact in real-time.
          </p>
          
          <button 
            onClick={runSimulation}
            disabled={isRunning}
            className={`inline-flex items-center gap-2 px-8 py-4 text-base font-bold text-white rounded-xl shadow-glow transition-all duration-300 ${
              isRunning ? 'bg-surface-border cursor-not-allowed opacity-50' : 'bg-gradient-brand hover:shadow-glow-lg hover:-translate-y-1'
            }`}
          >
            {isRunning ? (
              <><RefreshCw className="w-5 h-5 animate-spin" /> Simulating Ticket...</>
            ) : activeNode === 'DONE' ? (
              <><RefreshCcw className="w-5 h-5" /> Run Another Ticket</>
            ) : (
              <><Play className="w-5 h-5" /> Start Live Simulation</>
            )}
          </button>
        </div>

        <div className="flex flex-col lg:flex-row gap-8 items-start">
          
          {/* Visual Flow diagram container */}
          <div className="w-full lg:w-2/3 flex flex-col gap-6">
            
            {/* Phase 1 */}
            <div className="p-6 rounded-3xl bg-surface-card/40 border border-surface-border/50 backdrop-blur-sm">
              <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Phase 1: Deep Analysis</div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <NodeCard nodeKey="classification" active={activeNode === 'classification'} />
                <NodeCard nodeKey="kb" active={activeNode === 'kb'} />
                <NodeCard nodeKey="eval" active={activeNode === 'eval'} />
              </div>
            </div>

            {/* Phase 2: Split */}
            <div className="p-6 rounded-3xl bg-surface-card/40 border border-surface-border/50 backdrop-blur-sm relative">
               <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4 flex justify-between items-center">
                 <span>Phase 2: Resolution Branching</span>
                 {pathChosen && (
                   <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold text-white ${pathChosen === 'auto' ? 'bg-success/50 border border-success' : 'bg-accent-500/50 border border-accent-500'}`}>
                     Path selected: {pathChosen}
                   </span>
                 )}
               </div>
               
               <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                 
                 {/* Auto Branch */}
                 <div className={`p-4 rounded-2xl border transition-all duration-500 ${pathChosen === 'auto' ? 'border-brand-500/50 bg-brand-500/5' : 'border-surface-border/50 bg-surface/50'}`}>
                    <div className="text-xs font-mono text-brand-400 mb-3 flex items-center gap-2">
                       <div className="w-1.5 h-1.5 rounded-full bg-brand-400" />
                       High Confidence Flow
                    </div>
                    <NodeCard nodeKey="auto_resolve" active={activeNode === 'auto_resolve'} />
                 </div>

                 {/* Human Branch */}
                 <div className={`p-4 rounded-2xl border transition-all duration-500 ${pathChosen === 'human' ? 'border-accent-500/50 bg-accent-500/5' : 'border-surface-border/50 bg-surface/50'}`}>
                    <div className="text-xs font-mono text-accent-400 mb-3 flex items-center gap-2">
                       <div className="w-1.5 h-1.5 rounded-full bg-accent-400" />
                       HITL / Risky Flow
                    </div>
                    <div className="flex flex-col gap-4">
                      <NodeCard nodeKey="hitl" active={activeNode === 'hitl'} />
                      <NodeCard nodeKey="human_review" active={activeNode === 'human_review'} />
                    </div>
                 </div>

               </div>
               
               <div className="mt-4">
                 <NodeCard nodeKey="res_sent" active={activeNode === 'res_sent'} />
               </div>
            </div>

            {/* Phase 3 */}
            <div className="p-6 rounded-3xl bg-surface-card/40 border border-surface-border/50 backdrop-blur-sm">
              <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Phase 3: Continuous Learning</div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <NodeCard nodeKey="audit" active={activeNode === 'audit'} />
                <NodeCard nodeKey="feedback" active={activeNode === 'feedback'} />
                <NodeCard nodeKey="retrain" active={activeNode === 'retrain'} />
              </div>
            </div>

          </div>

          {/* Terminal / Live Logs View */}
          <div className="w-full lg:w-1/3 lg:sticky lg:top-32 h-[600px] bg-[#0A0C10] rounded-3xl border border-surface-border shadow-2xl overflow-hidden flex flex-col">
            <div className="px-4 py-3 bg-surface border-b border-surface-border flex items-center gap-2">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-danger/50" />
                <div className="w-3 h-3 rounded-full bg-accent-400/50" />
                <div className="w-3 h-3 rounded-full bg-success/50" />
              </div>
              <div className="mx-auto text-xs font-mono text-gray-500 pr-10">pipeline_trace.log</div>
            </div>
            
            <div className="p-4 overflow-y-auto flex-1 font-mono text-sm leading-relaxed flex flex-col justify-end">
              <AnimatePresence initial={false}>
                {logs.length === 0 && !isRunning && (
                   <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-gray-600 self-start w-full text-center my-auto">
                     Awaiting simulation trigger...
                   </motion.div>
                )}
                {logs.map((log, i) => (
                  <motion.div 
                    key={i}
                    initial={{ opacity: 0, x: -10, filter: 'blur(5px)' }}
                    animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
                    className="mb-4 text-gray-300"
                  >
                    {log.split('\\n').map((line, idx) => {
                      // Colorize lines based on prefixes
                      let color = "text-gray-300";
                      if (line.includes('[SYS]')) color = "text-brand-400";
                      if (line.includes('[DB]')) color = "text-accent-400";
                      if (line.includes('[EVAL]')) color = "text-success";
                      if (line.includes('[ROUTER]')) color = "text-danger";
                      if (line.includes('[AGENT]')) color = "text-orange-400";
                      if (line.includes('[LOG]')) color = "text-gray-500";
                      if (line.includes('[ETL]')) color = "text-purple-400";
                      if (line.includes('[ML]')) color = "text-green-400";
                      if (line.startsWith('>')) color = "text-gray-400 pl-4 border-l-2 border-surface-border mt-1";

                      return (
                        <div key={idx} className={`${color} break-words`}>
                          {line}
                        </div>
                      )
                    })}
                  </motion.div>
                ))}
              </AnimatePresence>
              {isRunning && (
                <motion.div 
                  className="w-2 h-4 bg-brand-400 animate-pulse mt-2" 
                  initial={{ opacity: 0 }} 
                  animate={{ opacity: 1 }} 
                  exit={{ opacity: 0 }} 
                />
              )}
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
