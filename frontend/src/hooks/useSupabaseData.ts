import { useState, useEffect, useCallback } from 'react';
import type { RealtimeChannel } from '@supabase/supabase-js';
import { getSupabaseClient } from '../lib/supabase';
import type { PlantRow, ProcessedData, TodoItem } from '../types';

const REFRESH_MS = 60_000;
const CONTROL_CHANNEL = import.meta.env.VITE_SUPABASE_CONTROL_CHANNEL ?? 'plant-control';
const HEARTBEAT_RETRY_INITIAL_MS = 2_000;
const HEARTBEAT_RETRY_MAX_MS = 30_000;
const HEARTBEAT_RETRY_MULTIPLIER = 1.5;

export interface HeartbeatPayload {
  timestamp: string;
  status: string;
  is_running: boolean;
}

interface SensorReading {
  temp_c: number | null;
  humidity_pct: number | null;
  light_state: string | null;
  soil_summary: string | null;
  soil_majority: string | null;
  temp_readings: (number | null)[] | null;
  hum_readings: (number | null)[] | null;
  soil_readings: string[] | null;
  soil_wetness_pct: number | null;
}

interface AIAnalysis {
  disease: string | null;
  plant: string | null;
  confidence: number | null;
  todos: TodoItem[] | null;
  prompt_markdown: string | null;
  response_markdown: string | null;
}

interface ActuatorAction {
  actions: string | null;
}

interface PlantCycleRow {
  id: string;
  captured_at: string | null;
  image_url: string | null;
  sensor_readings: SensorReading[] | SensorReading | null;
  ai_analyses: AIAnalysis[] | AIAnalysis | null;
  actuator_actions: ActuatorAction[] | ActuatorAction | null;
}

function pickOne<T>(value: T[] | T | null | undefined): T | null {
  if (!value) return null;
  return Array.isArray(value) ? value[0] ?? null : value;
}

function normalizeState(value: string | null): string | null {
  if (!value) return null;
  return value.trim().toUpperCase();
}

function normalizeActionToken(value: string | null): string {
  const normalized = (value ?? '').trim().toLowerCase();

  if (!normalized || normalized === 'none' || normalized === 'no action') {
    return 'No Action needed';
  }

  if (normalized.includes('fan on') || normalized.includes('airflow')) {
    return 'Increase Airflow';
  }

  if (normalized.includes('water')) {
    return 'Water the plant';
  }

  return value?.trim() || 'No Action needed';
}

function parseActionLabels(rawAction: string | null | undefined): string[] {
  const raw = (rawAction ?? '').trim();
  if (!raw) {
    return ['No Action needed'];
  }

  const tokens = raw
    .split(',')
    .map((token) => normalizeActionToken(token))
    .filter((token) => Boolean(token));

  if (tokens.length === 0) {
    return ['No Action needed'];
  }

  const unique = Array.from(new Set(tokens));
  if (unique.length > 1) {
    return unique.filter((token) => token !== 'No Action needed');
  }
  return unique;
}

function normalizeTodoPriority(value: unknown): 'HIGH' | 'MEDIUM' | 'LOW' {
  const p = String(value ?? '').trim().toUpperCase();
  if (p === 'HIGH' || p === 'MEDIUM' || p === 'LOW') {
    return p;
  }
  return 'LOW';
}

function parseTodos(value: unknown): TodoItem[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
    .map((item) => {
      const action = String(item.action ?? '').trim();
      const reason = String(item.reason ?? '').trim();
      if (!action) {
        return null;
      }
      return {
        action,
        priority: normalizeTodoPriority(item.priority),
        reason: reason || 'No reason provided.',
      };
    })
    .filter((item): item is TodoItem => item !== null);
}

function parseTodosFromResponse(response: string | null): TodoItem[] {
  if (!response) {
    return [];
  }

  const cleaned = response
    .replace(/^```json\s*/i, '')
    .replace(/^```\s*/i, '')
    .replace(/```\s*$/i, '')
    .trim();

  try {
    const parsed = JSON.parse(cleaned) as { todos?: unknown };
    return parseTodos(parsed.todos ?? []);
  } catch {
    return [];
  }
}

function parseRows(cycles: PlantCycleRow[]): ProcessedData {
  const labels: string[] = [];
  const temps: (number | null)[] = [];
  const hums: (number | null)[] = [];
  const soilSeries: number[] = [];
  const wetnessSeries: (number | null)[] = [];
  const light: Record<string, number> = { DARK: 0, BRIGHT: 0 };
  const soil: Record<string, number> = { DRY: 0, WET: 0 };
  const actions: Record<string, number> = {
    'No Action needed': 0,
    'Increase Airflow': 0,
    'Water the plant': 0,
  };
  const diseases: Record<string, number> = {};
  const rows: PlantRow[] = [];
  let latestPrompt: string | null = null;
  let latestResponse: string | null = null;
  let latestTodos: TodoItem[] = [];

  cycles.forEach((cycle) => {
    const sensor = pickOne(cycle.sensor_readings);
    const ai = pickOne(cycle.ai_analyses);
    const actuator = pickOne(cycle.actuator_actions);

    const time = cycle.captured_at ?? '';
    const temp = sensor?.temp_c ?? null;
    const hum = sensor?.humidity_pct ?? null;
    const lightState = normalizeState(sensor?.light_state ?? null);
    const soilSummary = sensor?.soil_summary ?? null;
    const soilState = normalizeState(sensor?.soil_majority ?? soilSummary);

    const img = cycle.image_url ?? null;
    const disease = ai?.disease ?? null;
    const actionLabels = parseActionLabels(actuator?.actions);
    const action = actionLabels.join(', ');
    const plant = ai?.plant ?? 'None';
    const prompt = ai?.prompt_markdown ?? null;
    const response = ai?.response_markdown ?? null;
    const todos = parseTodos(ai?.todos ?? []);
    const todosFromResponse = todos.length ? todos : parseTodosFromResponse(response);

    if (prompt) latestPrompt = prompt;
    if (response) latestResponse = response;
    if (todosFromResponse.length > 0) latestTodos = todosFromResponse;

    labels.push(time);
    temps.push(temp);
    hums.push(hum);
    soilSeries.push(soilState === 'WET' ? 1 : 0);
    wetnessSeries.push(sensor?.soil_wetness_pct ?? null);

    if (lightState) light[lightState] = (light[lightState] ?? 0) + 1;
    if (soilState) soil[soilState] = (soil[soilState] ?? 0) + 1;
    actionLabels.forEach((label) => {
      actions[label] = (actions[label] ?? 0) + 1;
    });
    if (disease) diseases[disease] = (diseases[disease] ?? 0) + 1;

    rows.push({
      time,
      temp,
      hum,
      tempReadings: sensor?.temp_readings ?? [],
      humReadings: sensor?.hum_readings ?? [],
      soilReadings: sensor?.soil_readings ?? [],
      soilWetnessPct: sensor?.soil_wetness_pct ?? null,
      light: lightState,
      soil: soilState,
      img,
      disease,
      action,
      plant,
      prompt,
      response,
      todos: todosFromResponse,
    });
  });

  return {
    labels,
    temps,
    hums,
    soilSeries,
    wetnessSeries,
    light,
    soil,
    actions,
    diseases,
    rows,
    latestPrompt,
    latestResponse,
    latestTodos,
  };
}



export interface HeartbeatSubscription {
  unsubscribe: () => Promise<void>;
  send: (event: string, payload: Record<string, unknown>) => Promise<void>;
}

// ---------------------------------------------------------------------------
// Singleton heartbeat manager — one Realtime channel shared by all callers.
// ---------------------------------------------------------------------------
type HeartbeatListener = {
  onHeartbeat: (payload: HeartbeatPayload) => void;
  onDisconnect: () => void;
};

let _channel: RealtimeChannel | null = null;
let _retryTimeout: ReturnType<typeof setTimeout> | null = null;
let _isReconnectScheduled = false;
let _retryCount = 0;
let _isStarted = false;
const _listeners = new Set<HeartbeatListener>();

function _calculateBackoffMs(): number {
  const delay = HEARTBEAT_RETRY_INITIAL_MS * Math.pow(HEARTBEAT_RETRY_MULTIPLIER, _retryCount);
  return Math.min(delay, HEARTBEAT_RETRY_MAX_MS);
}

async function _removeChannel(target?: RealtimeChannel | null): Promise<void> {
  const ch = target ?? _channel;
  if (!ch) return;
  if (_channel === ch) _channel = null;
  try {
    await getSupabaseClient().removeChannel(ch);
  } catch {
    // ignore
  }
}

async function _scheduleReconnect(reason: unknown, activeChannel?: RealtimeChannel | null): Promise<void> {
  if (_isReconnectScheduled) return;
  _isReconnectScheduled = true;
  await _removeChannel(activeChannel);
  _listeners.forEach((l) => l.onDisconnect());

  const backoffMs = _calculateBackoffMs();
  _retryCount += 1;
  console.warn(
    `[Heartbeat] Connection lost (retry ${_retryCount}, waiting ${backoffMs}ms):`,
    reason instanceof Error ? reason.message : reason,
  );

  _retryTimeout = window.setTimeout(() => {
    _isReconnectScheduled = false;
    void _startListening();
  }, backoffMs);
}

function _startListening(): void {
  if (_listeners.size === 0) return;

  _isStarted = true;
  const supabase = getSupabaseClient();
  const currentChannel = supabase.channel(CONTROL_CHANNEL, {
    config: { broadcast: { ack: false, self: false } },
  });
  _channel = currentChannel;
  let hasSubscribed = false;

  currentChannel.on('broadcast', { event: 'device_heartbeat' }, (payload: any) => {
    if (_channel !== currentChannel) return;
    const data = payload?.payload as HeartbeatPayload | undefined;
    if (!data) return;
    _retryCount = 0;
    _listeners.forEach((l) => l.onHeartbeat(data));
  });

  currentChannel.subscribe((status, err) => {
    if (_channel !== currentChannel) return;

    if (status === 'SUBSCRIBED') {
      hasSubscribed = true;
      _retryCount = 0;
      console.log('[Heartbeat] Subscribed to device heartbeat channel');
      return;
    }

    if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT' || status === 'CLOSED') {
      const reason = err ?? new Error(`Heartbeat channel failed: ${status}`);
      if (hasSubscribed) {
        console.warn(`[Heartbeat] Channel dropped after subscribe: ${status}`);
      } else {
        console.warn(`[Heartbeat] Initial subscribe failed: ${status}`);
      }
      void _scheduleReconnect(reason, currentChannel);
    }
  });
}

export function subscribeToHeartbeat(
  onHeartbeat: (payload: HeartbeatPayload) => void,
  onDisconnect: () => void,
): HeartbeatSubscription {
  const listener: HeartbeatListener = { onHeartbeat, onDisconnect };
  _listeners.add(listener);

  if (!_isStarted) {
    _startListening();
  }

  return {
    unsubscribe: async () => {
      _listeners.delete(listener);
      if (_listeners.size === 0) {
        _isStarted = false;
        if (_retryTimeout) {
          window.clearTimeout(_retryTimeout);
          _retryTimeout = null;
        }
        _isReconnectScheduled = false;
        _retryCount = 0;
        await _removeChannel();
      }
    },
    send: async (event: string, payload: Record<string, unknown>) => {
      if (!_channel) {
        throw new Error('Heartbeat channel not yet subscribed — cannot send command');
      }
      const sendStatus = await _channel.send({
        type: 'broadcast',
        event,
        payload: {
          source: 'dashboard-ui',
          requested_at: new Date().toISOString(),
          ...payload,
        },
      });
      if (sendStatus !== 'ok') {
        throw new Error(`Broadcast failed with status: ${sendStatus}`);
      }
    },
  };
}

export function useSupabaseData() {
  const [data, setData] = useState<ProcessedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const supabase = getSupabaseClient();
      const { data: rawCycles, error: queryError } = await supabase
        .from('plant_cycles')
        .select(
          `
            id,
            captured_at,
            image_url,
            sensor_readings(temp_c, humidity_pct, light_state, soil_summary, soil_majority, temp_readings, hum_readings, soil_readings, soil_wetness_pct),
            ai_analyses(disease, plant, confidence, todos, prompt_markdown, response_markdown),
            actuator_actions(actions)
          `,
        )
        .order('captured_at', { ascending: false })
        .limit(20);

      if (queryError) {
        throw queryError;
      }

      const ordered = ((rawCycles ?? []) as PlantCycleRow[]).slice().reverse();
      setData(parseRows(ordered));
      setError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to fetch data from Supabase: ${message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // Reuse the singleton channel managed by subscribeToHeartbeat — no new subscription needed.
  const broadcastStartReading = useCallback(async () => {
    if (!_channel) {
      throw new Error('Not connected — heartbeat channel is not subscribed yet');
    }
    const sendStatus = await _channel.send({
      type: 'broadcast',
      event: 'start_reading',
      payload: {
        source: 'dashboard-ui',
        requested_at: new Date().toISOString(),
      },
    });
    if (sendStatus !== 'ok') {
      throw new Error(`Failed to send command: broadcast returned ${sendStatus}`);
    }
  }, []);

  useEffect(() => {
    void fetchData();
    const interval = setInterval(() => void fetchData(), REFRESH_MS);
    return () => clearInterval(interval);
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    broadcastStartReading,
  };
}
