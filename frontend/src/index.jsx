import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import { AuthProvider } from "./contexts/AuthContext";
import { NotificationProvider } from "./contexts/NotificationContext";
import { Toaster } from "react-hot-toast";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <AuthProvider>
      <NotificationProvider>
        <App />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: "#1a1d27",
              color: "#f3f4f6",
              border: "1px solid #2a2d3a",
              borderRadius: "12px",
              fontSize: "14px",
            },
            success: { iconTheme: { primary: "#10b981", secondary: "#1a1d27" } },
            error:   { iconTheme: { primary: "#ef4444", secondary: "#1a1d27" } },
          }}
        />
      </NotificationProvider>
    </AuthProvider>
  </React.StrictMode>
);
