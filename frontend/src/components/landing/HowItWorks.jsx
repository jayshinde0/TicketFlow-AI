import React, { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { Mail, Cpu, Sparkles, CheckCircle2, Webhook, Zap, BarChart3, Users, AlertTriangle } from 'lucide-react';

const steps = [
  {
    title: 'AI Classifies Instantly',
    description: 'TicketFlow AI reads incoming tickets across all channels, automatically detecting customer sentiment, categorizing the issue, and flagging urgency within milliseconds.',
    icon: Cpu,
    tags: ['Sentiment Analysis', 'Auto-Tagging', 'Urgency Detection'],
    color: 'text-brand-400',
    bgColor: 'bg-brand-900/40',
    borderColor: 'border-brand-500/30'
  },
  {
    title: 'Auto Resolve',
    description: 'Routine questions and common requests are handled completely hands-free. The AI generates and sends accurate, personalized responses instantly—drastically reducing backlog.',
    icon: Zap,
    tags: ['Zero-Touch', 'Instant Reply', 'Knowledge Base Sync'],
    color: 'text-success',
    bgColor: 'bg-success/20',
    borderColor: 'border-success/30'
  },
  {
    title: 'Suggest to Agent',
    description: 'When human touch is needed, the ticket routes to the right agent. The interface immediately surfaces AI-generated draft suggestions and related articles to speed up handling.',
    icon: Sparkles,
    tags: ['Skills Routing', 'Draft Generation', 'Context Surfacing'],
    color: 'text-accent-400',
    bgColor: 'bg-accent-900/40',
    borderColor: 'border-accent-500/30'
  },
  {
    title: 'Escalate',
    description: 'High-priority or highly-sensitive issues bypass the standard queue and are instantly escalated to specialized tier-2 teams, ensuring critical cases get immediate attention.',
    icon: AlertTriangle,
    tags: ['Priority Routing', 'SLA Management', 'Alert Tracking'],
    color: 'text-danger',
    bgColor: 'bg-danger/20',
    borderColor: 'border-danger/30'
  },
];

export default function HowItWorks() {
  const sectionRef = useRef(null);

  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start center", "end center"]
  });

  const lineHeight = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);

  return (
    <section id="how-it-works" ref={sectionRef} className="py-24 md:py-32 bg-surface relative overflow-hidden">
      {/* Background aesthetics */}
      <div className="absolute top-1/4 left-0 w-[500px] h-[500px] bg-brand-600/5 rounded-full blur-[150px] pointer-events-none -translate-x-1/2" />
      <div className="absolute bottom-1/4 right-0 w-[500px] h-[500px] bg-accent-600/5 rounded-full blur-[150px] pointer-events-none translate-x-1/2" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto mb-20 md:mb-32">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-card border border-surface-border text-accent-400 text-xs font-bold uppercase tracking-widest mb-6">
              <Zap className="w-3.5 h-3.5" />
              <span>The Pipeline</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-6">
              From submission to resolution
            </h2>
            <p className="text-xl text-gray-400 leading-relaxed">
              Experience a completely unified workflow. Our architecture intercepts chaos and delivers beautifully structured, solvable tasks directly to your team.
            </p>
          </motion.div>
        </div>

        {/* Timeline Container */}
        <div className="relative max-w-5xl mx-auto">
          
          {/* Central Animated Line (Desktop) */}
          <div className="hidden md:block absolute left-1/2 top-4 bottom-4 w-1 -ml-[2px] bg-surface-border rounded-full overflow-hidden">
             <motion.div 
               style={{ height: lineHeight }} 
               className="w-full bg-gradient-to-b from-brand-500 via-accent-500 to-success" 
             />
          </div>

          <div className="space-y-16 md:space-y-24">
            {steps.map((step, index) => {
              const isEven = index % 2 === 0;

              return (
                <motion.div 
                  key={step.title} 
                  initial={{ opacity: 0, y: 50 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-15% 0px -15% 0px" }}
                  transition={{ duration: 0.7, ease: "easeOut", delay: 0.1 }}
                  className={`relative flex flex-col md:flex-row items-center gap-8 md:gap-16 ${isEven ? 'md:flex-row-reverse' : ''}`}
                >
                  
                  {/* Step Connector Node (Mobile left, Desktop Center) */}
                  <div className="absolute left-6 md:left-1/2 md:-ml-8 top-8 md:top-1/2 md:-mt-8 z-20">
                     <motion.div 
                        initial={{ scale: 0 }}
                        whileInView={{ scale: 1 }}
                        viewport={{ once: true, margin: "-15% 0px -15% 0px" }}
                        transition={{ type: "spring", stiffness: 200, delay: 0.3 }}
                        className={`w-16 h-16 rounded-full flex items-center justify-center border-4 border-surface shadow-xl ${step.bgColor} ${step.color} ${step.borderColor} backdrop-blur-md`}
                     >
                       <step.icon className="w-6 h-6" />
                     </motion.div>
                  </div>

                  {/* Mobile-only tracking line */}
                  <div className="md:hidden absolute left-[3.35rem] top-24 bottom-[-6rem] w-px bg-surface-border rounded-full" />

                  {/* Empty space for alternating layout */}
                  <div className="hidden md:block md:w-1/2" />

                  {/* Content Card */}
                  <div className={`w-full md:w-1/2 pl-24 pr-4 md:px-0 `}>
                    <motion.div 
                       whileHover={{ y: -5 }}
                       className={`relative bg-surface-card p-8 md:p-10 rounded-3xl border border-surface-border shadow-[0_8px_30px_rgba(0,0,0,0.12)] hover:border-surface-hover hover:shadow-glow-sm transition-all duration-300 group ${isEven ? 'md:pr-12 md:mr-4' : 'md:pl-12 md:ml-4'}`}
                    >
                      {/* Subdued Step Number */}
                      <div className="absolute top-6 right-8 text-6xl font-black text-white/5 pointer-events-none transition-colors group-hover:text-white/10">
                         0{index + 1}
                      </div>

                      <h3 className="text-2xl md:text-3xl font-bold text-white mb-4 tracking-tight">
                        {step.title}
                      </h3>
                      
                      <p className="text-gray-400 text-lg leading-relaxed mb-6">
                        {step.description}
                      </p>

                      {/* Tag Pills */}
                      <div className="flex flex-wrap gap-2 pt-4 border-t border-surface-border/50">
                        {step.tags.map(tag => (
                          <span key={tag} className="px-3 py-1 text-xs font-semibold text-gray-300 bg-surface rounded-full border border-surface-border">
                            {tag}
                          </span>
                        ))}
                      </div>

                    </motion.div>
                  </div>

                </motion.div>
              );
            })}
          </div>
        </div>

      </div>
    </section>
  );
}
