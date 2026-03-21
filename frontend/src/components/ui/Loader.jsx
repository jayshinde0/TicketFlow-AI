/**
 * components/ui/Loader.jsx — Full-screen & inline loading spinner.
 */
import React from "react";
import { Zap } from "lucide-react";
import clsx from "clsx";

export default function Loader({ fullscreen = false, size = "md", text }) {
  const sizeMap = { sm: "w-5 h-5", md: "w-8 h-8", lg: "w-12 h-12" };

  const spinner = (
    <div className="flex flex-col items-center gap-3">
      <div className={clsx("relative", sizeMap[size])}>
        <div className={clsx(
          "absolute inset-0 rounded-full border-2 border-brand-600/30 border-t-brand-500 animate-spin",
        )} />
        <Zap size={size === "lg" ? 20 : 12} className="absolute inset-0 m-auto text-brand-400" />
      </div>
      {text && <p className="text-sm text-gray-400">{text}</p>}
    </div>
  );

  if (fullscreen) {
    return (
      <div className="fixed inset-0 bg-surface flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return <div className="flex items-center justify-center py-12">{spinner}</div>;
}



/**
 * components/ui/RoutingBadge.jsx — Routing decision badge.
 */
export function RoutingBadge({ decision }) {
  if (!decision) return null;
  const map = {
    AUTO_RESOLVE:      { cls: "badge-auto",     label: "Auto Resolve" },
    SUGGEST_TO_AGENT:  { cls: "badge-suggest",  label: "Suggest" },
    ESCALATE_TO_HUMAN: { cls: "badge-escalate", label: "Escalate" },
  };
  const { cls, label } = map[decision] || { cls: "badge-suggest", label: decision };
  return <span className={cls}>{label}</span>;
}


/**
 * components/ui/PriorityBadge.jsx — Priority level badge.
 */
export function PriorityBadge({ priority }) {
  if (!priority) return null;
  const map = {
    Critical: "badge-critical",
    High:     "badge-high",
    Medium:   "badge-medium",
    Low:      "badge-low",
  };
  return <span className={map[priority] || "badge badge-medium"}>{priority}</span>;
}


/**
 * components/ui/ConfidenceBar.jsx — Visual confidence score bar.
 */
export function ConfidenceBar({ score, showLabel = true }) {
  const pct = Math.round((score || 0) * 100);
  const color =
    pct >= 85 ? "bg-emerald-500" :
    pct >= 60 ? "bg-amber-400"   :
                "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className="confidence-bar flex-1">
        <div className={`confidence-fill ${color}`} style={{ width: `${pct}%` }} />
      </div>
      {showLabel && (
        <span className="text-xs font-mono font-semibold text-gray-300 w-10 text-right">
          {pct}%
        </span>
      )}
    </div>
  );
}


/**
 * components/ui/EmptyState.jsx — Empty data placeholder.
 */
export function EmptyState({ icon: Icon, title, subtitle, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-4">
      {Icon && <Icon size={40} className="text-gray-600" />}
      <div>
        <p className="text-base font-semibold text-gray-300">{title}</p>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
