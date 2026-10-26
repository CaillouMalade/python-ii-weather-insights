export type Track = {
  id: string;
  name: string;
  country: string;
  lat: number;
  lon: number;
  timezone: string;
  lengthKm?: number;
  custom?: boolean;
};
export type Hour = {
  time: number;
  temperature: number | null;
  precipitation: number | null;
  probability: number | null;
  wind: number | null;
  gust: number | null;
  direction: number | null;
  humidity: number | null;
  dewpoint: number | null;
  cloud: number | null;
  pressure: number | null;
  visibility: number | null;
  weatherCode: number | null;
};
export type Forecast = {
  id: string;
  name: string;
  provider: string;
  transport: string;
  family: string;
  color: string;
  resolution: string;
  fetchedAt: string;
  hours: Hour[];
  kind: "model" | "provider";
  caveat?: string;
};
export type SourceStatus = {
  id: string;
  name: string;
  status: "ok" | "error" | "unconfigured";
  message: string;
  fetchedAt?: string;
};
export type WeatherResponse = {
  fetchedAt: string;
  location: { lat: number; lon: number; timezone: string };
  forecasts: Forecast[];
  statuses: SourceStatus[];
  notes: string[];
};
export type ConsensusHour = {
  time: number;
  count: number;
  wetCount: number;
  wetShare: number | null;
  rainMedian: number | null;
  rainMin: number | null;
  rainMax: number | null;
  temperature: number | null;
  tempMin: number | null;
  tempMax: number | null;
  wind: number | null;
  gust: number | null;
  humidity: number | null;
  dewpoint: number | null;
  cloud: number | null;
  pressure: number | null;
  visibility: number | null;
  direction: number | null;
  probability: number | null;
  dewpointSpread: number | null;
  agreement: "unavailable" | "limited" | "split" | "mixed" | "aligned";
};
export type RadarResponse = {
  host: string;
  generated: number;
  frames: { time: number; path: string }[];
  coverageUrl: string;
  note: string;
};
/** Geometry coordinate pairs are [latitude, longitude], ready for Leaflet. GeoJSON assets are converted once by the backend. */
export type GeometryResponse = {
  coordinates: [number, number][][];
  source: string;
  attribution: string;
  fetchedAt: string;
  message?: string;
};
export type HistoryPoint = {
  fetchedAt: string;
  provider: string;
  forecastTime: number;
  temperature: number | null;
  precipitation: number | null;
  wind: number | null;
};
