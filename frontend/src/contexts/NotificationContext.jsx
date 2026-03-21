/**
 * contexts/NotificationContext.jsx — Real-time WebSocket notifications.
 * Connects to backend /ws/agent or /ws/admin room based on user role.
 */

import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from "react";
import { io } from "socket.io-client";
import toast from "react-hot-toast";
import { useAuth } from "./AuthContext";

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const { user } = useAuth();
  const wsRef = useRef(null);
  const [liveTickets, setLiveTickets]   = useState([]);
  const [slaWarnings,  setSlaWarnings]  = useState([]);
  const [alerts,       setAlerts]       = useState([]);
  const [connected,    setConnected]    = useState(false);

  const connect = useCallback(() => {
    if (!user || wsRef.current) return;

    const room  = user.role === "admin" ? "admin" : "agent";
    const token = localStorage.getItem("token");
    const WS_URL = process.env.REACT_APP_WS_URL || "ws://localhost:8000";

    // Use native WebSocket (FastAPI WebSocket endpoint)
    const ws = new WebSocket(`${WS_URL}/ws/${room}?token=${token}`);

    ws.onopen = () => {
      setConnected(true);
      // Send keep-alive ping every 25s
      wsRef.current._pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: "ping" }));
        }
      }, 25000);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        handleMessage(msg);
      } catch (_) {}
    };

    ws.onclose = () => {
      setConnected(false);
      clearInterval(wsRef.current?._pingInterval);
      wsRef.current = null;
      // Reconnect after 5s
      setTimeout(connect, 5000);
    };

    ws.onerror = () => ws.close();

    wsRef.current = ws;
  }, [user]);

  const handleMessage = (msg) => {
    switch (msg.type) {
      case "new_ticket":
        setLiveTickets((prev) => [msg, ...prev].slice(0, 50));
        toast(`New ticket: ${msg.subject || msg.ticket_id}`, { icon: "🎫" });
        break;
      case "sla_warning":
        setSlaWarnings((prev) => [msg, ...prev].slice(0, 20));
        toast.error(`SLA Warning: Ticket ${msg.ticket_id} — ${msg.minutes_left}min left`);
        break;
      case "root_cause_alert":
        setAlerts((prev) => [msg, ...prev].slice(0, 20));
        toast(`Incident Spike: ${msg.category} (${msg.ticket_count} tickets)`, { icon: "⚠️" });
        break;
      case "retraining_complete":
        toast.success(`Model retrained: F1 ${msg.old_f1} → ${msg.new_f1} (${msg.promoted ? "promoted" : "rejected"})`);
        break;
      default:
        break;
    }
  };

  useEffect(() => {
    if (user && ["agent", "admin", "senior_engineer"].includes(user.role)) {
      connect();
    }
    return () => {
      if (wsRef.current) {
        clearInterval(wsRef.current._pingInterval);
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [user, connect]);

  return (
    <NotificationContext.Provider value={{ liveTickets, slaWarnings, alerts, connected }}>
      {children}
    </NotificationContext.Provider>
  );
}

export const useNotifications = () => useContext(NotificationContext);
