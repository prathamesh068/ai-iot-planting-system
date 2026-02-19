import { useState, useEffect, useCallback } from 'react';
import type { ProcessedData, SheetRow } from '../types';

const SHEET_ID = import.meta.env.VITE_SHEET_ID as string;
const SHEET_NAME = (import.meta.env.VITE_SHEET_NAME as string) || 'plant_readings';
const REFRESH_MS = 60_000;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function parseRows(rawRows: any[]): ProcessedData {
  const labels: string[] = [];
  const temps: (number | null)[] = [];
  const hums: (number | null)[] = [];
  const soilSeries: number[] = [];
  const light: Record<string, number> = { DARK: 0, BRIGHT: 0 };
  const soil: Record<string, number> = { DRY: 0, WET: 0 };
  const actions: Record<string, number> = { None: 0, 'Fan ON': 0, Watered: 0 };
  const diseases: Record<string, number> = {};
  const rows: SheetRow[] = [];
  let latestPrompt: string | null = null;
  let latestResponse: string | null = null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  rawRows.forEach((r: any) => {
    const time: string = r.c[0]?.v ?? '';
    const temp: number | null = r.c[1]?.v ?? null;
    const hum: number | null = r.c[2]?.v ?? null;
    const l: string | null = r.c[3]?.v ?? null;
    const s: string | null = r.c[4]?.v ?? null;
    const img: string | null = r.c[5]?.v ?? null;
    const dis: string | null = r.c[6]?.v ?? null;
    const act: string = r.c[8]?.v ?? 'None';
    const plant: string = r.c[9]?.v ?? 'None';
    const prompt: string | null = r.c[10]?.v ?? null;
    const resp: string | null = r.c[11]?.v ?? null;

    if (prompt) latestPrompt = prompt;
    if (resp) latestResponse = resp;

    labels.push(time);
    temps.push(temp);
    hums.push(hum);
    soilSeries.push(s === 'WET' ? 1 : 0);

    if (l) light[l] = (light[l] ?? 0) + 1;
    if (s) soil[s] = (soil[s] ?? 0) + 1;
    actions[act] = (actions[act] ?? 0) + 1;
    if (dis) diseases[dis] = (diseases[dis] ?? 0) + 1;

    rows.push({
      time,
      temp,
      hum,
      light: l,
      soil: s,
      img,
      disease: dis,
      action: act,
      plant,
      prompt,
      response: resp,
    });
  });

  return {
    labels,
    temps,
    hums,
    soilSeries,
    light,
    soil,
    actions,
    diseases,
    rows,
    latestPrompt,
    latestResponse,
  };
}

export function useSheetData() {
  const [data, setData] = useState<ProcessedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const url = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/gviz/tq?sheet=${SHEET_NAME}&t=${Date.now()}`;
      const res = await fetch(url);
      const text = await res.text();
      // Google Sheets wraps the JSON in a callback — strip it
      const json = JSON.parse(text.substring(47).slice(0, -2)) as {
        table: { rows: unknown[] };
      };
      const rawRows = json.table.rows.slice(-20);
      setData(parseRows(rawRows));
      setError(null);
    } catch {
      setError('Failed to fetch data from Google Sheets.');
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
