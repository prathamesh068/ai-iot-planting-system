import { useState, useEffect, useCallback } from 'react';
import { getSupabaseClient } from '../lib/supabase';
import type { PlantRow, ProcessedData } from '../types';

const REFRESH_MS = 60_000;

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

function parseRows(cycles: PlantCycleRow[]): ProcessedData {
  const labels: string[] = [];
  const temps: (number | null)[] = [];
  const hums: (number | null)[] = [];
  const soilSeries: number[] = [];
  const wetnessSeries: (number | null)[] = [];
  const light: Record<string, number> = { DARK: 0, BRIGHT: 0 };
  const soil: Record<string, number> = { DRY: 0, WET: 0 };
  const actions: Record<string, number> = { None: 0, 'Fan ON': 0, Watered: 0 };
  const diseases: Record<string, number> = {};
  const rows: PlantRow[] = [];
  let latestPrompt: string | null = null;
  let latestResponse: string | null = null;

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
    const action = actuator?.actions ?? 'None';
    const plant = ai?.plant ?? 'None';
    const prompt = ai?.prompt_markdown ?? null;
    const response = ai?.response_markdown ?? null;

    if (prompt) latestPrompt = prompt;
    if (response) latestResponse = response;

    labels.push(time);
    temps.push(temp);
    hums.push(hum);
    soilSeries.push(soilState === 'WET' ? 1 : 0);
    wetnessSeries.push(sensor?.soil_wetness_pct ?? null);

    if (lightState) light[lightState] = (light[lightState] ?? 0) + 1;
    if (soilState) soil[soilState] = (soil[soilState] ?? 0) + 1;
    actions[action] = (actions[action] ?? 0) + 1;
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
            ai_analyses(disease, plant, confidence, prompt_markdown, response_markdown),
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

  useEffect(() => {
    void fetchData();
    const interval = setInterval(() => void fetchData(), REFRESH_MS);
    return () => clearInterval(interval);
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}
