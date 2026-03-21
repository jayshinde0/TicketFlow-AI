/**
 * useWebSocket.js - Custom hook for WebSocket real-time updates
 * Connects to backend WebSocket for live ticket updates, alerts, and notifications
 */

import { useEffect, useRef, useState } from 'react';
import { toast } from 'react-hot-toast';

const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/dashboard';

export const useWebSocket = (userId) => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!userId) return;

    let ws = null;
    let reconnectTimeout = null;
    let reconnectAttempts = 0;
    let isMounted = true;

    const connect = () => {
      try {
        ws = new WebSocket(`${WS_URL}?user_id=${userId}`);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          
          console.log('✅ WebSocket connected');
          setIsConnected(true);
          reconnectAttempts = 0;
          
          // Send initial connection message
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
              type: 'connect',
              user_id: userId,
              timestamp: new Date().toISOString()
            }));
          }
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          
          try {
            const data = JSON.parse(event.data);
            console.log('📨 WebSocket message:', data);
            
            setLastMessage(data);
            setMessages(prev => [...prev.slice(-99), data]); // Keep last 100 messages

            // Handle different message types
            handleMessage(data);
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onerror = (error) => {
          if (!isMounted) return;
          
          console.error('❌ WebSocket error:', error);
          setIsConnected(false);
        };

        ws.onclose = () => {
          if (!isMounted) return;
          
          console.log('🔌 WebSocket disconnected');
          setIsConnected(false);
          wsRef.current = null;
          
          // Attempt to reconnect with exponential backoff
          if (reconnectAttempts < 10) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            console.log(`🔄 Reconnecting in ${delay}ms...`);
            
            reconnectTimeout = setTimeout(() => {
              reconnectAttempts += 1;
              connect();
            }, delay);
          }
        };
      } catch (error) {
        console.error('Failed to create WebSocket connection:', error);
      }
    };

    connect();

    // Cleanup on unmount
    return () => {
      isMounted = false;
      
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      
      if (ws && ws.readyState !== WebSocket.CLOSED) {
        ws.close();
      }
      
      wsRef.current = null;
    };
  }, [userId]);

  const handleMessage = (data) => {
    const { type, message, severity } = data;

    switch (type) {
      case 'ticket_update':
        toast.success(`Ticket ${data.ticket_id} updated`, { duration: 3000 });
        break;
      
      case 'new_ticket':
        toast(`New ticket: ${data.ticket_id}`, { 
          icon: '🎫',
          duration: 4000 
        });
        break;
      
      case 'root_cause_alert':
        toast.error(`🚨 Root Cause Alert: ${data.category} - ${data.ticket_count} tickets`, {
          duration: 8000
        });
        break;
      
      case 'sla_warning':
        toast(`⏰ SLA Warning: ${data.ticket_id} - ${data.minutes_left}min left`, {
          icon: '⚠️',
          duration: 6000
        });
        break;
      
      case 'sla_breach':
        toast.error(`🔴 SLA BREACH: ${data.ticket_id}`, { duration: 10000 });
        break;
      
      case 'retraining_complete':
        toast.success(`✨ Model retrained! New F1: ${data.f1_score?.toFixed(3)}`, {
          duration: 5000
        });
        break;
      
      case 'notification':
        if (severity === 'error') {
          toast.error(message);
        } else if (severity === 'warning') {
          toast(message, { icon: '⚠️' });
        } else {
          toast.success(message);
        }
        break;
      
      default:
        console.log('Unhandled message type:', type);
    }
  };

  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  };

  return {
    isConnected,
    messages,
    lastMessage,
    sendMessage
  };
};
