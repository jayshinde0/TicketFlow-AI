/**
 * components/ticket/JourneyBadge.jsx — Compact badge showing current journey phase
 */
import React from "react";
import { Bot, User, CheckCircle2, Clock, Loader as LoaderIcon } from "lucide-react";

const PHASE_CONFIG = {
  submitted: {
    label: "Submitted",
    icon: Clock,
    color: "text-blue-400",
    bgColor: "bg-blue-500/15",
    borderColor: "border-blue-500/25",
  },
  ai_processing: {
    label: "AI Processing",
    icon: Bot,
    color: "text-purple-400",
    bgColor: "bg-purple-500/15",
    borderColor: "border-purple-500/25",
  },
  ai_resolved: {
    label: "AI Resolved",
    icon: CheckCircle2,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/15",
    borderColor: "border-emerald-500/25",
  },
  assigned_to_agent: {
    label: "With Agent",
    icon: User,
    color: "text-amber-400",
    bgColor: "bg-amber-500/15",
    borderColor: "border-amber-500/25",
  },
  in_progress: {
    label: "In Progress",
    icon: LoaderIcon,
    color: "text-cyan-400",
    bgColor: "bg-cyan-500/15",
    borderColor: "border-cyan-500/25",
  },
  resolved: {
    label: "Resolved",
    icon: CheckCircle2,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/15",
    borderColor: "border-emerald-500/25",
  },
  closed: {
    label: "Closed",
    icon: CheckCircle2,
    color: "text-gray-400",
    bgColor: "bg-gray-500/15",
    borderColor: "border-gray-500/25",
  },
};

export default function JourneyBadge({ phase, agentName }) {
  if (!phase) return null;
  
  const config = PHASE_CONFIG[phase] || PHASE_CONFIG.submitted;
  const Icon = config.icon;
  
  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded-lg border text-xs ${config.bgColor} ${config.borderColor} ${config.color}`}>
      <Icon size={12} />
      <span>{config.label}</span>
      {agentName && phase === "assigned_to_agent" && (
        <span className="text-gray-400">· {agentName}</span>
      )}
    </div>
  );
}
