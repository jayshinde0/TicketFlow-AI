/**
 * pages/MyTickets.jsx — User's personal ticket history.
 */
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ticketsAPI } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import Loader, { RoutingBadge, PriorityBadge, ConfidenceBar, EmptyState } from "../components/ui/Loader";
import { Ticket, PlusCircle } from "lucide-react";

export default function MyTickets() {
  const { user }     = useAuth();
  const navigate     = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    ticketsAPI.list({ page_size: 50 })
      .then((r) => setTickets(r.data.tickets || []))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader text="Loading your tickets…" />;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">My Tickets</h1>
          <p className="page-subtitle">{tickets.length} ticket{tickets.length !== 1 ? "s" : ""} submitted</p>
        </div>
        <button onClick={() => navigate("/submit")} className="btn-primary">
          <PlusCircle size={15} /> New Ticket
        </button>
      </div>

      {tickets.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={Ticket}
            title="No tickets yet"
            subtitle="Submit your first ticket and our AI will handle it instantly."
            action={
              <button onClick={() => navigate("/submit")} className="btn-primary">
                <PlusCircle size={15} /> Submit Ticket
              </button>
            }
          />
        </div>
      ) : (
        <div className="space-y-3">
          {tickets.map((t) => (
            <div
              key={t.ticket_id}
              className="card-hover cursor-pointer"
              onClick={() => navigate(`/tickets/${t.ticket_id}`)}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="font-mono text-xs text-brand-400">{t.ticket_id}</span>
                    <span className={`badge text-xs ${t.status === "resolved"
                      ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/25"
                      : "bg-blue-500/15 text-blue-400 border-blue-500/25"}`}>
                      {t.status}
                    </span>
                    <PriorityBadge priority={t.priority} />
                    <RoutingBadge decision={t.routing_decision} />
                  </div>
                  <p className="font-medium text-gray-200 truncate">{t.subject || "(No subject)"}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {t.category || "—"} · {new Date(t.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="w-28 shrink-0">
                  <p className="text-xs text-gray-500 mb-1 text-right">
                    {t.confidence_score ? `${Math.round(t.confidence_score * 100)}%` : ""}
                  </p>
                  <ConfidenceBar score={t.confidence_score} showLabel={false} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
