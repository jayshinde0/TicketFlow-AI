/**
 * App.jsx — Root router with protected routes and layout.
 */

import React, { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./contexts/AuthContext";
import Layout from "./components/Layout";
import Loader from "./components/ui/Loader";

// Lazy-loaded pages for code splitting
const Login       = lazy(() => import("./pages/Login"));
const Register    = lazy(() => import("./pages/Register"));
const Dashboard   = lazy(() => import("./pages/Dashboard"));
const SubmitTicket= lazy(() => import("./pages/SubmitTicket"));
const TicketDetail= lazy(() => import("./pages/TicketDetail"));
const AgentQueue  = lazy(() => import("./pages/AgentQueue"));
const Analytics   = lazy(() => import("./pages/Analytics"));
const KnowledgeBase= lazy(() => import("./pages/KnowledgeBase"));
const AdminPanel  = lazy(() => import("./pages/AdminPanel"));
const MyTickets   = lazy(() => import("./pages/MyTickets"));

// Route guards
function PrivateRoute({ children, roles }) {
  const { user, loading } = useAuth();

  if (loading) return <Loader fullscreen />;
  if (!user)   return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;

  return children;
}

function PublicRoute({ children }) {
  const { user } = useAuth();
  if (user) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<Loader fullscreen />}>
        <Routes>

          {/* Public routes */}
          <Route path="/login"    element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

          {/* Protected routes inside Layout */}
          <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard"    element={<Dashboard />} />
            <Route path="submit"       element={<SubmitTicket />} />
            <Route path="tickets/:id"  element={<TicketDetail />} />
            <Route path="my-tickets"   element={<MyTickets />} />

            {/* Agent-only */}
            <Route path="queue"        element={
              <PrivateRoute roles={["agent","admin","senior_engineer"]}>
                <AgentQueue />
              </PrivateRoute>
            } />

            {/* Admin-only */}
            <Route path="analytics"    element={
              <PrivateRoute roles={["admin","agent","senior_engineer"]}>
                <Analytics />
              </PrivateRoute>
            } />
            <Route path="knowledge"    element={
              <PrivateRoute roles={["admin","agent","senior_engineer"]}>
                <KnowledgeBase />
              </PrivateRoute>
            } />
            <Route path="admin"        element={
              <PrivateRoute roles={["admin"]}>
                <AdminPanel />
              </PrivateRoute>
            } />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
