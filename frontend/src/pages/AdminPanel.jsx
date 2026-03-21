/**
 * pages/AdminPanel.jsx — Admin: model versions, retraining, system health, KB management.
 */
import React, { useEffect, useState } from "react";
import { adminAPI } from "../services/api";
import Loader, { EmptyState } from "../components/ui/Loader";
import toast from "react-hot-toast";
import {
  RefreshCw, Server, Database, Zap, CheckCircle2,
  XCircle, BookOpen, Settings, AlertTriangle, Brain,
} from "lucide-react";

function HealthDot({ status }) {
  const ok = status === "ok";
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full
      ${ok ? "bg-emerald-500/15 text-emerald-400" : "bg-red-500/15 text-red-400"}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${ok ? "bg-emerald-400" : "bg-red-400"} animate-pulse`} />
      {ok ? "Online" : status}
    </span>
  );
}

export default function AdminPanel() {
  const [versions, setVersions]   = useState([]);
  const [health,   setHealth]     = useState(null);
  const [kb,       setKb]         = useState([]);
  const [loading,  setLoading]    = useState(true);
  const [retraining, setRetraining] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([
      adminAPI.modelVersions(),
      adminAPI.systemHealth(),
      adminAPI.knowledgeBase({ page_size: 10 }),
    ]).then(([v, h, k]) => {
      setVersions(v.data.versions || []);
      setHealth(h.data);
      setKb(k.data.articles || []);
    }).catch(() => {}).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleRetrain = async () => {
    setRetraining(true);
    try {
      await adminAPI.triggerRetrain();
      toast.success("Retraining started in background. You'll be notified when complete.");
    } catch (e) {
      toast.error("Failed to trigger retraining");
    } finally {
      setRetraining(false);
    }
  };

  if (loading) return <Loader text="Loading admin panel…" />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Admin Panel</h1>
          <p className="page-subtitle">System management and model control</p>
        </div>
        <button onClick={load} className="btn-secondary btn-sm"><RefreshCw size={14} /> Refresh</button>
      </div>

      {/* System health */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Server size={14} /> System Health
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {health && Object.entries(health)
            .filter(([k]) => !["chromadb_stats"].includes(k))
            .map(([key, val]) => (
              <div key={key} className="flex items-center justify-between p-3 rounded-xl bg-surface border border-surface-border">
                <div className="flex items-center gap-2">
                  {key === "mongodb"  && <Database size={14} className="text-emerald-400" />}
                  {key === "chromadb" && <Brain size={14} className="text-brand-400" />}
                  {key === "ollama"   && <Zap size={14} className="text-accent-400" />}
                  {key === "api"      && <Server size={14} className="text-gray-400" />}
                  <span className="text-xs text-gray-400 capitalize">{key}</span>
                </div>
                <HealthDot status={val} />
              </div>
            ))
          }
        </div>

        {health?.chromadb_stats && (
          <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
            {Object.entries(health.chromadb_stats).map(([k, v]) => (
              <div key={k} className="flex justify-between px-3 py-2 rounded-lg bg-surface border border-surface-border">
                <span className="text-gray-500 capitalize">{k.replace(/_/g, " ")}</span>
                <span className="text-white font-semibold">{v}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Retraining control */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Settings size={14} /> Model Retraining
        </h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-300">Trigger model retraining with collected feedback data.</p>
            <p className="text-xs text-gray-500 mt-0.5">New model is only promoted if F1 improves by ≥ 2%.</p>
          </div>
          <button
            onClick={handleRetrain}
            disabled={retraining}
            className="btn-primary ml-6 shrink-0"
          >
            {retraining
              ? <><span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Retraining…</>
              : <><RefreshCw size={14} /> Retrain Now</>
            }
          </button>
        </div>
      </div>

      {/* Model versions */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <Brain size={14} /> Model Versions
        </h3>
        {versions.length === 0 ? (
          <EmptyState icon={Brain} title="No models trained yet" subtitle="Run the training pipeline first." />
        ) : (
          <div className="table-wrapper -m-0 overflow-hidden rounded-xl">
            <table className="table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Trained At</th>
                  <th>Category F1</th>
                  <th>Priority F1</th>
                  <th>SLA AUC</th>
                  <th>Feedback Used</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {versions.map((v) => (
                  <tr key={v.version}>
                    <td className="font-mono text-xs text-brand-400">{v.version}</td>
                    <td className="text-xs text-gray-400">
                      {v.trained_at ? new Date(v.trained_at).toLocaleDateString() : "—"}
                    </td>
                    <td className="font-semibold">{v.category_f1 ? `${Math.round(v.category_f1 * 100)}%` : "—"}</td>
                    <td className="font-semibold">{v.priority_f1 ? `${Math.round(v.priority_f1 * 100)}%` : "—"}</td>
                    <td className="font-semibold">{v.sla_auc ? `${Math.round(v.sla_auc * 100)}%` : "—"}</td>
                    <td className="text-gray-400">{v.feedback_examples_added || 0}</td>
                    <td>
                      {v.is_active
                        ? <span className="badge badge-auto">Active</span>
                        : <span className="badge bg-surface-hover text-gray-400 border-surface-border">Superseded</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Knowledge base preview */}
      <div className="card">
        <h3 className="text-sm font-semibold text-gray-300 mb-4 flex items-center gap-2">
          <BookOpen size={14} /> Knowledge Base (Top 10 by Usage)
        </h3>
        {kb.length === 0 ? (
          <EmptyState icon={BookOpen} title="No articles yet" subtitle="Articles are generated automatically as tickets are resolved." />
        ) : (
          <div className="space-y-2">
            {kb.map((art) => (
              <div key={art.article_id} className="p-3 rounded-xl bg-surface border border-surface-border">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-mono text-xs text-gray-500">{art.article_id}</span>
                      <span className="badge bg-surface-hover text-gray-400 border-surface-border text-xs">{art.category}</span>
                      <span className="badge bg-surface-hover text-gray-400 border-surface-border text-xs">{art.difficulty}</span>
                    </div>
                    <p className="text-sm font-medium text-gray-200">{art.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{art.problem_description}</p>
                  </div>
                  <span className="text-xs text-gray-500 shrink-0">×{art.usage_count}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
