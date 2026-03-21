/**
 * pages/Analytics.jsx — Analytics dashboard with model performance, SLA, and confidence charts.
 */
import React, { useEffect, useState } from "react";
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Cell, LineChart, Line,
} from "recharts";
import { analyticsAPI } from "../services/api";
import Loader from "../components/ui/Loader";
import { TrendingUp, ShieldCheck, Cpu, AlertTriangle } from "lucide-react";

const CATEGORY_COLORS = [
  "#4169ff","#8b5cf6","#10b981","#f59e0b","#ef4444",
  "#06b6d4","#ec4899","#84cc16","#f97316","#a78bfa",
];

function MetricCard({ label, value, unit, icon: Icon, color = "brand" }) {
  return (
    <div className="card-hover flex items-center gap-4">
      <div className={`p-3 rounded-xl bg-${color}-500/15 shrink-0`}>
        <Icon size={18} className={`text-${color}-400`} />
      </div>
      <div>
        <div className="text-2xl font-bold text-white">
          {value}{unit && <span className="text-sm font-normal text-gray-400 ml-1">{unit}</span>}
        </div>
        <div className="text-xs text-gray-400">{label}</div>
      </div>
    </div>
  );
}

export default function Analytics() {
  const [overview,     setOverview]     = useState(null);
  const [confidence,   setConfidence]   = useState([]);
  const [slaData,      setSlaData]      = useState([]);
  const [modelPerf,    setModelPerf]    = useState(null);
  const [alerts,       setAlerts]       = useState([]);
  const [loading,      setLoading]      = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsAPI.overview(),
      analyticsAPI.confidenceDist(30),
      analyticsAPI.slaBreakdown(),
      analyticsAPI.modelPerformance().catch(() => ({ data: null })),
      analyticsAPI.rootCauseAlerts("open"),
    ]).then(([ov, conf, sla, perf, al]) => {
      setOverview(ov.data);
      setConfidence(conf.data.confidence_distribution || []);
      setSlaData(sla.data.sla_breakdown || []);
      setModelPerf(perf.data);
      setAlerts(al.data.alerts || []);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader text="Loading analytics…" />;

  const autoRate  = Math.round((overview?.auto_resolve_rate  || 0) * 100);
  const slaRate   = Math.round((1 - (overview?.sla_breach_rate || 0)) * 100);
  const catF1     = modelPerf?.category_f1 || modelPerf?.["category_f1_macro"] || 0;

  // Radar data from per-category F1
  const radarData = Object.entries(modelPerf?.per_category_f1 || {}).map(([cat, f1]) => ({
    subject: cat, f1: Math.round(f1 * 100),
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="page-title">Analytics & Model Performance</h1>
        <p className="page-subtitle">30-day overview of AI pipeline performance</p>
      </div>

      {/* Top metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Auto-Resolve Rate" value={autoRate} unit="%" icon={TrendingUp} color="emerald" />
        <MetricCard label="SLA Compliance" value={slaRate} unit="%" icon={ShieldCheck} color="brand" />
        <MetricCard label="Category F1" value={catF1 ? `${Math.round(catF1 * 100)}%` : "—"} icon={Cpu} color="accent" />
        <MetricCard label="Open Incidents" value={alerts.length} icon={AlertTriangle} color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Confidence distribution */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Confidence Distribution (30 days)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={confidence}>
              <XAxis dataKey="range" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#4169ff" radius={[4,4,0,0]} name="Tickets" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* SLA compliance by category */}
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">SLA Compliance by Category</h3>
          {slaData.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-10">No SLA data yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={slaData}>
                <XAxis dataKey="category" tick={{ fontSize: 10 }} />
                <YAxis tickFormatter={(v) => `${Math.round(v * 100)}%`} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v) => `${Math.round(v * 100)}%`} />
                <Bar dataKey="compliance_rate" radius={[4,4,0,0]} name="Compliance">
                  {slaData.map((_, i) => <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Per-category model performance radar */}
      {radarData.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Per-Category F1 Score (Radar)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#2a2d3a" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
              <Radar dataKey="f1" stroke="#4169ff" fill="#4169ff" fillOpacity={0.25} name="F1 %" />
              <Tooltip formatter={(v) => `${v}%`} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Root cause alerts */}
      {alerts.length > 0 && (
        <div className="card">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Open Incident Alerts</h3>
          <div className="space-y-3">
            {alerts.map((a) => (
              <div key={a.alert_id} className="p-4 rounded-xl border border-red-500/20 bg-red-500/5">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`badge ${a.severity === "P0" ? "badge-escalate" : "badge-suggest"}`}>
                    {a.severity}
                  </span>
                  <span className="font-semibold text-white text-sm">{a.category}</span>
                  <span className="text-xs text-gray-500">{a.ticket_count} tickets / {a.time_window_minutes}min</span>
                </div>
                <p className="text-sm text-gray-300">{a.root_cause_hypothesis}</p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {(a.common_keywords || []).map((kw) => (
                    <span key={kw} className="badge bg-surface text-gray-400 border-surface-border">{kw}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
