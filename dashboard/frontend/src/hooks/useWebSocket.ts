import { useEffect, useState, useRef } from "react";

export function useWebSocket(guildId: string | null) {
  const [messages, setMessages] = useState<any[]>([]);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!guildId) return;
    
    const token = typeof window !== "undefined" ? localStorage.getItem("dashboard_token") : null;
    if (!token) return;

    // Use wss:// in production, ws:// locally
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host; // Proxy to backend
    
    ws.current = new WebSocket(`${protocol}//${host}/api/v1/ws/${guildId}?token=${token}`);

    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages((prev) => [data, ...prev].slice(0, 100)); // Keep last 100
      } catch (e) {
        if (event.data === "pong") {
           // Heartbeat
        }
      }
    };

    const interval = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send("ping");
      }
    }, 25000); // 25s heartbeat

    return () => {
      clearInterval(interval);
      ws.current?.close();
    };
  }, [guildId]);

  return { messages };
}
