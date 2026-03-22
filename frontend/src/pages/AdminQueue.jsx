/**
 * pages/AdminQueue.jsx — Priority Queue Monitor page.
 * Shows real-time queue depth, routing breakdown, priority distribution,
 * latency metrics (p50/p95/p99), and cache stats.
 */

import React, { useState, useEffect, useCallback } from "react";
import { queueAPI } from "../services/api";

const REFRESH_INTERVAL = 15000; // 15s auto-refresh

export default function AdminQueue() {
  const [queueData, setQueueData] = useState(null);
  const [perfData, setPerfData] = useState(null);
  const [stageData, setStageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = useCallback(async () => {
    try {
      const [q, p, s] = await Promise.all([
        queueAPI.status(),
        queueAPI.performance(24),
        queueAPI.stageBreakdown(24),
      ]);
      setQueueData(q.data);
      setPerfData(p.data);
      setStageData(s.data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load queue data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) return <div className="admin-queue loading">Loading queue data…</div>;
  if (error) return <div className="admin-queue error">{error}</div>;

  const queue = queueData?.queue_depth || {};
  const routing = queueData?.routing_breakdown || {};
  const priority = queueData?.priority_in_queue || {};
  const cache = queueData?.cache_stats || {};

  return (
    <div className="admin-queue" style={{ padding: "2rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <h1 style={{ margin: 0, fontSize: "1.5rem" }}>🎯 Priority Queue Monitor</h1>
        <button onClick={fetchData} style={refreshBtnStyle}>↻ Refresh</button>
      </div>

      {/* Queue Depth Cards */}
      <div style={cardGridStyle}>
        <StatCard title="Open" value={queue.open || 0} color="#f59e0b" />
        <StatCard title="In Progress" value={queue.in_progress || 0} color="#3b82f6" />
        <StatCard title="Total Waiting" value={queue.total_waiting || 0} color="#ef4444" />
        <StatCard title="Resolved (1h)" value={queueData?.resolved_last_hour || 0} color="#10b981" />
      </div>

      {/* Routing Breakdown */}
      <section style={sectionStyle}>
        <h2 style={h2Style}>Routing Breakdown</h2>
        <div style={cardGridStyle}>
          <StatCard title="Auto-Resolved" value={routing.auto_resolved || 0} color="#10b981" />
          <StatCard title="To Agent" value={routing.suggest_to_agent || 0} color="#f59e0b" />
          <StatCard title="Escalated" value={routing.escalated || 0} color="#ef4444" />
        </div>
      </section>

      {/* Priority Distribution */}
      <section style={sectionStyle}>
        <h2 style={h2Style}>Priority in Queue</h2>
        <div style={tableContainerStyle}>
          <table style={tableStyle}>
            <thead>
              <tr>
                {Object.keys(priority).map(p => <th key={p} style={thStyle}>{p}</th>)}
              </tr>
            </thead>
            <tbody>
              <tr>
                {Object.values(priority).map((v, i) => <td key={i} style={tdStyle}>{v}</td>)}
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Latency Metrics */}
      {perfData && (
        <section style={sectionStyle}>
          <h2 style={h2Style}>Pipeline Latency (Last 24h)</h2>
          <div style={cardGridStyle}>
            <StatCard title="p50" value={`${perfData.p50_ms || 0}ms`} color="#8b5cf6" />
            <StatCard title="p95" value={`${perfData.p95_ms || 0}ms`} color="#f59e0b" />
            <StatCard title="p99" value={`${perfData.p99_ms || 0}ms`} color="#ef4444" />
            <StatCard title="Avg" value={`${perfData.avg_ms || 0}ms`} color="#3b82f6" />
          </div>
          <p style={{ color: "#9ca3af", fontSize: "0.85rem", marginTop: "0.5rem" }}>
            Sample count: {perfData.sample_count || 0} tickets
          </p>
        </section>
      )}

      {/* Stage Breakdown */}
      {stageData && Object.keys(stageData).length > 0 && (
        <section style={sectionStyle}>
          <h2 style={h2Style}>Average Stage Breakdown</h2>
          <div style={tableContainerStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Stage</th>
                  <th style={thStyle}>Avg Time (ms)</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(stageData)
                  .filter(([k]) => k !== "count" && k !== "_id")
                  .map(([key, val]) => (
                    <tr key={key}>
                      <td style={tdStyle}>{key.replace("avg_", "").replace("_ms", "")}</td>
                      <td style={tdStyle}>{typeof val === "number" ? Math.round(val) : val}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Cache Stats */}
      <section style={sectionStyle}>
        <h2 style={h2Style}>Cache Performance</h2>
        <div style={cardGridStyle}>
          <StatCard title="Hit Rate" value={`${((cache.hit_rate || 0) * 100).toFixed(1)}%`} color="#10b981" />
          <StatCard title="Hits" value={cache.hits || 0} color="#3b82f6" />
          <StatCard title="Misses" value={cache.misses || 0} color="#f59e0b" />
          <StatCard title="LLM Cached" value={cache.llm_size || 0} color="#8b5cf6" />
        </div>
      </section>
    </div>
  );
}

// Reusable stat card
function StatCard({ title, value, color }) {
  return (
    <div style={{
      background: "var(--bg-secondary, #1e293b)",
      borderRadius: "12px",
      padding: "1.25rem",
      textAlign: "center",
      border: `1px solid ${color}22`,
      minWidth: "140px",
    }}>
      <p style={{ color: "#9ca3af", fontSize: "0.8rem", marginBottom: "0.5rem" }}>{title}</p>
      <p style={{ color, fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>{value}</p>
    </div>
  );
}

// Styles
const cardGridStyle = { display: "flex", gap: "1rem", flexWrap: "wrap" };
const sectionStyle = { marginTop: "2rem" };
const h2Style = { fontSize: "1.15rem", marginBottom: "1rem", color: "var(--color-text, #e2e8f0)" };
const refreshBtnStyle = {
  padding: "0.5rem 1rem", border: "1px solid #4b5563", borderRadius: "8px",
  background: "transparent", color: "#e2e8f0", cursor: "pointer", fontSize: "0.85rem",
};
const tableContainerStyle = { overflowX: "auto" };
const tableStyle = { width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" };
const thStyle = { padding: "0.75rem", textAlign: "left", borderBottom: "1px solid #374151", color: "#9ca3af" };
const tdStyle = { padding: "0.75rem", borderBottom: "1px solid #1e293b", color: "#e2e8f0" };
