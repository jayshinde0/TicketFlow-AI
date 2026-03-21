/**
 * pages/KnowledgeBase.jsx — Browse auto-generated knowledge base articles.
 */
import React, { useEffect, useState } from "react";
import { adminAPI } from "../services/api";
import Loader, { EmptyState } from "../components/ui/Loader";
import { BookOpen, Search, ChevronDown, ChevronUp } from "lucide-react";

const CATEGORIES = ["All","Network","Auth","Software","Hardware","Access","Billing","Email","Security","ServiceRequest","Database"];

export default function KnowledgeBase() {
  const [articles, setArticles] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [query,    setQuery]    = useState("");
  const [cat,      setCat]      = useState("All");
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    adminAPI.knowledgeBase({ page_size: 50 })
      .then((r) => { setArticles(r.data.articles || []); setFiltered(r.data.articles || []); })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    let results = articles;
    if (cat !== "All") results = results.filter((a) => a.category === cat);
    if (query) results = results.filter(
      (a) => a.title.toLowerCase().includes(query.toLowerCase()) ||
             a.problem_description?.toLowerCase().includes(query.toLowerCase())
    );
    setFiltered(results);
  }, [query, cat, articles]);

  if (loading) return <Loader text="Loading knowledge base…" />;

  return (
    <div className="space-y-5 animate-fade-in">
      <div>
        <h1 className="page-title">Knowledge Base</h1>
        <p className="page-subtitle">{articles.length} auto-generated articles from resolved tickets</p>
      </div>

      {/* Search + filter */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search size={15} className="absolute left-3 top-3.5 text-gray-500" />
          <input
            className="input pl-9"
            placeholder="Search articles…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setCat(c)}
              className={`text-xs px-3 py-2 rounded-xl border transition-colors ${
                cat === c
                  ? "bg-brand-600 border-brand-500 text-white"
                  : "bg-surface-hover border-surface-border text-gray-400 hover:text-white"
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="card">
          <EmptyState icon={BookOpen} title="No articles found" subtitle="Articles appear automatically after tickets are resolved." />
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((art) => (
            <div key={art.article_id} className="card-hover cursor-pointer"
                 onClick={() => setExpanded(expanded === art.article_id ? null : art.article_id)}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1 flex-wrap">
                    <span className="font-mono text-xs text-gray-500">{art.article_id}</span>
                    <span className="badge bg-brand-600/15 text-brand-300 border-brand-600/25">{art.category}</span>
                    <span className="badge bg-surface text-gray-400 border-surface-border">{art.difficulty}</span>
                    <span className="badge bg-surface text-gray-400 border-surface-border">
                      ×{art.usage_count} used
                    </span>
                  </div>
                  <p className="font-semibold text-white text-sm">{art.title}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{art.problem_description}</p>
                </div>
                <div className="text-gray-500 shrink-0">
                  {expanded === art.article_id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </div>

              {expanded === art.article_id && (
                <div className="mt-4 pt-4 border-t border-surface-border space-y-3 text-sm">
                  {art.likely_cause && (
                    <div>
                      <p className="text-xs font-semibold text-gray-400 mb-1">Likely Cause</p>
                      <p className="text-gray-300">{art.likely_cause}</p>
                    </div>
                  )}
                  {art.solution_steps?.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-400 mb-1">Solution Steps</p>
                      <ol className="space-y-1.5">
                        {art.solution_steps.map((s, i) => (
                          <li key={i} className="flex gap-2 text-gray-300">
                            <span className="text-brand-400 font-bold shrink-0">{i+1}.</span>
                            <span>{s}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                  {art.prevention && (
                    <div>
                      <p className="text-xs font-semibold text-gray-400 mb-1">Prevention</p>
                      <p className="text-gray-300">{art.prevention}</p>
                    </div>
                  )}
                  {art.tags?.length > 0 && (
                    <div className="flex gap-1.5 flex-wrap">
                      {art.tags.map((t) => (
                        <span key={t} className="badge bg-surface text-gray-500 border-surface-border text-xs">#{t}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
