/**
 * components/Layout/TopBar.jsx — Top navigation bar with breadcrumb + user actions.
 */

import React from "react";
import { useLocation } from "react-router-dom";
import { Menu, Bell } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { useNotifications } from "../contexts/NotificationContext";

const ROUTE_LABELS = {
  "/dashboard":  "Dashboard",
  "/submit":     "Submit Ticket",
  "/my-tickets": "My Tickets",
  "/queue":      "Agent Queue",
  "/analytics":  "Analytics",
  "/knowledge":  "Knowledge Base",
  "/admin":      "Admin Panel",
};

export default function TopBar({ onMenuClick }) {
  const { pathname } = useLocation();
  const { user }     = useAuth();
  const { alerts, slaWarnings } = useNotifications();

  const label = ROUTE_LABELS[pathname] || "TicketFlow AI";
  const alertCount = alerts.filter((a) => a.status === "open").length + slaWarnings.length;

  return (
    <header className="flex items-center justify-between px-6 h-16 border-b border-surface-border
                        bg-surface-card/50 backdrop-blur-sm flex-shrink-0">
      {/* Left: hamburger + page title */}
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded-lg text-gray-400 hover:text-white hover:bg-surface-hover"
        >
          <Menu size={20} />
        </button>
        <div>
          <h1 className="text-base font-semibold text-white">{label}</h1>
          <p className="text-xs text-gray-500">
            {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
          </p>
        </div>
      </div>

      {/* Right: notifications + user */}
      <div className="flex items-center gap-3">
        <button className="relative p-2 rounded-xl text-gray-400 hover:text-white hover:bg-surface-hover
                            transition-colors">
          <Bell size={18} />
          {alertCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-red-500 rounded-full
                              text-[10px] font-bold text-white flex items-center justify-center">
              {alertCount}
            </span>
          )}
        </button>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-hover border border-surface-border">
          <div className="w-6 h-6 rounded-full bg-brand-600/30 border border-brand-600/50
                          flex items-center justify-center text-[11px] font-bold text-brand-300">
            {user?.name?.charAt(0)?.toUpperCase() || "?"}
          </div>
          <span className="text-sm font-medium text-gray-200 hidden sm:block">{user?.name}</span>
        </div>
      </div>
    </header>
  );
}
