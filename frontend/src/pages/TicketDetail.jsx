/**
 * pages/TicketDetail.jsx — Full ticket detail with AI analysis, LIME explanation, and agent actions.
 */
import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ticketsAPI, feedbackAPI } from "../services/api";
import Loader, { RoutingBadge, PriorityBadge, ConfidenceBar } from "../components/ui/Loader";
import { useAuth } from "../contexts/AuthContext";
import toast from "react-hot-toast";
import {
  Brain, CheckCircle2, Edit3, XCircle, ChevronUp, ArrowLeft,
  Clock, Shield, Activity, MessageSquare,
} from "lucide-react";

export default function TicketDetail() {
  const { id }           = useParams();
  const { isAgent }      = useAuth();
  const navigate         = useNavigate();
  const [ticket,setTicket]       = useState(null);
  const [lime,  setLime]         = useState(null);
  const [similar,setSimilar]     = useState([]);
  const [loading,setLoading]     = useState(true);
  const [editing,setEditing]     = useState(false);
  const [editedRes, setEditedRes]= useState("");
  const [acting, setActing]      = useState(false);

  useEffect(() => {
    Promise.all([
      ticketsAPI.get(id),
      ticketsAPI.explain(id).catch(() => ({ data: {} })),
      ticketsAPI.similar(id).catch(() => ({ data: { similar_tickets: [] } })),
    ]).then(([t, e, s]) => {
      setTicket(t.data);
      setLime(e.data?.lime_explanation);
      setSimilar(s.data?.similar_tickets || []);
      setEditedRes(t.data?.ai_analysis?.generated_response || "");
    }).finally(() => setLoading(false));
  }, [id]);

  const doAction = async (type, extra = {}) => {
    setActing(true);
    try {
      if (type === "approve") await feedbackAPI.approve(id, {});
      if (type === "edit")    await feedbackAPI.edit(id, { corrected_response: editedRes, ...extra });
      if (type === "reject")  await feedbackAPI.reject(id, { manual_response: editedRes, rejection_reason: extra.reason || "" });
      toast.success(`Ticket ${type === "approve" ? "approved" : type === "edit" ? "edited & resolved" : "rejected"}`);
      navigate("/queue");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Action failed");
    } finally {
      setActing(false);
    }
  };

  if (loading) return <Loader text="Loading ticket…" />;
  if (!ticket) return <div className="text-gray-400 text-center py-20">Ticket not found</div>;

  const ai = ticket.ai_analysis || {};

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="btn-ghost btn-sm">
          <ArrowLeft size={14} /> Back
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-mono text-sm text-brand-400">{ticket.ticket_id}</span>
            <RoutingBadge decision={ai.routing_decision} />
            <PriorityBadge priority={ai.priority} />
            <span className={`badge ${ticket.status === "resolved" ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/25" : "bg-blue-500/15 text-blue-400 border-blue-500/25"}`}>
              {ticket.status}
            </span>
          </div>
          <h1 className="text-xl font-bold text-white mt-1">{ticket.subject}</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {new Date(ticket.created_at).toLocaleString()} · {ai.category} · {ticket.metadata?.user_tier}
          </p>
        </div>
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Main: description + response */}
        <div className="lg:col-span-2 space-y-5">
          <div className="card">
            <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
              <MessageSquare size={14} /> Description
            </h3>
            <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{ticket.description}</p>
          </div>

          {/* Attachments — only if ticket has images */}
          {ticket.images && ticket.images.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
                📎 Attachments ({ticket.images.length})
              </h3>
              <div className="flex flex-wrap gap-3">
                {ticket.images.map((img, i) => {
                  const src = (process.env.REACT_APP_API_URL || "http://localhost:8000") + img.url;
                  return (
                    <a
                      key={i}
                      href={src}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block rounded-xl overflow-hidden border border-surface-border hover:border-brand-500/50 transition-colors"
                      style={{ width: "120px" }}
                    >
                      <img
                        src={src}
                        alt={img.original_name}
                        style={{ width: "100%", height: "90px", objectFit: "cover" }}
                        loading="lazy"
                      />
                      <div className="p-1.5">
                        <p className="text-xs text-gray-300 truncate">{img.original_name}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(img.uploaded_at).toLocaleString()}
                        </p>
                      </div>
                    </a>
                  );
                })}
              </div>
            </div>
          )}

          {/* AI Response / Edit area */}
          {ai.generated_response && (
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                  <Brain size={14} className="text-brand-400" /> AI Response
                </h3>
                {isAgent && ticket.status !== "resolved" && (
                  <button onClick={() => setEditing(!editing)} className="btn-ghost btn-sm">
                    <Edit3 size={12} /> {editing ? "Cancel" : "Edit"}
                  </button>
                )}
              </div>

              {editing ? (
                <textarea
                  className="textarea"
                  rows={6}
                  value={editedRes}
                  onChange={(e) => setEditedRes(e.target.value)}
                />
              ) : (
                <div className="bg-surface rounded-xl p-4 border border-surface-border">
                  <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{ai.generated_response}</p>
                </div>
              )}
              {ai.fallback_used && (
                <p className="text-xs text-amber-400 mt-2">⚠ From knowledge base (LLM fallback)</p>
              )}
            </div>
          )}

          {/* LIME Explanation */}
          {lime && (
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
                <Activity size={14} className="text-accent-400" /> AI Explanation (LIME)
              </h3>
              <p className="text-xs text-gray-500 mb-3">
                Words that contributed most to the <strong className="text-white">{lime.predicted_class}</strong> classification:
              </p>
              <div className="space-y-2">
                {(lime.top_positive_features || []).map((f) => (
                  <div key={f.word} className="flex items-center gap-2.5">
                    <span className="text-xs font-mono w-24 truncate text-emerald-400">{f.word}</span>
                    <div className="flex-1 h-1.5 rounded-full bg-surface-border overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full"
                           style={{ width: `${Math.min(Math.abs(f.weight) * 500, 100)}%` }} />
                    </div>
                    <span className="text-xs text-gray-500 w-12 text-right">{f.weight.toFixed(3)}</span>
                  </div>
                ))}
                {(lime.top_negative_features || []).map((f) => (
                  <div key={f.word} className="flex items-center gap-2.5">
                    <span className="text-xs font-mono w-24 truncate text-red-400">{f.word}</span>
                    <div className="flex-1 h-1.5 rounded-full bg-surface-border overflow-hidden">
                      <div className="h-full bg-red-500 rounded-full"
                           style={{ width: `${Math.min(Math.abs(f.weight) * 500, 100)}%` }} />
                    </div>
                    <span className="text-xs text-gray-500 w-12 text-right">{f.weight.toFixed(3)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Similar tickets */}
          {similar.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">Similar Resolved Tickets</h3>
              <div className="space-y-2">
                {similar.slice(0, 3).map((t, i) => (
                  <div key={i} className="p-3 rounded-xl bg-surface border border-surface-border text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-xs text-brand-400">{t.ticket_id}</span>
                      <span className="text-xs text-gray-500">{Math.round(t.similarity_score * 100)}% similar</span>
                    </div>
                    <p className="text-gray-400 text-xs leading-relaxed truncate">{t.solution}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar: AI metrics */}
        <div className="space-y-4">
          <div className="card space-y-4">
            <h3 className="text-sm font-semibold text-gray-300">AI Metrics</h3>

            <div>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Model Confidence</span>
                <span>{Math.round((ai.model_confidence || 0) * 100)}%</span>
              </div>
              <ConfidenceBar score={ai.model_confidence} showLabel={false} />
            </div>

            <div>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Composite Score</span>
                <span>{Math.round((ai.confidence_score || 0) * 100)}%</span>
              </div>
              <ConfidenceBar score={ai.confidence_score} showLabel={false} />
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-gray-500">Category</span>
                <p className="font-semibold text-white mt-0.5">{ai.category || "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">Sentiment</span>
                <p className="font-semibold text-white mt-0.5 capitalize">{ai.sentiment_label || "—"}</p>
              </div>
              <div>
                <span className="text-gray-500">SLA Risk</span>
                <p className="font-semibold text-white mt-0.5">
                  {ai.sla_breach_probability ? `${Math.round(ai.sla_breach_probability * 100)}%` : "—"}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Processing</span>
                <p className="font-semibold text-white mt-0.5">{ai.processing_time_ms ? `${ai.processing_time_ms}ms` : "—"}</p>
              </div>
            </div>

            {ai.security_override && (
              <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/10 rounded-lg p-2">
                <Shield size={12} /> Security override applied
              </div>
            )}
            {ai.sla_override && (
              <div className="flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 rounded-lg p-2">
                <Clock size={12} /> SLA breach override
              </div>
            )}
          </div>

          {/* Agent action buttons */}
          {isAgent && ticket.status !== "resolved" && (
            <div className="card space-y-2">
              <h3 className="text-sm font-semibold text-gray-300 mb-1">Agent Actions</h3>
              <button
                className="btn-primary w-full justify-center"
                disabled={acting}
                onClick={() => doAction("approve")}
              >
                <CheckCircle2 size={14} /> Approve & Resolve
              </button>
              {editing && (
                <button
                  className="btn-secondary w-full justify-center"
                  disabled={acting}
                  onClick={() => doAction("edit")}
                >
                  <Edit3 size={14} /> Save Edited Response
                </button>
              )}
              <button
                className="btn-danger w-full justify-center"
                disabled={acting}
                onClick={() => doAction("reject", { reason: "Manual resolution required" })}
              >
                <XCircle size={14} /> Reject AI Response
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
