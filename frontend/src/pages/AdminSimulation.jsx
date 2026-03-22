/**
 * pages/AdminSimulation.jsx — Simulation Mode page.
 * Start/stop ticket simulation, configure speed, and watch live stats.
 */

import React, { useState, useEffect, useCallback } from "react";
import { simulationAPI } from "../services/api";

export default function AdminSimulation() {
  const [status, setStatus] = useState(null);
  const [speed, setSpeed] = useState(1.0);
  const [maxTickets, setMaxTickets] = useState(50);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchStatus = useCallback(async () => {
    try {
      const res = await simulationAPI.status();
      setStatus(res.data);
    } catch (err) {
      // Simulation endpoint might not have data yet — that's OK
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  const handleStart = async () => {
    setLoading(true);
    setError("");
    try {
      await simulationAPI.start({ speed_multiplier: speed, max_tickets: maxTickets });
      fetchStatus();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to start simulation");
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    setLoading(true);
    try {
      await simulationAPI.stop();
      fetchStatus();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to stop simulation");
    } finally {
      setLoading(false);
    }
  };

  const isRunning = status?.running;
  const stats = status?.stats || {};
  const total = status?.tickets_generated || 0;

  return (
    <div style={{ padding: "2rem" }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: "1.5rem" }}>🧪 Simulation Mode</h1>

      {error && <div style={errorStyle}>{error}</div>}

      {/* Controls */}
      <div style={controlsStyle}>
        <div style={{ display: "flex", gap: "1rem", alignItems: "flex-end", flexWrap: "wrap" }}>
          <div>
            <label style={labelStyle}>Speed Multiplier</label>
            <input
              type="range" min="0.5" max="5" step="0.5" value={speed}
              onChange={e => setSpeed(parseFloat(e.target.value))}
              disabled={isRunning}
              style={{ width: "150px" }}
            />
            <span style={{ color: "#e2e8f0", marginLeft: "0.5rem" }}>{speed}x</span>
          </div>
          <div>
            <label style={labelStyle}>Max Tickets</label>
            <input
              type="number" min={1} max={500} value={maxTickets}
              onChange={e => setMaxTickets(parseInt(e.target.value) || 50)}
              disabled={isRunning}
              style={inputStyle}
            />
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            {!isRunning ? (
              <button onClick={handleStart} disabled={loading} style={startBtnStyle}>
                {loading ? "Starting…" : "▶ Start Simulation"}
              </button>
            ) : (
              <button onClick={handleStop} disabled={loading} style={stopBtnStyle}>
                {loading ? "Stopping…" : "⏹ Stop Simulation"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Live Status */}
      <div style={{ marginTop: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
          <div style={{
            width: "12px", height: "12px", borderRadius: "50%",
            background: isRunning ? "#10b981" : "#6b7280",
            boxShadow: isRunning ? "0 0 8px #10b981" : "none",
          }} />
          <span style={{ color: "#e2e8f0", fontWeight: 600 }}>
            {isRunning ? "Simulation Running" : "Idle"}
          </span>
          {status?.start_time && (
            <span style={{ color: "#9ca3af", fontSize: "0.85rem" }}>
              Started: {new Date(status.start_time).toLocaleTimeString()}
            </span>
          )}
        </div>

        {/* Progress */}
        <div style={progressContainerStyle}>
          <div style={{
            ...progressBarStyle,
            width: `${Math.min(100, (total / maxTickets) * 100)}%`,
          }} />
        </div>
        <p style={{ color: "#9ca3af", fontSize: "0.85rem", marginTop: "0.25rem" }}>
          {total} / {maxTickets} tickets generated
        </p>
      </div>

      {/* Stats Cards */}
      <div style={{ ...cardGridStyle, marginTop: "2rem" }}>
        <StatCard title="Auto-Resolved" value={stats.auto_resolved || 0} color="#10b981" />
        <StatCard title="To Agent" value={stats.suggested_to_agent || 0} color="#f59e0b" />
        <StatCard title="Escalated" value={stats.escalated_to_human || 0} color="#ef4444" />
        <StatCard title="Avg Confidence" value={`${((stats.avg_confidence || 0) * 100).toFixed(1)}%`} color="#8b5cf6" />
        <StatCard
          title="Avg Processing"
          value={`${total > 0 ? Math.round((stats.total_processing_ms || 0) / total) : 0}ms`}
          color="#3b82f6"
        />
      </div>

      {/* Routing Distribution Bar */}
      {total > 0 && (
        <div style={{ marginTop: "2rem" }}>
          <h2 style={{ fontSize: "1.1rem", color: "#e2e8f0", marginBottom: "0.75rem" }}>
            Routing Distribution
          </h2>
          <div style={{ display: "flex", height: "32px", borderRadius: "8px", overflow: "hidden" }}>
            <div style={{
              width: `${(stats.auto_resolved / total) * 100}%`,
              background: "#10b981", display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: "0.75rem", color: "#fff",
            }}>
              {stats.auto_resolved > 0 && `Auto ${Math.round((stats.auto_resolved / total) * 100)}%`}
            </div>
            <div style={{
              width: `${(stats.suggested_to_agent / total) * 100}%`,
              background: "#f59e0b", display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: "0.75rem", color: "#fff",
            }}>
              {stats.suggested_to_agent > 0 && `Agent ${Math.round((stats.suggested_to_agent / total) * 100)}%`}
            </div>
            <div style={{
              width: `${(stats.escalated_to_human / total) * 100}%`,
              background: "#ef4444", display: "flex", alignItems: "center",
              justifyContent: "center", fontSize: "0.75rem", color: "#fff",
            }}>
              {stats.escalated_to_human > 0 && `Esc ${Math.round((stats.escalated_to_human / total) * 100)}%`}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ title, value, color }) {
  return (
    <div style={{
      background: "var(--bg-secondary, #1e293b)", borderRadius: "12px",
      padding: "1.25rem", textAlign: "center", border: `1px solid ${color}22`, minWidth: "140px",
    }}>
      <p style={{ color: "#9ca3af", fontSize: "0.8rem", marginBottom: "0.5rem" }}>{title}</p>
      <p style={{ color, fontSize: "1.5rem", fontWeight: 700, margin: 0 }}>{value}</p>
    </div>
  );
}

const cardGridStyle = { display: "flex", gap: "1rem", flexWrap: "wrap" };
const controlsStyle = {
  background: "var(--bg-secondary, #1e293b)", borderRadius: "12px", padding: "1.5rem",
};
const labelStyle = { display: "block", color: "#9ca3af", fontSize: "0.8rem", marginBottom: "0.25rem" };
const inputStyle = {
  width: "80px", padding: "0.4rem", borderRadius: "6px", border: "1px solid #4b5563",
  background: "#0f172a", color: "#e2e8f0", fontSize: "0.9rem",
};
const startBtnStyle = {
  padding: "0.6rem 1.5rem", borderRadius: "8px", border: "none",
  background: "#10b981", color: "#fff", fontWeight: 600, cursor: "pointer",
};
const stopBtnStyle = {
  padding: "0.6rem 1.5rem", borderRadius: "8px", border: "none",
  background: "#ef4444", color: "#fff", fontWeight: 600, cursor: "pointer",
};
const progressContainerStyle = {
  width: "100%", height: "10px", background: "#1e293b", borderRadius: "5px", overflow: "hidden",
};
const progressBarStyle = {
  height: "100%", background: "linear-gradient(90deg, #3b82f6, #8b5cf6)",
  borderRadius: "5px", transition: "width 0.5s ease",
};
const errorStyle = {
  color: "#ef4444", padding: "0.75rem", border: "1px solid #ef4444", borderRadius: "8px",
  marginBottom: "1rem",
};
