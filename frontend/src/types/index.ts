export interface SheetRow {
  time: string;
  temp: number | null;
  hum: number | null;
  light: string | null;
  soil: string | null;
  img: string | null;
  disease: string | null;
  action: string;
  plant: string;
  prompt: string | null;
  response: string | null;
}

export interface ProcessedData {
  labels: string[];
  temps: (number | null)[];
  hums: (number | null)[];
  soilSeries: number[];
  light: Record<string, number>;
  soil: Record<string, number>;
  actions: Record<string, number>;
  diseases: Record<string, number>;
  rows: SheetRow[];
  latestPrompt: string | null;
  latestResponse: string | null;
}
