/**
 * components/Layout/Sidebar.jsx — Navigation sidebar.
 */

import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useNotifications } from "../contexts/NotificationContext";
import {
  LayoutDashboard, Ticket, ListTodo, BarChart2,
  BookOpen, Settings, LogOut, Zap, Wifi, WifiOff,
  PlusCircle, Users,
} from "lucide-react";
import clsx from "clsx";

const NavItem = ({ to, icon: Icon, label, badge }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      clsx(isActive ? "nav-item-active" : "nav-item", "group")
    }
  >
    <Icon size={18} />
    <span className="flex-1">{label}</span>
    {badge > 0 && (
      <span className="ml-auto text-xs bg-brand-600 text-white rounded-full w-5 h-5
                       flex items-center justify-center font-bold">
        {badge > 99 ? "99+" : badge}
      </span>
    )}
  </NavLink>
);

export default function Sidebar({ onClose }) {
  const { user, logout, isAdmin, isAgent } = useAuth();
  const { connected, liveTickets } = useNotifications();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
    onClose?.();
  };

  return (
    <div className="flex flex-col h-full bg-surface-card border-r border-surface-border">

      {/* Logo */}
      <div className="p-6 border-b border-surface-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-brand flex items-center justify-center shadow-glow-sm">
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-none">TicketFlow</div>
            <div className="text-xs text-brand-400 mt-0.5">AI Platform</div>
          </div>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">

        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-2">
          General
        </p>
        <NavItem to="/dashboard"   icon={LayoutDashboard} label="Dashboard" />
        <NavItem to="/submit"      icon={PlusCircle}       label="Submit Ticket" />
        <NavItem to="/my-tickets"  icon={Ticket}           label="My Tickets" />

        {isAgent && (
          <>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-2 mt-4">
              Agent Tools
            </p>
            <NavItem to="/queue"     icon={ListTodo}  label="Agent Queue" badge={liveTickets.length} />
            <NavItem to="/analytics" icon={BarChart2} label="Analytics" />
            <NavItem to="/knowledge" icon={BookOpen}  label="Knowledge Base" />
          </>
        )}

        {isAdmin && (
          <>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider px-3 mb-2 mt-4">
              Admin
            </p>
            <NavItem to="/admin" icon={Settings} label="Admin Panel" />
          </>
        )}
      </nav>

      {/* User + WS status */}
      <div className="p-4 border-t border-surface-border space-y-3">
        {/* WebSocket indicator */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-surface text-xs">
          {connected
            ? <><Wifi  size={12} className="text-emerald-400" /><span className="text-emerald-400">Live</span></>
            : <><WifiOff size={12} className="text-gray-500"  /><span className="text-gray-500">Offline</span></>
          }
        </div>

        {/* User info */}
        <div className="flex items-center gap-3 px-3">
          <div className="w-8 h-8 rounded-full bg-brand-600/20 border border-brand-600/40
                          flex items-center justify-center text-xs font-bold text-brand-300">
            {user?.name?.charAt(0)?.toUpperCase() || "?"}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-white truncate">{user?.name}</div>
            <div className="text-xs text-gray-500 capitalize">{user?.role}</div>
          </div>
          <button onClick={handleLogout} className="text-gray-500 hover:text-red-400 transition-colors" title="Logout">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
