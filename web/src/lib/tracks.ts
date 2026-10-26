import type { Track } from "./contracts";
export const TRACKS: Track[] = [
  {
    id: "portimao",
    name: "Portimão",
    country: "Portugal",
    lat: 37.2319,
    lon: -8.6267,
    timezone: "Europe/Lisbon",
    lengthKm: 4.653,
  },
  {
    id: "nogaro",
    name: "Nogaro",
    country: "France",
    lat: 43.77006,
    lon: -0.04033,
    timezone: "Europe/Paris",
    lengthKm: 3.636,
  },
  {
    id: "spa",
    name: "Spa-Francorchamps",
    country: "Belgium",
    lat: 50.4372,
    lon: 5.9714,
    timezone: "Europe/Brussels",
    lengthKm: 7.004,
  },
  {
    id: "paul-ricard",
    name: "Paul Ricard",
    country: "France",
    lat: 43.2506,
    lon: 5.7917,
    timezone: "Europe/Paris",
    lengthKm: 5.842,
  },
  {
    id: "nurburgring",
    name: "Nürburgring GP",
    country: "Germany",
    lat: 50.3356,
    lon: 6.9475,
    timezone: "Europe/Berlin",
    lengthKm: 5.148,
  },
  {
    id: "nordschleife",
    name: "Nürburgring Nordschleife",
    country: "Germany",
    lat: 50.3566,
    lon: 6.9689,
    timezone: "Europe/Berlin",
    lengthKm: 20.832,
  },
  {
    id: "lemans",
    name: "Le Mans · La Sarthe",
    country: "France",
    lat: 47.9497,
    lon: 0.2192,
    timezone: "Europe/Paris",
    lengthKm: 13.626,
  },
  {
    id: "barcelona",
    name: "Barcelona-Catalunya",
    country: "Spain",
    lat: 41.57,
    lon: 2.2611,
    timezone: "Europe/Madrid",
    lengthKm: 4.657,
  },
  {
    id: "silverstone",
    name: "Silverstone",
    country: "United Kingdom",
    lat: 52.0733,
    lon: -1.0147,
    timezone: "Europe/London",
    lengthKm: 5.891,
  },
  {
    id: "monza",
    name: "Monza",
    country: "Italy",
    lat: 45.6191,
    lon: 9.2822,
    timezone: "Europe/Rome",
    lengthKm: 5.793,
  },
  {
    id: "imola",
    name: "Imola",
    country: "Italy",
    lat: 44.3439,
    lon: 11.7167,
    timezone: "Europe/Rome",
    lengthKm: 4.909,
  },
  {
    id: "magny-cours",
    name: "Magny-Cours",
    country: "France",
    lat: 46.8642,
    lon: 3.1636,
    timezone: "Europe/Paris",
    lengthKm: 4.411,
  },
  {
    id: "alcaniz",
    name: "MotorLand Aragón",
    country: "Spain",
    lat: 41.0786,
    lon: -0.2033,
    timezone: "Europe/Madrid",
    lengthKm: 5.344,
  },
  {
    id: "jarama",
    name: "Jarama",
    country: "Spain",
    lat: 40.617,
    lon: -3.5855,
    timezone: "Europe/Madrid",
    lengthKm: 3.85,
  },
  {
    id: "jerez",
    name: "Jerez",
    country: "Spain",
    lat: 36.7083,
    lon: -6.0342,
    timezone: "Europe/Madrid",
    lengthKm: 4.428,
  },
  {
    id: "estoril",
    name: "Estoril",
    country: "Portugal",
    lat: 38.7509,
    lon: -9.3947,
    timezone: "Europe/Lisbon",
    lengthKm: 4.182,
  },
];
export const INITIAL_TRACKS = TRACKS.slice(0, 5);
export function validTrack(t: unknown): t is Track {
  if (!t || typeof t !== "object") return false;
  const v = t as Track;
  if (typeof v.timezone !== "string" || !v.timezone.trim()) return false;
  try {
    new Intl.DateTimeFormat("en", { timeZone: v.timezone }).format();
  } catch {
    return false;
  }
  return (
    typeof v.id === "string" &&
    typeof v.name === "string" &&
    v.name.length > 0 &&
    typeof v.country === "string" &&
    Number.isFinite(v.lat) &&
    Math.abs(v.lat) <= 90 &&
    Number.isFinite(v.lon) &&
    Math.abs(v.lon) <= 180
  );
}
