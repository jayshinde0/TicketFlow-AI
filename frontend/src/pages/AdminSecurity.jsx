/**
 * pages/AdminSecurity.jsx — Security Threat Feed page.
 * Shows live threat feed, severity breakdown, escalation levels,
 * and playbook viewer.
 */

import React, { useState, useEffect, useCallback } from "react";
import { securityAPI } from "../services/api";

export default function AdminSecurity() {
  const [stats, setStats] = useState(null);
  const [threats, setThreats] = useState([]);
  const [filter, setFilter] = useState("pending");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [playbook, setPlaybook] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([
        securityAPI.stats(),
        securityAPI.threats({ status: filter, page_size: 50 }),
      ]);
      setStats(s.data);
      setThreats(t.data?.items || []);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load security data");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleAcknowledge = async (ticketId) => {
    try {
      await securityAPI.acknowledge(ticketId);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Acknowledge failed");
    }
  };

  const handleViewPlaybook = async (type) => {
    try {
      const res = await securityAPI.playbook(type);
      setPlaybook(res.data?.playbook || null);
    } catch {
      alert("Failed to load playbook");
    }
  };

  if (loading) return <div style={{ padding: "2rem" }}>Loading security data…</div>;

  return (
    <div style={{ padding: "2rem" }}>
      <h1 style={{ fontSize: "1.5rem", marginBottom: "1.5rem" }}>🛡️ Security Threat Center</h1>

      {error && <div style={errorStyle}>{error}</div>}

      {/* Stats Overview */}
      {stats && (
        <div style={cardGridStyle}>
          <StatCard title="Total Threats" value={stats.total} color="#ef4444" />
          <StatCard title="Pending" value={stats.pending} color="#f59e0b" />
          <StatCard title="Acknowledged" value={stats.acknowledged} color="#3b82f6" />
          <StatCard title="Resolved" value={stats.resolved} color="#10b981" />
        </div>
      )}

      {/* Severity + Type Breakdown */}
      {stats && (
        <div style={{ display: "flex", gap: "2rem", marginTop: "1.5rem", flexWrap: "wrap" }}>
          <div style={miniTableStyle}>
            <h3 style={h3Style}>By Severity</h3>
            {Object.entries(stats.severity_breakdown || {}).map(([k, v]) => (
              <div key={k} style={rowStyle}>
                <span style={{ color: severityColor(k) }}>● {k}</span>
                <span>{v}</span>
              </div>
            ))}
          </div>
          <div style={miniTableStyle}>
            <h3 style={h3Style}>By Type</h3>
            {Object.entries(stats.type_breakdown || {}).map(([k, v]) => (
              <div key={k} style={rowStyle}>
                <span>{k}</span>
                <span>{v}</span>
              </div>
            ))}
          </div>
          <div style={miniTableStyle}>
            <h3 style={h3Style}>Active Escalation Levels</h3>
            {Object.entries(stats.active_escalation_levels || {}).map(([k, v]) => (
              <div key={k} style={rowStyle}>
                <span style={{ color: k === "L3" ? "#ef4444" : k === "L2" ? "#f59e0b" : "#3b82f6" }}>{k}</span>
                <span>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div style={{ display: "flex", gap: "0.5rem", marginTop: "2rem" }}>
        {["pending", "acknowledged", "resolved"].map(f => (
          <button
            key={f}
            onClick={() => { setFilter(f); setLoading(true); }}
            style={{
              ...tabBtnStyle,
              background: filter === f ? "#3b82f6" : "transparent",
              color: filter === f ? "#fff" : "#9ca3af",
            }}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Threat Feed */}
      <div style={{ marginTop: "1rem" }}>
        {threats.length === 0 ? (
          <p style={{ color: "#9ca3af" }}>No threats in this category</p>
        ) : (
          threats.map((t, i) => (
            <div key={i} style={threatCardStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <span style={{
                    color: severityColor(t.severity),
                    fontWeight: 700,
                    textTransform: "uppercase",
                    fontSize: "0.75rem",
                  }}>
                    {t.severity} — {t.threat_type}
                  </span>
                  <p style={{ margin: "0.25rem 0", color: "#e2e8f0" }}>
                    Ticket: <strong>{t.ticket_id}</strong>
                  </p>
                  <p style={{ color: "#9ca3af", fontSize: "0.82rem" }}>
                    Level: {t.current_level} • Created: {new Date(t.created_at).toLocaleString()}
                  </p>
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <button
                    onClick={() => handleViewPlaybook(t.threat_type)}
                    style={actionBtnStyle}
                  >
                    📋 Playbook
                  </button>
                  {!t.acknowledged && (
                    <button
                      onClick={() => handleAcknowledge(t.ticket_id)}
                      style={{ ...actionBtnStyle, background: "#10b981" }}
                    >
                      ✓ Acknowledge
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Playbook Modal */}
      {playbook && (
        <div style={modalOverlayStyle} onClick={() => setPlaybook(null)}>
          <div style={modalStyle} onClick={e => e.stopPropagation()}>
            <h2 style={{ marginBottom: "1rem" }}>{playbook.title}</h2>
            <ol style={{ paddingLeft: "1.25rem", lineHeight: 1.8 }}>
              {playbook.steps?.map((step, i) => (
                <li key={i} style={{ color: "#e2e8f0", marginBottom: "0.5rem" }}>{step}</li>
              ))}
            </ol>
            <button onClick={() => setPlaybook(null)} style={{ ...actionBtnStyle, marginTop: "1rem" }}>
              Close
            </button>
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

function severityColor(sev) {
  return { critical: "#ef4444", high: "#f59e0b", medium: "#3b82f6", low: "#10b981", none: "#6b7280" }[sev] || "#9ca3af";
}

const cardGridStyle = { display: "flex", gap: "1rem", flexWrap: "wrap" };
const h3Style = { fontSize: "0.95rem", marginBottom: "0.75rem", color: "#e2e8f0" };
const miniTableStyle = {
  background: "var(--bg-secondary, #1e293b)", borderRadius: "12px",
  padding: "1rem", flex: "1", minWidth: "200px",
};
const rowStyle = {
  display: "flex", justifyContent: "space-between", padding: "0.35rem 0",
  color: "#e2e8f0", fontSize: "0.85rem",
};
const threatCardStyle = {
  background: "var(--bg-secondary, #1e293b)", borderRadius: "12px",
  padding: "1rem", marginBottom: "0.75rem", border: "1px solid #374151",
};
const errorStyle = { color: "#ef4444", padding: "0.75rem", border: "1px solid #ef4444", borderRadius: "8px", marginBottom: "1rem" };
const tabBtnStyle = {
  padding: "0.5rem 1rem", border: "1px solid #4b5563", borderRadius: "8px",
  cursor: "pointer", fontSize: "0.85rem", transition: "all 0.2s",
};
const actionBtnStyle = {
  padding: "0.4rem 0.75rem", border: "none", borderRadius: "6px",
  background: "#374151", color: "#e2e8f0", cursor: "pointer", fontSize: "0.8rem",
};
const modalOverlayStyle = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex",
  alignItems: "center", justifyContent: "center", zIndex: 1000,
};
const modalStyle = {
  background: "#1e293b", borderRadius: "16px", padding: "2rem",
  maxWidth: "600px", width: "90%", maxHeight: "80vh", overflowY: "auto",
};
