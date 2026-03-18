import { useState, useEffect } from 'react';
import { subscribeToHeartbeat, type HeartbeatPayload } from './useSupabaseData';

const HEARTBEAT_CHECK_INTERVAL_MS = 1000;
const HEARTBEAT_STALE_THRESHOLD_MS = 35_000;

export interface ConnectionState {
  isLive: boolean;
  lastHeartbeat: Date | null;
  secondsSinceHeartbeat: number;
  isDeviceRunning: boolean;
}

export function useDeviceHeartbeat(): ConnectionState {
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);
  const [isDeviceRunning, setIsDeviceRunning] = useState(false);
  const [secondsSinceHeartbeat, setSecondsSinceHeartbeat] = useState(0);

  useEffect(() => {
    const subscription = subscribeToHeartbeat(
      (payload: HeartbeatPayload) => {
        setLastHeartbeat(new Date(payload.timestamp));
        setSecondsSinceHeartbeat(0);
        setIsDeviceRunning(payload.is_running ?? false);
      },
      () => {
        setIsDeviceRunning(false);
      },
    );

    return () => {
      void subscription.unsubscribe();
    };
  // subscribeToHeartbeat is a stable module-level function — no dep needed
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!lastHeartbeat) {
      setSecondsSinceHeartbeat(0);
      return;
    }

    const updateElapsedSeconds = () => {
      const now = new Date();
      const seconds = Math.floor((now.getTime() - lastHeartbeat.getTime()) / 1000);
      setSecondsSinceHeartbeat(Math.max(0, seconds));
    };

    updateElapsedSeconds();
    const timer = window.setInterval(updateElapsedSeconds, HEARTBEAT_CHECK_INTERVAL_MS);

    return () => {
      window.clearInterval(timer);
    };
  }, [lastHeartbeat]);

  const isLive = lastHeartbeat !== null && secondsSinceHeartbeat < HEARTBEAT_STALE_THRESHOLD_MS / 1000;

  return {
    isLive,
    lastHeartbeat,
    secondsSinceHeartbeat,
    isDeviceRunning,
  };
}
