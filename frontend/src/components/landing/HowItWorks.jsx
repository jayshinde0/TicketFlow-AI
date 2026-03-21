import React from 'react';
import { motion } from 'framer-motion';
import { Mail, Cpu, CheckCircle2 } from 'lucide-react';

const steps = [
  {
    title: 'Customer Submits Ticket',
    description: 'A customer reaches out via email, chat, or web portal with an issue or question.',
    icon: Mail,
    color: 'text-gray-300',
    bgColor: 'bg-surface-hover',
    borderColor: 'border-surface-border'
  },
  {
    title: 'AI Analyzes & Triages',
    description: 'TicketFlow AI instantly reads the ticket, detects the sentiment, identifies the category, and flags urgency.',
    icon: Cpu,
    color: 'text-brand-400',
    bgColor: 'bg-brand-900/40',
    borderColor: 'border-brand-500/30'
  },
  {
    title: 'Agent Resolves Faster',
    description: 'The ticket is routed to the perfect agent, accompanied by AI-suggested responses and knowledge base articles.',
    icon: CheckCircle2,
    color: 'text-success',
    bgColor: 'bg-success/20',
    borderColor: 'border-success/30'
  },
];

export default function HowItWorks() {
  const containerVariants = {
    hidden: { opacity: 0 },
    whileInView: {
      opacity: 1,
      transition: {
        staggerChildren: 0.3,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -50 },
    whileInView: {
      opacity: 1,
      x: 0,
      transition: { duration: 0.6, ease: 'easeOut' },
    },
  };

  return (
    <section id="how-it-works" className="py-24 bg-surface border-t border-surface-border relative overflow-hidden">
      {/* Background glow for How It Works */}
      <div className="absolute top-1/2 left-0 w-64 h-64 bg-accent-600/10 rounded-full blur-[100px] pointer-events-none -translate-y-1/2" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-base font-semibold tracking-wide text-accent-400 uppercase">
              How it works
            </h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-white sm:text-4xl">
              From submission to resolution
            </p>
          </motion.div>
        </div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="whileInView"
          viewport={{ once: true, margin: "-50px" }}
          className="relative max-w-4xl mx-auto"
        >
          {/* Vertical connecting line */}
          <div className="hidden md:block absolute left-8 top-8 bottom-8 w-px bg-surface-border" />

          <div className="space-y-12 md:space-y-16">
            {steps.map((step, index) => (
              <motion.div key={step.title} variants={itemVariants} className="relative flex flex-col md:flex-row gap-6 md:gap-12 items-start md:items-center">
                {/* Visual Step Indicator */}
                <div className="relative z-10 flex-shrink-0">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center border-2 shadow-sm ${step.bgColor} ${step.color} ${step.borderColor} border-surface`}>
                     <step.icon className="w-7 h-7" />
                  </div>
                  {/* Mobile connecting line */}
                  {index !== steps.length - 1 && (
                    <div className="md:hidden absolute left-1/2 top-16 bottom-[-3rem] w-px -ml-[1px] bg-surface-border" />
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 bg-surface-card p-6 md:p-8 rounded-2xl shadow-card border border-surface-border hover:border-surface-hover hover:shadow-glow-sm transition-all duration-300">
                  <div className="text-sm font-semibold text-brand-400 mb-2 tracking-wide uppercase">Step {index + 1}</div>
                  <h3 className="text-2xl font-bold text-white mb-3">{step.title}</h3>
                  <p className="text-lg text-gray-400 leading-relaxed">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
