import { useState, useEffect, useRef, useCallback } from "react";

/**
 * React hook untuk real-time sensor data streaming via WebSocket.
 * 
 * Usage:
 *   const { data, isConnected, error } = useDeviceStream(deviceId);
 *   // data = { temperature, humidity, ammonia, is_alert, timestamp, ... }
 * 
 * WebSocket URL: ws://host/api/ws/devices/{deviceId}?token=JWT
 */
export function useDeviceStream(deviceId) {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (!deviceId) return;

    const token = localStorage.getItem("access_token");
    if (!token) {
      setError("Tidak ada token autentikasi");
      return;
    }

    // Determine WebSocket URL
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;

    // Di development (Vite proxy), gunakan backend langsung
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "";
    let wsUrl;

    if (apiBaseUrl && apiBaseUrl.startsWith("http")) {
      // Development: http://localhost:8001/api → ws://localhost:8001/api/ws/...
      const backendUrl = apiBaseUrl.replace(/^http/, "ws");
      wsUrl = `${backendUrl}/ws/devices/${deviceId}?token=${token}`;
    } else {
      // Production: same origin
      wsUrl = `${protocol}//${host}/api/ws/devices/${deviceId}?token=${token}`;
    }

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          if (parsed.type === "sensor_data") {
            setData(parsed);
          }
        } catch {
          // Ignore non-JSON messages
        }
      };

      ws.onerror = () => {
        setError("Koneksi WebSocket gagal");
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        wsRef.current = null;

        // Auto-reconnect setelah 5 detik (kecuali ditutup sengaja)
        if (event.code !== 1000 && event.code !== 4001 && event.code !== 4003) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 5000);
        }
      };
    } catch (err) {
      setError(`WebSocket error: ${err.message}`);
    }
  }, [deviceId]);

  // Connect saat deviceId berubah
  useEffect(() => {
    connect();

    return () => {
      // Cleanup saat unmount
      if (wsRef.current) {
        wsRef.current.close(1000);
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  // Manual disconnect
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000);
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    setIsConnected(false);
  }, []);

  return {
    data,
    isConnected,
    error,
    disconnect,
  };
}
