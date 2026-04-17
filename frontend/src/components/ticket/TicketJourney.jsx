/**
 * components/ticket/TicketJourney.jsx — Visual timeline showing ticket journey phases
 */
import React, { useEffect, useState } from "react";
import { journeyAPI } from "../../services/api";
import { 
  CheckCircle2, Clock, User, Bot, AlertCircle, 
  ArrowRight, Loader as LoaderIcon 
} from "lucide-react";

const PHASE_CONFIG = {
  submitted: {
    label: "Submitted",
    icon: Clock,
    color: "text-blue-400",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/25",
  },
  ai_processing: {
    label: "AI Processing",
    icon: Bot,
    color: "text-purple-400",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/25",
  },
  ai_resolved: {
    label: "AI Resolved",
    icon: CheckCircle2,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/25",
  },
  assigned_to_agent: {
    label: "Assigned to Agent",
    icon: User,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/25",
  },
  in_progress: {
    label: "In Progress",
    icon: LoaderIcon,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/25",
  },
  resolved: {
    label: "Resolved",
    icon: CheckCircle2,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/25",
  },
  closed: {
    label: "Closed",
    icon: CheckCircle2,
    color: "text-gray-400",
    bgColor: "bg-gray-500/10",
    borderColor: "border-gray-500/25",
  },
};

function formatDuration(ms) {
  if (!ms) return "—";
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
  return `${seconds}s`;
}

function PhaseStep({ phase, isActive, isCompleted, duration }) {
  const config = PHASE_CONFIG[phase] || PHASE_CONFIG.submitted;
  const Icon = config.icon;
  
  return (
    <div className="flex items-start gap-3">
      {/* Icon */}
      <div className={`
        flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all
        ${isActive ? `${config.bgColor} ${config.borderColor} ${config.color}` : ''}
        ${isCompleted ? `${config.bgColor} ${config.borderColor} ${config.color}` : ''}
        ${!isActive && !isCompleted ? 'bg-surface border-surface-border text-gray-600' : ''}
      `}>
        <Icon size={18} className={isActive ? "animate-pulse" : ""} />
      </div>
      
      {/* Content */}
      <div className="flex-1 pb-6">
        <div className="flex items-center justify-between">
          <h4 className={`text-sm font-semibold ${isActive || isCompleted ? 'text-white' : 'text-gray-500'}`}>
            {config.label}
          </h4>
          {duration && (
            <span className="text-xs text-gray-500">
              {formatDuration(duration)}
            </span>
          )}
        </div>
        {isActive && (
          <p className="text-xs text-gray-400 mt-1">Currently in this phase...</p>
        )}
      </div>
    </div>
  );
}

export default function TicketJourney({ ticketId }) {
  const [journey, setJourney] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!ticketId) return;
    
    const loadJourney = () => {
      journeyAPI.getByTicket(ticketId)
        .then(res => {
          setJourney(res.data);
          setError(null);
        })
        .catch(err => {
          console.error("Failed to load journey:", err);
          setError(err.response?.data?.detail || "Failed to load journey");
        })
        .finally(() => setLoading(false));
    };
    
    loadJourney();
    
    // Auto-refresh every 5 seconds to show phase updates
    const interval = setInterval(loadJourney, 5000);
    
    return () => clearInterval(interval);
  }, [ticketId]);

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8">
          <LoaderIcon className="animate-spin text-brand-400" size={24} />
          <span className="ml-2 text-sm text-gray-400">Loading journey...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="flex items-center gap-2 text-amber-400 text-sm">
          <AlertCircle size={16} />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!journey) return null;

  const currentPhaseIndex = journey.phases.findIndex(p => p.phase === journey.current_phase);
  
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
          <ArrowRight size={14} className="text-brand-400" /> Ticket Journey
        </h3>
        <span className="text-xs text-gray-500">
          {journey.phases.length} phases
        </span>
      </div>

      {/* Assigned Agent Info */}
      {journey.assigned_agent && (
        <div className="mb-6 p-4 rounded-xl bg-surface border border-surface-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center">
              <User size={18} className="text-brand-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-white">{journey.assigned_agent.full_name}</p>
              <p className="text-xs text-gray-500">
                {journey.assigned_agent.department} · {journey.assigned_agent.specialization}
              </p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Workload</p>
              <p className="text-sm font-semibold text-white">
                {journey.assigned_agent.current_workload}/{journey.assigned_agent.max_concurrent_tickets}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Timeline */}
      <div className="relative">
        {/* Vertical line */}
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-surface-border" />
        
        {/* Phases */}
        <div className="relative space-y-0">
          {journey.phases.map((phaseData, index) => {
            const isActive = index === currentPhaseIndex;
            const isCompleted = index < currentPhaseIndex;
            
            return (
              <PhaseStep
                key={phaseData.phase}
                phase={phaseData.phase}
                isActive={isActive}
                isCompleted={isCompleted}
                duration={phaseData.duration_ms}
              />
            );
          })}
        </div>
      </div>

      {/* Summary */}
      <div className="mt-4 pt-4 border-t border-surface-border">
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-gray-500">Total Duration</span>
            <p className="font-semibold text-white mt-0.5">
              {formatDuration(journey.total_duration_ms)}
            </p>
          </div>
          <div>
            <span className="text-gray-500">Current Phase</span>
            <p className="font-semibold text-white mt-0.5 capitalize">
              {journey.current_phase.replace(/_/g, ' ')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
