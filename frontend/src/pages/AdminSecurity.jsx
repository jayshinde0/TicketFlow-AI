/**
 * pages/AdminSecurity.jsx — Enhanced Security Threat Center.
 * Integrates AI Attack Detection pipeline with real-time Socket.io updates.
 * DO NOT create a new menu — this replaces the existing AdminSecurity page.
 */

import React, { useState, useEffect, useCallback, useRef } from "react";
import { securityAPI } from "../services/api";

// ─── Constants ────────────────────────────────────────────────────────
const THREAT_LEVEL_CONFIG = {
  attack:     { label: "🚨 Attack",     color: "#ef4444", bg: "#fef2f2", border: "#fca5a5" },
  suspicious: { label: "⚠️ Suspicious", color: "#f59e0b", bg: "#fffbeb", border: "#fcd34d" },
  normal:     { label: "✅ Normal",     color: "#10b981", bg: "#f0fdf4", border: "#6ee7b7" },
};

const THREAT_TYPE_LABELS = {
  sql_injection:      "SQL Injection",
  xss:                "XSS",
  brute_force:        "Brute Force",
  unauthorized_access:"Unauthorized Access",
  ddos:               "DDoS",
  phishing:           "Phishing",
  malware:            "Malware",
  data_breach:        "Data Breach",
  social_engineering: "Social Engineering",
  insider_threat:     "Insider Threat",
  none:               "None",
};

const SEVERITY_COLORS = {
  critical: "#ef4444", high: "#f59e0b", medium: "#3b82f6", low: "#10b981", none: "#6b7280",
};

// ─── Sub-components ───────────────────────────────────────────────────

function StatCard({ title, value, color, icon, subtitle }) {
  return (
    <div style={{
      background: "#1e293b", borderRadius: "12px", padding: "1.25rem",
      border: `1px solid ${color}33`, minWidth: "150px", flex: 1,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <p style={{ color: "#9ca3af", fontSize: "0.78rem", marginBottom: "0.4rem" }}>{title}</p>
          <p style={{ color, fontSize: "1.75rem", fontWeight: 700, margin: 0 }}>{value ?? "—"}</p>
          {subtitle && <p style={{ color: "#6b7280", fontSize: "0.72rem", marginTop: "0.25rem" }}>{subtitle}</p>}
        </div>
        <span style={{ fontSize: "1.5rem" }}>{icon}</span>
      </div>
    </div>
  );
}

function ThreatLevelBadge({ level }) {
  const cfg = THREAT_LEVEL_CONFIG[level] || THREAT_LEVEL_CONFIG.normal;
  return (
    <span style={{
      background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`,
      borderRadius: "6px", padding: "2px 8px", fontSize: "0.72rem", fontWeight: 700,
      whiteSpace: "nowrap",
    }}>
      {cfg.label}
    </span>
  );
}

function AIBadge({ rules = [] }) {
  if (!rules || rules.length === 0) return null;
  return (
    <span style={{
      background: "#1d4ed8", color: "#bfdbfe", borderRadius: "6px",
      padding: "2px 7px", fontSize: "0.68rem", fontWeight: 600,
    }}>
      🤖 AI Detected
    </span>
  );
}

function RuleTag({ rule }) {
  const colors = {
    sql_injection: "#dc2626", xss: "#7c3aed", brute_force: "#d97706",
    unauthorized_access: "#0891b2", ddos: "#be185d",
    suspicious_keywords: "#6b7280", anomaly_detected: "#9333ea",
    similar_to_past_attack: "#b45309",
  };
  return (
    <span style={{
      background: `${colors[rule] || "#374151"}22`,
      color: colors[rule] || "#9ca3af",
      border: `1px solid ${colors[rule] || "#374151"}44`,
      borderRadius: "4px", padding: "1px 6px", fontSize: "0.65rem", fontWeight: 600,
    }}>
      {rule.replace(/_/g, " ")}
    </span>
  );
}

function FilterTab({ label, active, onClick, count }) {
  return (
    <button onClick={onClick} style={{
      padding: "0.45rem 1rem", border: "1px solid #4b5563", borderRadius: "8px",
      cursor: "pointer", fontSize: "0.82rem", transition: "all 0.2s",
      background: active ? "#3b82f6" : "transparent",
      color: active ? "#fff" : "#9ca3af",
      display: "flex", alignItems: "center", gap: "0.4rem",
    }}>
      {label}
      {count !== undefined && (
        <span style={{
          background: active ? "rgba(255,255,255,0.25)" : "#374151",
          borderRadius: "10px", padding: "0 6px", fontSize: "0.7rem",
        }}>{count}</span>
      )}
    </button>
  );
}

function LogsModal({ ticketId, onClose }) {
  const [logs, setLogs] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    securityAPI.getLogs(ticketId)
      .then(r => setLogs(r.data))
      .catch(() => setLogs({ security_logs: [], triggered_rules: [], detection_reason: "" }))
      .finally(() => setLoading(false));
  }, [ticketId]);

  return (
    <div style={modalOverlayStyle} onClick={onClose}>
      <div style={{ ...modalStyle, maxWidth: "700px" }} onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h2 style={{ color: "#e2e8f0", margin: 0 }}>🔍 Security Logs — {ticketId}</h2>
          <button onClick={onClose} style={closeBtnStyle}>✕</button>
        </div>
        {loading ? <p style={{ color: "#9ca3af" }}>Loading…</p> : (
          <>
            {logs?.detection_reason && (
              <div style={{ background: "#0f172a", borderRadius: "8px", padding: "0.75rem", marginBottom: "1rem" }}>
                <p style={{ color: "#94a3b8", fontSize: "0.8rem", margin: 0 }}>
                  <strong style={{ color: "#e2e8f0" }}>Detection Reason:</strong> {logs.detection_reason}
                </p>
              </div>
            )}
            {logs?.triggered_rules?.length > 0 && (
              <div style={{ marginBottom: "1rem" }}>
                <p style={{ color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.5rem" }}>Triggered Rules:</p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                  {logs.triggered_rules.map(r => <RuleTag key={r} rule={r} />)}
                </div>
              </div>
            )}
            <p style={{ color: "#94a3b8", fontSize: "0.8rem", marginBottom: "0.5rem" }}>Action Log:</p>
            {(logs?.security_logs || []).length === 0
              ? <p style={{ color: "#6b7280", fontSize: "0.82rem" }}>No actions recorded yet.</p>
              : (logs.security_logs || []).map((log, i) => (
                <div key={i} style={{ background: "#0f172a", borderRadius: "8px", padding: "0.6rem 0.75rem", marginBottom: "0.5rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#60a5fa", fontSize: "0.78rem", fontWeight: 600 }}>{log.action}</span>
                    <span style={{ color: "#6b7280", fontSize: "0.72rem" }}>{new Date(log.timestamp).toLocaleString()}</span>
                  </div>
                  <p style={{ color: "#94a3b8", fontSize: "0.75rem", margin: "0.25rem 0 0" }}>
                    By: {log.actor}{log.reason ? ` — ${log.reason}` : ""}
                  </p>
                </div>
              ))
            }
          </>
        )}
        <button onClick={onClose} style={{ ...actionBtnStyle, marginTop: "1rem" }}>Close</button>
      </div>
    </div>
  );
}

function PlaybookModal({ threatType, onClose }) {
  const [playbook, setPlaybook] = useState(null);
  useEffect(() => {
    securityAPI.playbook(threatType)
      .then(r => setPlaybook(r.data?.playbook))
      .catch(() => {});
  }, [threatType]);

  return (
    <div style={modalOverlayStyle} onClick={onClose}>
      <div style={modalStyle} onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h2 style={{ color: "#e2e8f0", margin: 0 }}>📋 {playbook?.title || "Playbook"}</h2>
          <button onClick={onClose} style={closeBtnStyle}>✕</button>
        </div>
        {playbook ? (
          <ol style={{ paddingLeft: "1.25rem", lineHeight: 1.9 }}>
            {playbook.steps?.map((step, i) => (
              <li key={i} style={{ color: "#e2e8f0", marginBottom: "0.4rem", fontSize: "0.88rem" }}>{step}</li>
            ))}
          </ol>
        ) : <p style={{ color: "#9ca3af" }}>Loading playbook…</p>}
        <button onClick={onClose} style={{ ...actionBtnStyle, marginTop: "1rem" }}>Close</button>
      </div>
    </div>
  );
}

function EscalateModal({ ticket, onClose, onDone }) {
  const [reason, setReason] = useState("");
  const [threatType, setThreatType] = useState(ticket?.threat_type || "unauthorized_access");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!reason.trim()) return;
    setLoading(true);
    try {
      await securityAPI.escalateTicket({
        ticket_id: ticket.ticket_id,
        reason,
        threat_type: threatType,
        severity: "high",
      });
      onDone();
      onClose();
    } catch (e) {
      alert(e.response?.data?.detail || "Escalation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={modalOverlayStyle} onClick={onClose}>
      <div style={{ ...modalStyle, maxWidth: "500px" }} onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h2 style={{ color: "#ef4444", margin: 0 }}>🚨 Escalate Ticket</h2>
          <button onClick={onClose} style={closeBtnStyle}>✕</button>
        </div>
        <p style={{ color: "#94a3b8", fontSize: "0.85rem", marginBottom: "1rem" }}>
          Ticket: <strong style={{ color: "#e2e8f0" }}>{ticket?.ticket_id}</strong>
        </p>
        <label style={labelStyle}>Threat Type</label>
        <select value={threatType} onChange={e => setThreatType(e.target.value)} style={inputStyle}>
          {Object.entries(THREAT_TYPE_LABELS).filter(([k]) => k !== "none").map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <label style={{ ...labelStyle, marginTop: "0.75rem" }}>Reason *</label>
        <textarea
          value={reason}
          onChange={e => setReason(e.target.value)}
          placeholder="Describe why this ticket is being escalated…"
          rows={4}
          style={{ ...inputStyle, resize: "vertical" }}
        />
        <div style={{ display: "flex", gap: "0.5rem", marginTop: "1rem" }}>
          <button onClick={handleSubmit} disabled={loading || !reason.trim()} style={{
            ...actionBtnStyle, background: "#ef4444", flex: 1, opacity: loading ? 0.6 : 1,
          }}>
            {loading ? "Escalating…" : "🚨 Escalate to Security Team"}
          </button>
          <button onClick={onClose} style={actionBtnStyle}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

// ─── Attack Notification Toast ────────────────────────────────────────
function AttackToast({ alert, onDismiss }) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 8000);
    return () => clearTimeout(t);
  }, [onDismiss]);

  return (
    <div style={{
      position: "fixed", top: "1.5rem", right: "1.5rem", zIndex: 9999,
      background: "#1e293b", border: "2px solid #ef4444", borderRadius: "12px",
      padding: "1rem 1.25rem", maxWidth: "360px", boxShadow: "0 8px 32px rgba(239,68,68,0.3)",
      animation: "slideIn 0.3s ease",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <p style={{ color: "#ef4444", fontWeight: 700, margin: "0 0 0.25rem", fontSize: "0.9rem" }}>
            🚨 New Security Alert
          </p>
          <p style={{ color: "#e2e8f0", fontSize: "0.82rem", margin: "0 0 0.25rem" }}>
            Ticket: <strong>{alert.ticket_id}</strong>
          </p>
          <p style={{ color: "#94a3b8", fontSize: "0.78rem", margin: 0 }}>
            {THREAT_TYPE_LABELS[alert.threat_type] || alert.threat_type} — {alert.threat_level}
          </p>
        </div>
        <button onClick={onDismiss} style={{ ...closeBtnStyle, marginLeft: "0.5rem" }}>✕</button>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────
export default function AdminSecurity() {
  const [stats, setStats] = useState(null);
  const [threats, setThreats] = useState([]);
  const [filter, setFilter] = useState("all");
  const [levelFilter, setLevelFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [playbook, setPlaybook] = useState(null);
  const [logsTicketId, setLogsTicketId] = useState(null);
  const [escalateTicket, setEscalateTicket] = useState(null);
  const [toasts, setToasts] = useState([]);
  const wsRef = useRef(null);

  // ── Fetch data ──────────────────────────────────────────────────────
  const fetchData = useCallback(async () => {
    try {
      const statusParam = filter === "all" ? undefined : filter;
      const [s, t] = await Promise.all([
        securityAPI.stats(),
        securityAPI.threats({ status: statusParam, page_size: 100 }),
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
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // ── WebSocket for real-time alerts ──────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem("access_token") || localStorage.getItem("token");
    const wsUrl = `${(process.env.REACT_APP_API_URL || "http://localhost:8000").replace("http", "ws")}/ws/admin${token ? `?token=${token}` : ""}`;

    const connect = () => {
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === "security_alert") {
              const alert = msg.data;
              // Add toast notification
              setToasts(prev => [...prev, { id: Date.now(), ...alert }]);
              // Refresh data to show new threat
              fetchData();
            }
          } catch (_) {}
        };

        ws.onclose = () => {
          // Reconnect after 5s
          setTimeout(connect, 5000);
        };
      } catch (_) {}
    };

    connect();
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [fetchData]);

  // ── Actions ─────────────────────────────────────────────────────────
  const handleAcknowledge = async (ticketId) => {
    try {
      await securityAPI.acknowledge(ticketId);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Acknowledge failed");
    }
  };

  const handleResolve = async (ticketId) => {
    if (!window.confirm("Mark this threat as resolved?")) return;
    try {
      await securityAPI.resolve(ticketId);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Resolve failed");
    }
  };

  const dismissToast = (id) => setToasts(prev => prev.filter(t => t.id !== id));

  // ── Filter threats ───────────────────────────────────────────────────
  const filteredThreats = threats.filter(t => {
    if (levelFilter === "all") return true;
    return (t.threat_level || "attack") === levelFilter;
  });

  if (loading) return (
    <div style={{ padding: "2rem", color: "#9ca3af" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <span style={{ fontSize: "1.5rem" }}>🛡️</span>
        <span>Loading Security Threat Center…</span>
      </div>
    </div>
  );

  return (
    <div style={{ padding: "2rem", maxWidth: "1400px" }}>
      {/* Toast notifications */}
      {toasts.map(toast => (
        <AttackToast key={toast.id} alert={toast} onDismiss={() => dismissToast(toast.id)} />
      ))}

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1 style={{ fontSize: "1.5rem", margin: 0, color: "#e2e8f0" }}>🛡️ Security Threat Center</h1>
          <p style={{ color: "#6b7280", fontSize: "0.82rem", margin: "0.25rem 0 0" }}>
            AI-powered attack detection • Real-time monitoring
          </p>
        </div>
        <button onClick={fetchData} style={{ ...actionBtnStyle, background: "#1e40af" }}>
          🔄 Refresh
        </button>
      </div>

      {error && <div style={errorStyle}>{error}</div>}

      {/* Stat Cards */}
      {stats && (
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", marginBottom: "1.5rem" }}>
          <StatCard title="Total Threats" value={stats.total_threats} color="#ef4444" icon="🎯"
            subtitle={`${stats.total} escalations`} />
          <StatCard title="Suspicious" value={stats.suspicious_count} color="#f59e0b" icon="⚠️"
            subtitle="Pending review" />
          <StatCard title="Active Attacks" value={stats.attack_count} color="#dc2626" icon="🚨"
            subtitle="Immediate action" />
          <StatCard title="Resolved" value={stats.resolved_count} color="#10b981" icon="✅"
            subtitle="Closed threats" />
        </div>
      )}

      {/* Breakdown panels */}
      {stats && (
        <div style={{ display: "flex", gap: "1.5rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
          <div style={miniTableStyle}>
            <h3 style={h3Style}>By Severity</h3>
            {Object.entries(stats.severity_breakdown || {}).map(([k, v]) => (
              <div key={k} style={rowStyle}>
                <span style={{ color: SEVERITY_COLORS[k] || "#9ca3af" }}>● {k}</span>
                <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>
          <div style={miniTableStyle}>
            <h3 style={h3Style}>By Threat Type</h3>
            {Object.entries(stats.type_breakdown || {}).map(([k, v]) => (
              <div key={k} style={rowStyle}>
                <span>{THREAT_TYPE_LABELS[k] || k}</span>
                <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>
          <div style={miniTableStyle}>
            <h3 style={h3Style}>Threat Level Breakdown</h3>
            {Object.entries(stats.threat_level_breakdown || {}).map(([k, v]) => {
              const cfg = THREAT_LEVEL_CONFIG[k] || {};
              return (
                <div key={k} style={rowStyle}>
                  <span style={{ color: cfg.color || "#9ca3af" }}>{cfg.label || k}</span>
                  <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{v}</span>
                </div>
              );
            })}
          </div>
          <div style={miniTableStyle}>
            <h3 style={h3Style}>Escalation Levels</h3>
            {Object.entries(stats.active_escalation_levels || {}).map(([k, v]) => (
              <div key={k} style={rowStyle}>
                <span style={{ color: k === "L3" ? "#ef4444" : k === "L2" ? "#f59e0b" : "#3b82f6" }}>{k}</span>
                <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filter tabs */}
      <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
        <div style={{ display: "flex", gap: "0.4rem", marginRight: "1rem" }}>
          {[
            { key: "all", label: "All Status" },
            { key: "pending", label: "Pending" },
            { key: "acknowledged", label: "Acknowledged" },
            { key: "resolved", label: "Resolved" },
          ].map(f => (
            <FilterTab key={f.key} label={f.label} active={filter === f.key}
              onClick={() => { setFilter(f.key); setLoading(true); }} />
          ))}
        </div>
        <div style={{ display: "flex", gap: "0.4rem" }}>
          {[
            { key: "all", label: "All Levels" },
            { key: "attack", label: "🚨 Attack", count: stats?.attack_count },
            { key: "suspicious", label: "⚠️ Suspicious", count: stats?.suspicious_count },
            { key: "normal", label: "✅ Normal" },
          ].map(f => (
            <FilterTab key={f.key} label={f.label} active={levelFilter === f.key}
              count={f.count} onClick={() => setLevelFilter(f.key)} />
          ))}
        </div>
      </div>

      {/* Threat count */}
      <p style={{ color: "#6b7280", fontSize: "0.8rem", marginBottom: "0.75rem" }}>
        Showing {filteredThreats.length} threat{filteredThreats.length !== 1 ? "s" : ""}
      </p>

      {/* Threat Feed */}
      <div>
        {filteredThreats.length === 0 ? (
          <div style={{ textAlign: "center", padding: "3rem", color: "#6b7280" }}>
            <div style={{ fontSize: "3rem", marginBottom: "0.75rem" }}>🛡️</div>
            <p>No threats in this category</p>
          </div>
        ) : (
          filteredThreats.map((t, i) => (
            <ThreatCard
              key={i}
              threat={t}
              onAcknowledge={handleAcknowledge}
              onResolve={handleResolve}
              onPlaybook={(type) => setPlaybook(type)}
              onLogs={(id) => setLogsTicketId(id)}
              onEscalate={(threat) => setEscalateTicket(threat)}
            />
          ))
        )}
      </div>

      {/* Modals */}
      {playbook && <PlaybookModal threatType={playbook} onClose={() => setPlaybook(null)} />}
      {logsTicketId && <LogsModal ticketId={logsTicketId} onClose={() => setLogsTicketId(null)} />}
      {escalateTicket && (
        <EscalateModal
          ticket={escalateTicket}
          onClose={() => setEscalateTicket(null)}
          onDone={fetchData}
        />
      )}
    </div>
  );
}

// ─── ThreatCard ───────────────────────────────────────────────────────
function ThreatCard({ threat, onAcknowledge, onResolve, onPlaybook, onLogs, onEscalate }) {
  const [expanded, setExpanded] = useState(false);
  const threatLevel = threat.threat_level || "attack";
  const cfg = THREAT_LEVEL_CONFIG[threatLevel] || THREAT_LEVEL_CONFIG.attack;
  const isResolved = threat.resolved;
  const isAcknowledged = threat.acknowledged;

  return (
    <div style={{
      background: "#1e293b", borderRadius: "12px", padding: "1rem 1.25rem",
      marginBottom: "0.75rem", border: `1px solid ${cfg.border}44`,
      borderLeft: `4px solid ${cfg.color}`,
    }}>
      {/* Top row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.5rem" }}>
        <div style={{ flex: 1 }}>
          {/* Badges row */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginBottom: "0.5rem", alignItems: "center" }}>
            <ThreatLevelBadge level={threatLevel} />
            <AIBadge rules={threat.triggered_rules} />
            {isAcknowledged && !isResolved && (
              <span style={{ background: "#1e3a5f", color: "#60a5fa", borderRadius: "6px", padding: "2px 7px", fontSize: "0.68rem", fontWeight: 600 }}>
                👁 Acknowledged
              </span>
            )}
            {isResolved && (
              <span style={{ background: "#064e3b", color: "#34d399", borderRadius: "6px", padding: "2px 7px", fontSize: "0.68rem", fontWeight: 600 }}>
                ✅ Resolved
              </span>
            )}
          </div>

          {/* Ticket info */}
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>
            <span style={{ color: "#60a5fa", fontWeight: 700, fontSize: "0.9rem" }}>
              {threat.ticket_id}
            </span>
            {threat.subject && (
              <span style={{ color: "#e2e8f0", fontSize: "0.85rem" }}>{threat.subject}</span>
            )}
          </div>

          {/* Threat type + severity */}
          <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.35rem", flexWrap: "wrap" }}>
            <span style={{ color: SEVERITY_COLORS[threat.severity] || "#9ca3af", fontSize: "0.78rem", fontWeight: 600 }}>
              ● {threat.severity?.toUpperCase() || "HIGH"} severity
            </span>
            <span style={{ color: "#94a3b8", fontSize: "0.78rem" }}>
              Type: <strong style={{ color: "#e2e8f0" }}>{THREAT_TYPE_LABELS[threat.threat_type] || threat.threat_type || "Unknown"}</strong>
            </span>
            {threat.ai_confidence !== undefined && (
              <span style={{ color: "#94a3b8", fontSize: "0.78rem" }}>
                AI Confidence: <strong style={{ color: "#e2e8f0" }}>{(threat.ai_confidence * 100).toFixed(0)}%</strong>
              </span>
            )}
            <span style={{ color: "#6b7280", fontSize: "0.75rem" }}>
              Level: {threat.current_level} • {new Date(threat.created_at).toLocaleString()}
            </span>
          </div>

          {/* Triggered rules */}
          {threat.triggered_rules?.length > 0 && (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.3rem", marginTop: "0.5rem" }}>
              {threat.triggered_rules.map(r => <RuleTag key={r} rule={r} />)}
            </div>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: "flex", flexDirection: "column", gap: "0.4rem", alignItems: "flex-end" }}>
          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
            <button onClick={() => onPlaybook(threat.threat_type)} style={actionBtnStyle}>
              📋 Playbook
            </button>
            <button onClick={() => onLogs(threat.ticket_id)} style={actionBtnStyle}>
              📄 Logs
            </button>
          </div>
          <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
            {!isAcknowledged && !isResolved && (
              <button onClick={() => onAcknowledge(threat.ticket_id)}
                style={{ ...actionBtnStyle, background: "#1e40af" }}>
                👁 Acknowledge
              </button>
            )}
            {!isResolved && (
              <>
                <button onClick={() => onEscalate(threat)}
                  style={{ ...actionBtnStyle, background: "#7c2d12" }}>
                  🚨 Escalate
                </button>
                <button onClick={() => onResolve(threat.ticket_id)}
                  style={{ ...actionBtnStyle, background: "#064e3b" }}>
                  ✅ Resolve
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Detection reason (expandable) */}
      {threat.detection_reason && (
        <div style={{ marginTop: "0.6rem" }}>
          <button onClick={() => setExpanded(!expanded)} style={{
            background: "none", border: "none", color: "#6b7280", cursor: "pointer",
            fontSize: "0.75rem", padding: 0,
          }}>
            {expanded ? "▲ Hide" : "▼ Show"} detection details
          </button>
          {expanded && (
            <div style={{ background: "#0f172a", borderRadius: "6px", padding: "0.6rem 0.75rem", marginTop: "0.4rem" }}>
              <p style={{ color: "#94a3b8", fontSize: "0.78rem", margin: 0 }}>
                {threat.detection_reason}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Styles ───────────────────────────────────────────────────────────
const h3Style = { fontSize: "0.88rem", marginBottom: "0.6rem", color: "#e2e8f0", fontWeight: 600 };
const miniTableStyle = {
  background: "#1e293b", borderRadius: "12px", padding: "1rem", flex: "1", minWidth: "180px",
};
const rowStyle = {
  display: "flex", justifyContent: "space-between", padding: "0.3rem 0",
  color: "#94a3b8", fontSize: "0.82rem", borderBottom: "1px solid #1e293b",
};
const errorStyle = {
  color: "#ef4444", padding: "0.75rem", border: "1px solid #ef4444",
  borderRadius: "8px", marginBottom: "1rem", fontSize: "0.85rem",
};
const actionBtnStyle = {
  padding: "0.4rem 0.75rem", border: "none", borderRadius: "6px",
  background: "#374151", color: "#e2e8f0", cursor: "pointer", fontSize: "0.78rem",
  whiteSpace: "nowrap",
};
const modalOverlayStyle = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.75)", display: "flex",
  alignItems: "center", justifyContent: "center", zIndex: 1000,
};
const modalStyle = {
  background: "#1e293b", borderRadius: "16px", padding: "2rem",
  maxWidth: "600px", width: "90%", maxHeight: "80vh", overflowY: "auto",
};
const closeBtnStyle = {
  background: "none", border: "none", color: "#9ca3af", cursor: "pointer",
  fontSize: "1.1rem", padding: "0.25rem",
};
const inputStyle = {
  width: "100%", background: "#0f172a", border: "1px solid #374151",
  borderRadius: "6px", padding: "0.5rem 0.75rem", color: "#e2e8f0",
  fontSize: "0.85rem", boxSizing: "border-box",
};
const labelStyle = {
  display: "block", color: "#94a3b8", fontSize: "0.78rem",
  marginBottom: "0.35rem", fontWeight: 600,
};
