export interface TodoItem {
  action: string;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  reason: string;
}

export interface PlantRow {
  time: string;
  temp: number | null;
  hum: number | null;
  tempReadings: (number | null)[];
  humReadings: (number | null)[];
  soilReadings: string[];
  soilWetnessPct: number | null;
  light: string | null;
  soil: string | null;
  img: string | null;
  disease: string | null;
  action: string;
  plant: string;
  prompt: string | null;
  response: string | null;
  todos: TodoItem[];
}

export interface ProcessedData {
  labels: string[];
  temps: (number | null)[];
  hums: (number | null)[];
  soilSeries: number[];
  wetnessSeries: (number | null)[];
  light: Record<string, number>;
  soil: Record<string, number>;
  actions: Record<string, number>;
  diseases: Record<string, number>;
  rows: PlantRow[];
  latestPrompt: string | null;
  latestResponse: string | null;
  latestTodos: TodoItem[];
}
