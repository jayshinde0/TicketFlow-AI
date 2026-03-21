/**
 * pages/AgentQueue.jsx — Live queue of tickets awaiting agent review.
 */
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { agentsAPI } from "../services/api";
import Loader, { RoutingBadge, PriorityBadge, ConfidenceBar, EmptyState } from "../components/ui/Loader";
import { useNotifications } from "../contexts/NotificationContext";
import { RefreshCw, ListTodo } from "lucide-react";

export default function AgentQueue() {
  const [queue,   setQueue]   = useState([]);
  const [loading, setLoading] = useState(true);
  const { liveTickets }       = useNotifications();
  const navigate              = useNavigate();

  const load = () => {
    setLoading(true);
    agentsAPI.queue()
      .then((r) => setQueue(r.data.items || []))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  // Prepend live new tickets (deduplicated)
  useEffect(() => {
    if (liveTickets.length > 0) load();
  }, [liveTickets.length]);

  if (loading) return <Loader text="Loading queue…" />;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Agent Queue</h1>
          <p className="page-subtitle">{queue.length} ticket{queue.length !== 1 ? "s" : ""} awaiting review</p>
        </div>
        <button onClick={load} className="btn-secondary btn-sm">
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {queue.length === 0 ? (
        <div className="card">
          <EmptyState icon={ListTodo} title="Queue is empty" subtitle="All tickets have been resolved!" />
        </div>
      ) : (
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th>Ticket ID</th>
                <th>Subject</th>
                <th>Category</th>
                <th>Priority</th>
                <th>Routing</th>
                <th>Confidence</th>
                <th>Sentiment</th>
                <th>SLA Risk</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {queue.map((t) => {
                const ai = t.ai_analysis || {};
                return (
                  <tr
                    key={t.ticket_id}
                    className="cursor-pointer"
                    onClick={() => navigate(`/tickets/${t.ticket_id}`)}
                  >
                    <td className="font-mono text-xs text-brand-400">{t.ticket_id}</td>
                    <td className="max-w-xs">
                      <span className="truncate block text-gray-200" title={t.subject}>{t.subject}</span>
                    </td>
                    <td className="text-gray-400 text-xs">{ai.category || "—"}</td>
                    <td><PriorityBadge priority={ai.priority} /></td>
                    <td><RoutingBadge decision={ai.routing_decision} /></td>
                    <td className="w-28">
                      <ConfidenceBar score={ai.confidence_score} />
                    </td>
                    <td className="text-xs text-gray-400 capitalize">{ai.sentiment_label || "—"}</td>
                    <td className="text-xs">
                      <span className={
                        (ai.sla_breach_probability || 0) > 0.75 ? "text-red-400" :
                        (ai.sla_breach_probability || 0) > 0.5  ? "text-amber-400" :
                        "text-gray-400"
                      }>
                        {ai.sla_breach_probability ? `${Math.round(ai.sla_breach_probability * 100)}%` : "—"}
                      </span>
                    </td>
                    <td className="text-xs text-gray-500 whitespace-nowrap">
                      {new Date(t.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
