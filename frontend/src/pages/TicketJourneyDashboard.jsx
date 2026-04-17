/**
 * pages/TicketJourneyDashboard.jsx — User dashboard showing all ticket journeys
 */
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { journeyAPI } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import JourneyBadge from "../components/ticket/JourneyBadge";
import Loader, { EmptyState } from "../components/ui/Loader";
import { 
  ArrowRight, User, Clock, CheckCircle2, 
  AlertCircle, TrendingUp, Ticket, RefreshCw 
} from "lucide-react";

function formatDuration(ms) {
  if (!ms) return "—";
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return `${days}d ${hours % 24}h`;
  if (hours > 0) return `${hours}h ${minutes % 60}m`;
  if (minutes > 0) return `${minutes}m`;
  return `${seconds}s`;
}

function JourneyCard({ journey, onClick }) {
  const currentPhase = journey.phases.find(p => p.phase === journey.current_phase);
  const isResolved = journey.current_phase === "resolved" || journey.current_phase === "closed";
  
  return (
    <div
      className="card-hover cursor-pointer"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="font-mono text-xs text-brand-400">{journey.ticket_id}</span>
            <JourneyBadge 
              phase={journey.current_phase} 
              agentName={journey.assigned_agent?.full_name?.split(' ')[0]}
            />
          </div>
          <p className="text-xs text-gray-500">
            Started {new Date(journey.created_at).toLocaleString()}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500">Duration</p>
          <p className="text-sm font-semibold text-white">
            {formatDuration(journey.total_duration_ms)}
          </p>
        </div>
      </div>

      {/* Assigned Agent */}
      {journey.assigned_agent && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-surface border border-surface-border mb-3">
          <div className="w-8 h-8 rounded-full bg-brand-500/20 flex items-center justify-center">
            <User size={14} className="text-brand-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white truncate">
              {journey.assigned_agent.full_name}
            </p>
            <p className="text-xs text-gray-500">
              {journey.assigned_agent.department}
            </p>
          </div>
        </div>
      )}

      {/* Phase Progress */}
      <div className="flex items-center gap-1">
        {journey.phases.map((phase, index) => {
          const isCurrent = phase.phase === journey.current_phase;
          const isPast = journey.phases.findIndex(p => p.phase === journey.current_phase) > index;
          
          return (
            <div
              key={phase.phase}
              className={`flex-1 h-1.5 rounded-full transition-all ${
                isCurrent ? "bg-brand-500 animate-pulse" :
                isPast ? "bg-emerald-500" :
                "bg-surface-border"
              }`}
              title={phase.phase.replace(/_/g, ' ')}
            />
          );
        })}
      </div>

      {/* Phase count */}
      <p className="text-xs text-gray-500 mt-2">
        Phase {journey.phases.findIndex(p => p.phase === journey.current_phase) + 1} of {journey.phases.length}
      </p>
    </div>
  );
}

export default function TicketJourneyDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [journeys, setJourneys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    resolved: 0,
    avgDuration: 0,
  });

  const loadJourneys = (isRefresh = false) => {
    if (!user?.user_id) return;
    
    if (isRefresh) setRefreshing(true);

    journeyAPI.getByUser(user.user_id)
      .then(res => {
        const data = res.data.journeys || [];
        setJourneys(data);
        setLastUpdated(new Date());
        
        // Calculate stats
        const active = data.filter(j => 
          j.current_phase !== "resolved" && j.current_phase !== "closed"
        ).length;
        const resolved = data.filter(j => 
          j.current_phase === "resolved" || j.current_phase === "closed"
        ).length;
        const avgDuration = data.length > 0
          ? data.reduce((sum, j) => sum + (j.total_duration_ms || 0), 0) / data.length
          : 0;
        
        setStats({
          total: data.length,
          active,
          resolved,
          avgDuration,
        });
      })
      .catch(err => {
        console.error("Failed to load journeys:", err);
      })
      .finally(() => {
        setLoading(false);
        if (isRefresh) setRefreshing(false);
      });
  };

  useEffect(() => {
    loadJourneys();
    
    // Auto-refresh every 10 seconds to show new tickets
    const interval = setInterval(loadJourneys, 10000);
    
    return () => clearInterval(interval);
  }, [user]);

  if (loading) return <Loader text="Loading ticket journeys…" />;

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Ticket Journey Dashboard</h1>
          <p className="page-subtitle">
            Track the progress of all your tickets
            {lastUpdated && (
              <span className="text-gray-600 ml-2">
                · Last updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <button 
          onClick={() => loadJourneys(true)} 
          disabled={refreshing}
          className="btn-secondary"
        >
          <RefreshCw size={15} className={refreshing ? "animate-spin" : ""} />
          {refreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center">
              <Ticket size={18} className="text-brand-400" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Tickets</p>
              <p className="text-2xl font-bold text-white">{stats.total}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center">
              <Clock size={18} className="text-amber-400" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Active</p>
              <p className="text-2xl font-bold text-white">{stats.active}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center">
              <CheckCircle2 size={18} className="text-emerald-400" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Resolved</p>
              <p className="text-2xl font-bold text-white">{stats.resolved}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center">
              <TrendingUp size={18} className="text-purple-400" />
            </div>
            <div>
              <p className="text-xs text-gray-500">Avg Duration</p>
              <p className="text-2xl font-bold text-white">{formatDuration(stats.avgDuration)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Journey List */}
      {journeys.length === 0 ? (
        <div className="card">
          <EmptyState
            icon={ArrowRight}
            title="No ticket journeys yet"
            subtitle="Submit a ticket to start tracking its journey through our system."
            action={
              <button onClick={() => navigate("/submit")} className="btn-primary">
                Submit Ticket
              </button>
            }
          />
        </div>
      ) : (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">All Journeys</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {journeys.map(journey => (
              <JourneyCard
                key={journey.journey_id}
                journey={journey}
                onClick={() => navigate(`/tickets/${journey.ticket_id}`)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
