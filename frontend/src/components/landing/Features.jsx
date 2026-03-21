import React from 'react';
import { motion } from 'framer-motion';
import { MessageSquareText, Route, Zap, BrainCircuit } from 'lucide-react';

const features = [
  {
    name: 'Automated Triage',
    description: 'Instantly categorize and prioritize incoming tickets based on urgency, topic, and customer history.',
    icon: Zap,
    color: 'text-brand-400',
    bgColor: 'bg-brand-900/40',
    borderColor: 'border-brand-500/30'
  },
  {
    name: 'Sentiment Analysis',
    description: 'Understand customer emotion at a glance. Automatically flag angry or frustrated customers for immediate attention.',
    icon: MessageSquareText,
    color: 'text-danger',
    bgColor: 'bg-danger/20',
    borderColor: 'border-danger/30'
  },
  {
    name: 'Smart Routing',
    description: 'Route tickets to the most qualified agent based on their skills, current workload, and past performance.',
    icon: Route,
    color: 'text-accent-400',
    bgColor: 'bg-accent-900/40',
    borderColor: 'border-accent-500/30'
  },
  {
    name: 'AI Knowledge Base',
    description: 'Suggest solutions to agents before they even start typing. Keep your answers consistent and fast.',
    icon: BrainCircuit,
    color: 'text-success',
    bgColor: 'bg-success/20',
    borderColor: 'border-success/30'
  },
];

export default function Features() {
  const containerVariants = {
    hidden: { opacity: 0 },
    whileInView: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    whileInView: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5 },
    },
  };

  return (
    <section id="features" className="py-24 bg-surface border-t border-surface-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-base font-semibold tracking-wide text-brand-400 uppercase">
              Features
            </h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-white sm:text-4xl">
              A smarter way to manage support
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-400 mx-auto">
              Everything you need to deliver exceptional customer service at scale, powered by advanced artificial intelligence.
            </p>
          </motion.div>
        </div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="whileInView"
          viewport={{ once: true, margin: "-50px" }}
          className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12"
        >
          {features.map((feature) => (
            <motion.div
              key={feature.name}
              variants={itemVariants}
              className="relative group bg-surface-card p-8 rounded-2xl shadow-card border border-surface-border hover:shadow-glow-sm hover:-translate-y-1 transition-all duration-300"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-brand-900/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl pointer-events-none" />
              
              <div className="relative z-10">
                <div className={`w-14 h-14 rounded-xl flex items-center justify-center mb-6 shadow-sm ${feature.bgColor} ${feature.color} border ${feature.borderColor}`}>
                  <feature.icon className="h-7 w-7" aria-hidden="true" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3 group-hover:text-brand-300 transition-colors">
                  {feature.name}
                </h3>
                <p className="text-gray-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
