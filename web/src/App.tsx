import { useEffect, useMemo, useRef, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
} from "recharts";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  CalendarDays,
  Check,
  ChevronDown,
  ChevronRight,
  Cloud,
  CloudDrizzle,
  CloudRain,
  Compass,
  Flag,
  Gauge,
  History,
  Info,
  Layers,
  Loader2,
  MapPin,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Sun,
  Thermometer,
  Trash2,
  Upload,
  Wind,
  X,
} from "lucide-react";
import CircuitMap from "@/components/pitwall/circuit-map";
import { apiFetch } from "@/lib/browser-api";
import { usePwa, InstallApp } from "@/components/pitwall/install-app";
import type {
  Track,
  WeatherResponse,
  Forecast,
  ConsensusHour,
  HistoryPoint,
  Session,
} from "@/lib/contracts";
import { buildConsensus, summarizeSession } from "@/lib/consensus";
import { getDryWindows, sessionSources } from "@/lib/session-planner";
import {
  createBackup,
  mergeBackup,
  parseBackup,
  parsePreferences,
  validSession,
} from "@/lib/device-state";
import { csvEscape, download, sessionsCalendar, toCsv } from "@/lib/exports";
import { useModalFocus } from "@/lib/use-modal-focus";
import { localEpoch } from "@/lib/local-time";
import { INITIAL_TRACKS, TRACKS, validTrack } from "@/lib/tracks";

type View = "overview" | "comparison" | "planner" | "history";
const TABS: [View, string, typeof Activity][] = [
  ["overview", "Overview", Activity],
  ["comparison", "Forecast comparison", Layers],
  ["planner", "Session planner", CalendarDays],
  ["history", "History & sources", History],
];
const n = (v: number | null | undefined, d = 0) =>
  v === null || v === undefined || !Number.isFinite(v) ? "—" : v.toFixed(d);
function time(t: number, tz: string, detail = false) {
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: tz,
    hour: "2-digit",
    minute: "2-digit",
    ...(detail ? { weekday: "short", day: "2-digit", month: "short" } : {}),
  }).format(t * 1000);
}
function day(t: number, tz: string) {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: tz,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(t * 1000);
}
function niceDate(d: string) {
  if (!Number.isFinite(new Date(d + "T12:00:00Z").getTime()))
    return "Choose date";
  return new Date(d + "T12:00:00Z").toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}
function max(values: (number | null)[]) {
  const f = values.filter((v): v is number => v !== null && Number.isFinite(v));
  return f.length ? Math.max(...f) : null;
}
function min(values: (number | null)[]) {
  const f = values.filter((v): v is number => v !== null && Number.isFinite(v));
  return f.length ? Math.min(...f) : null;
}
function mean(values: (number | null)[]) {
  const f = values.filter((v): v is number => v !== null && Number.isFinite(v));
  return f.length ? f.reduce((a, b) => a + b, 0) / f.length : null;
}
function compass(deg: number | null) {
  return deg === null
    ? "—"
    : [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
      ][Math.round(deg / 22.5) % 16];
}
function WeatherIcon({
  rain,
  cloud,
  size = 20,
}: {
  rain: number | null;
  cloud?: number | null;
  size?: number;
}) {
  if (rain === null && (cloud === null || cloud === undefined))
    return <Cloud size={size} style={{ opacity: 0.4 }} />;
  return rain !== null && rain >= 0.1 ? (
    <CloudRain size={size} />
  ) : cloud !== null && cloud !== undefined && cloud > 55 ? (
    <Cloud size={size} />
  ) : (
    <Sun size={size} />
  );
}
function Empty({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty-state">
      <Cloud size={28} />
      <strong>{title}</strong>
      <p>{detail}</p>
    </div>
  );
}
function ChartTip({
  active,
  payload,
  label,
  tz,
}: {
  active?: boolean;
  payload?: any[];
  label?: any;
  tz: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <strong>{time(Number(label), tz, true)}</strong>
      {payload.map((p: any, i: number) => (
        <div key={i}>
          <span style={{ background: p.color }} className="tiny-dot" />
          {p.name}
          <b>{n(p.value, 2)}</b>
        </div>
      ))}
    </div>
  );
}
function RainChart({
  hours,
  forecasts,
  tz,
  height = 220,
}: {
  hours: ConsensusHour[];
  forecasts: Forecast[];
  tz: string;
  height?: number;
}) {
  const rows = hours.map((h) => {
    const r: Record<string, any> = {
      time: h.time,
      median: h.rainMedian,
      range: h.rainMax,
    };
    forecasts.forEach(
      (f) =>
        (r[f.id] =
          f.hours.find((x) => x.time === h.time)?.precipitation ?? null),
    );
    return r;
  });
  if (!rows.length)
    return (
      <Empty
        title="No precipitation forecast"
        detail="Refresh the forecast or enable a weather source."
      />
    );
  return (
    <div className="chart" style={{ height }}>
      <ResponsiveContainer
        width="100%"
        height="100%"
        initialDimension={{ width: 320, height }}
      >
        <AreaChart
          data={rows}
          margin={{ top: 12, right: 16, left: -18, bottom: 0 }}
        >
          <defs>
            <linearGradient id="rain-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#e2fa76" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#e2fa76" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#ffffff0c" vertical={false} />
          <XAxis
            dataKey="time"
            tickFormatter={(t) => time(t, tz)}
            minTickGap={35}
            stroke="#58616b"
            tickLine={false}
            axisLine={false}
            fontSize={10}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            stroke="#58616b"
            fontSize={10}
            unit=""
            domain={[0, "auto"]}
          />
          <Tooltip content={<ChartTip tz={tz} />} />
          <Area
            dataKey="range"
            name="Highest forecast · mm/h"
            type="linear"
            stroke="none"
            fill="#758288"
            fillOpacity={0.09}
          />
          <Area
            dataKey="median"
            name="Family median · mm/h"
            type="linear"
            stroke="#e2fa76"
            strokeWidth={2}
            fill="url(#rain-fill)"
            connectNulls={false}
          />
          {forecasts.map((f) => (
            <Line
              key={f.id}
              dataKey={f.id}
              name={`${f.name} · mm/h`}
              stroke={f.color}
              strokeWidth={1.2}
              dot={false}
              type="linear"
              connectNulls={false}
              opacity={0.7}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
function MetricChart({
  hours,
  tz,
  metric,
}: {
  hours: ConsensusHour[];
  tz: string;
  metric: "temperature" | "wind";
}) {
  return (
    <div className="chart" style={{ height: 185 }}>
      <ResponsiveContainer
        width="100%"
        height="100%"
        initialDimension={{ width: 320, height: 185 }}
      >
        <LineChart
          data={hours}
          margin={{ top: 12, right: 12, left: -18, bottom: 0 }}
        >
          <CartesianGrid stroke="#ffffff0c" vertical={false} />
          <XAxis
            dataKey="time"
            tickFormatter={(t) => time(t, tz)}
            minTickGap={40}
            stroke="#58616b"
            tickLine={false}
            axisLine={false}
            fontSize={10}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            stroke="#58616b"
            fontSize={10}
          />
          <Tooltip content={<ChartTip tz={tz} />} />
          {metric === "temperature" ? (
            <>
              <Line
                dataKey="temperature"
                name="Median air · °C"
                stroke="#edc383"
                strokeWidth={2}
                dot={false}
                connectNulls={false}
              />
              <Line
                dataKey="dewpoint"
                name="Median dew point · °C"
                stroke="#8daaaa"
                strokeWidth={1.2}
                strokeDasharray="4 4"
                dot={false}
                connectNulls={false}
              />
            </>
          ) : (
            <>
              <Line
                dataKey="wind"
                name="Median wind · km/h"
                stroke="#94b4f5"
                strokeWidth={2}
                dot={false}
                connectNulls={false}
              />
              <Line
                dataKey="gust"
                name="Max gust · km/h"
                stroke="#bd9de5"
                strokeWidth={1.2}
                strokeDasharray="4 4"
                dot={false}
                connectNulls={false}
              />
            </>
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function Pitwall() {
  const pwa = usePwa();
  const refreshRequested = useRef(false);
  const backupInput = useRef<HTMLInputElement>(null);
  const [view, setView] = useState<View>("overview"),
    [track, setTrack] = useState<Track>(TRACKS[0]),
    [favorites, setFavorites] = useState<Track[]>(INITIAL_TRACKS),
    [data, setData] = useState<WeatherResponse | null>(null),
    [loading, setLoading] = useState(true),
    [error, setError] = useState(""),
    [refresh, setRefresh] = useState(0),
    [disabled, setDisabled] = useState<string[]>([]),
    [threshold, setThreshold] = useState(0.1),
    [settings, setSettings] = useState(false),
    [selectedDay, setSelectedDay] = useState(""),
    [horizon, setHorizon] = useState(24),
    [searchOpen, setSearchOpen] = useState(false),
    [query, setQuery] = useState(""),
    [searching, setSearching] = useState(false),
    [searchResults, setSearchResults] = useState<Track[]>([]),
    [searchError, setSearchError] = useState(""),
    [coordinateMode, setCoordinateMode] = useState(false),
    [coordName, setCoordName] = useState(""),
    [coordLat, setCoordLat] = useState(""),
    [coordLon, setCoordLon] = useState(""),
    [coordTz, setCoordTz] = useState("Europe/Madrid"),
    [hydrated, setHydrated] = useState(false),
    [mobileNav, setMobileNav] = useState(false),
    [sessions, setSessions] = useState<Session[]>([]),
    [sessionName, setSessionName] = useState("Practice"),
    [sessionDate, setSessionDate] = useState(""),
    [sessionTime, setSessionTime] = useState("10:00"),
    [duration, setDuration] = useState(60),
    [gustLimit, setGustLimit] = useState(40),
    [sessionError, setSessionError] = useState(""),
    [history, setHistory] = useState<HistoryPoint[]>([]),
    [historyLoading, setHistoryLoading] = useState(false),
    [historyMessage, setHistoryMessage] = useState(""),
    [historyRefresh, setHistoryRefresh] = useState(0),
    [historyValidHour, setHistoryValidHour] = useState(0),
    [historyMetric, setHistoryMetric] = useState<
      "temperature" | "precipitation" | "wind"
    >("temperature"),
    [clock, setClock] = useState(Date.now()),
    [editingSessionId, setEditingSessionId] = useState<string | null>(null),
    [sessionFeedback, setSessionFeedback] = useState(""),
    [deletedSession, setDeletedSession] = useState<Session | null>(null),
    [storageMessage, setStorageMessage] = useState(""),
    [canSave, setCanSave] = useState(true),
    [backupMessage, setBackupMessage] = useState("");
  useModalFocus(searchOpen || settings);
  useEffect(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem("pitwall-preferences") || "null",
      );
      if (saved) {
        const preferences = parsePreferences(saved);
        setFavorites(preferences.favorites);
        setTrack(preferences.track);
        setDisabled(preferences.disabled);
        setThreshold(preferences.threshold);
        setGustLimit(preferences.gustLimit);
      }
    } catch {
      setCanSave(false);
      setStorageMessage(
        "Saved preferences could not be read. Automatic saving is paused to preserve the existing data. Export your current plans or restore a Pitwall backup in preferences.",
      );
    }
    try {
      const ss = JSON.parse(localStorage.getItem("pitwall-sessions") || "[]");
      if (!Array.isArray(ss) || !ss.every(validSession))
        throw Error("Invalid saved sessions");
      setSessions(ss);
    } catch {
      setCanSave(false);
      setStorageMessage(
        "Saved sessions could not be read. Automatic saving is paused to preserve the existing data. Restore a Pitwall backup in preferences to resume saving.",
      );
    }
    setHydrated(true);
  }, []);
  useEffect(() => {
    if (hydrated && canSave)
      try {
        localStorage.setItem(
          "pitwall-preferences",
          JSON.stringify({ favorites, track, disabled, threshold, gustLimit }),
        );
        localStorage.setItem("pitwall-sessions", JSON.stringify(sessions));
        setStorageMessage("");
      } catch {
        setStorageMessage(
          "This browser could not save your latest changes. Keep Pitwall open and export a backup in preferences; storage may be full or blocked.",
        );
      }
  }, [
    hydrated,
    canSave,
    favorites,
    track,
    disabled,
    threshold,
    gustLimit,
    sessions,
  ]);
  useEffect(() => {
    if (!hydrated) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setData((previous) =>
      previous &&
      previous.location.lat.toFixed(4) === track.lat.toFixed(4) &&
      previous.location.lon.toFixed(4) === track.lon.toFixed(4) &&
      previous.location.timezone === track.timezone
        ? previous
        : null,
    );
    const force = refreshRequested.current;
    refreshRequested.current = false;
    apiFetch(
      `/api/weather?lat=${track.lat}&lon=${track.lon}&timezone=${encodeURIComponent(track.timezone)}${force ? "&refresh=1" : ""}`,
      { signal: controller.signal },
    )
      .then(async (r) => {
        const j: any = await r.json();
        if (!r.ok && !Array.isArray(j.forecasts))
          throw Error(
            j.error || "Weather could not be loaded. Please try again.",
          );
        return j as WeatherResponse;
      })
      .then((d) => {
        setData(d);
        if (!d.forecasts?.length)
          setError(
            "No forecast sources returned data. Check source status and try again.",
          );
      })
      .catch((e) => {
        if (e.name !== "AbortError") setError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [hydrated, track.id, track.lat, track.lon, track.timezone, refresh]);
  useEffect(() => {
    if (!hydrated) return;
    const nextHour = (Math.floor(Date.now() / 3600000) + 1) * 3600;
    setSessionDate(day(nextHour, track.timezone));
    setSessionTime(time(nextHour, track.timezone));
    setSelectedDay("");
    setEditingSessionId(null);
    setSessionFeedback("");
    setSessionError("");
    setDeletedSession(null);
  }, [hydrated, track.id, track.timezone]);
  useEffect(() => {
    const i = setInterval(() => setRefresh((v) => v + 1), 10 * 60 * 1000);
    return () => clearInterval(i);
  }, []);
  useEffect(() => {
    const tick = () => setClock(Date.now());
    const connected = () => {
      tick();
      refreshRequested.current = true;
      setRefresh((v) => v + 1);
    };
    const interval = setInterval(tick, 60000);
    window.addEventListener("focus", tick);
    window.addEventListener("online", connected);
    return () => {
      clearInterval(interval);
      window.removeEventListener("focus", tick);
      window.removeEventListener("online", connected);
    };
  }, []);
  useEffect(() => {
    if (!searchOpen || query.trim().length < 2) {
      setSearchResults([]);
      setSearchError("");
      setSearching(false);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setSearching(true);
      setSearchError("");
      apiFetch(`/api/search?q=${encodeURIComponent(query.trim())}`, {
        signal: controller.signal,
      })
        .then(async (r) => {
          const j: any = await r.json();
          if (!r.ok) throw Error(j.error || "Location search is unavailable.");
          return j;
        })
        .then((j) => {
          const rows = Array.isArray(j) ? j : j.results || [];
          setSearchResults(
            rows
              .map((r: any) => ({
                id: String(r.id ?? `place-${r.latitude}-${r.longitude}`),
                name: r.name,
                country: r.country || r.admin1 || "Custom location",
                lat: r.lat ?? r.latitude,
                lon: r.lon ?? r.longitude,
                timezone: r.timezone || "UTC",
                custom: true,
              }))
              .filter(validTrack),
          );
        })
        .catch((e) => {
          if (e.name !== "AbortError") setSearchError(e.message);
        })
        .finally(() => {
          if (!controller.signal.aborted) setSearching(false);
        });
    }, 350);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, searchOpen]);
  useEffect(() => {
    if (view !== "history") return;
    const controller = new AbortController();
    setHistoryLoading(true);
    setHistoryMessage("");
    apiFetch(`/api/history?lat=${track.lat}&lon=${track.lon}`, {
      signal: controller.signal,
    })
      .then(async (r) => {
        const j: any = await r.json();
        if (!r.ok) throw Error(j.error || "History is not available.");
        return j;
      })
      .then((j) => {
        setHistory(Array.isArray(j) ? j : j.points || j.history || []);
        setHistoryMessage(j.message || "");
      })
      .catch((e) => {
        if (e.name !== "AbortError") {
          setHistory([]);
          setHistoryMessage(e.message);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setHistoryLoading(false);
      });
    return () => controller.abort();
  }, [view, track.lat, track.lon, historyRefresh, data?.fetchedAt]);
  useEffect(() => {
    if (!searchOpen && !settings) return;
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSearchOpen(false);
        setSettings(false);
      }
    };
    document.addEventListener("keydown", key);
    return () => document.removeEventListener("keydown", key);
  }, [searchOpen, settings]);
  const active = useMemo(
    () => (data?.forecasts || []).filter((f) => !disabled.includes(f.id)),
    [data, disabled],
  );
  const consensus = useMemo(
    () => buildConsensus(active, threshold),
    [active, threshold],
  );
  const now = clock / 1000;
  const future = consensus.filter((h) => h.time + 3600 > now);
  const current = future.find((h) => h.time <= now);
  const days = [...new Set(future.map((h) => day(h.time, track.timezone)))];
  const shownDay = days.includes(selectedDay)
    ? selectedDay
    : days[0] || day(now, track.timezone);
  const hours = future
    .filter((h) => day(h.time, track.timezone) === shownDay)
    .slice(0, horizon);
  const upcoming = future.slice(0, 12);
  const hasRainEvidence = future.slice(0, 24).some((h) => h.wetShare !== null);
  const wetHour = future
    .slice(0, 24)
    .find((h) => h.rainMax !== null && h.rainMax >= threshold);
  const wetSignalSources = wetHour
    ? active.filter((f) =>
        f.hours.some(
          (h) =>
            h.time === wetHour.time &&
            h.precipitation !== null &&
            h.precipitation >= threshold,
        ),
      )
    : [];
  const maxGust = max(hours.map((h) => h.gust));
  const dissent = upcoming.find(
    (h) => h.agreement === "split" || h.agreement === "mixed",
  );
  const availableCount = data?.forecasts.length || 0;
  const families = [...new Set(active.map((f) => f.family))].length;
  const cachedSources =
    data?.statuses.filter((s) => s.status === "cached") ?? [];
  const oldestFetch = min(active.map((f) => Date.parse(f.fetchedAt) / 1000));
  const oldestAge =
    oldestFetch === null
      ? null
      : Math.max(0, Math.floor((now - oldestFetch) / 60));
  const first = upcoming[0];
  const narrative = !active.length
    ? "Enable a source to compare the forecast."
    : !first
      ? "Forecast hours are not available for this location."
      : first.wetShare === null
        ? "Rainfall is unavailable for the current forecast hour. No wet or dry agreement can be assessed for this interval."
        : first.count < 3
          ? "Fewer than three model families are available. Rain agreement is limited; inspect the individual sources."
          : dissent
            ? `Models diverge around ${time(dissent.time, track.timezone)}: ${dissent.wetCount} of ${dissent.count} families forecast at least ${threshold} mm in that hourly interval. Keep the radar in view.`
            : wetHour
              ? `The first wet signal appears in the ${time(wetHour.time, track.timezone)} hourly interval: ${wetSignalSources.map((f) => f.name).join(", ")} reaches ${threshold} mm. ${wetHour.wetCount} of ${wetHour.count} family medians cross that threshold; individual related feeds can disagree.`
              : `No enabled model family crosses ${threshold} mm per hour in the next 24 forecast hours. Local showers can still be missed.`;
  function refreshWeather() {
    refreshRequested.current = true;
    setRefresh((v) => v + 1);
  }
  function choose(t: Track) {
    setTrack(t);
    setFavorites((fs) => (fs.some((f) => f.id === t.id) ? fs : [...fs, t]));
    setSearchOpen(false);
    setQuery("");
    setMobileNav(false);
  }
  function toggleSource(id: string) {
    setDisabled((a) =>
      a.includes(id) ? a.filter((x) => x !== id) : [...a, id],
    );
  }
  function exportForecast() {
    if (!data) return;
    const rows = [
      [
        "location",
        "latitude",
        "longitude",
        "provider",
        "model",
        "family",
        "fetched_at_utc",
        "forecast_time_utc",
        "air_temperature_C",
        "precipitation_mm_hour",
        "rain_probability_pct",
        "wind_km_h",
        "gust_km_h",
        "humidity_pct",
        "dewpoint_C",
        "cloud_pct",
        "pressure_hPa",
        "visibility_m",
      ],
    ];
    data.forecasts.forEach((f) =>
      f.hours.forEach((h) =>
        rows.push([
          track.name,
          track.lat,
          track.lon,
          f.provider,
          f.name,
          f.family,
          f.fetchedAt,
          new Date(h.time * 1000).toISOString(),
          h.temperature,
          h.precipitation,
          h.probability,
          h.wind,
          h.gust,
          h.humidity,
          h.dewpoint,
          h.cloud,
          h.pressure,
          h.visibility,
        ] as any),
      ),
    );
    download(
      `pitwall-${track.id}-${day(now, "UTC")}.csv`,
      rows.map((r) => r.map(csvEscape).join(",")).join("\r\n"),
    );
  }
  function addCoordinates() {
    setSearchError("");
    const lat = Number(coordLat),
      lon = Number(coordLon);
    if (
      !coordName.trim() ||
      !coordLat.trim() ||
      !coordLon.trim() ||
      !Number.isFinite(lat) ||
      Math.abs(lat) > 90 ||
      !Number.isFinite(lon) ||
      Math.abs(lon) > 180
    ) {
      setSearchError(
        "Enter a name and valid latitude (−90 to 90) and longitude (−180 to 180).",
      );
      return;
    }
    const t: Track = {
      id: `custom-${lat.toFixed(5)}-${lon.toFixed(5)}`,
      name: coordName.trim(),
      country: "Custom location",
      lat,
      lon,
      timezone: coordTz,
      custom: true,
    };
    if (!validTrack(t)) {
      setSearchError("Enter a valid IANA timezone, such as Europe/Paris.");
      return;
    }
    choose(t);
  }
  function sessionStats(s: Session) {
    const start = localEpoch(s.date, s.time, track.timezone),
      end = start + s.duration * 60;
    const hs = consensus.filter((h) => h.time < end && h.time + 3600 > start);
    const coverage = summarizeSession(consensus, start, end);
    const sources = sessionSources(active, start, end, threshold);
    const complete =
      coverage.coverage === 1 &&
      sources.length > 0 &&
      sources.every((source) => source.rainCoverage === 1);
    const rawDisagreement = hs.some((h) => {
      const rain = sources
        .flatMap((source) =>
          source.hours.filter((hour) => hour.time === h.time),
        )
        .map((hour) => hour.precipitation)
        .filter(
          (value): value is number => value !== null && Number.isFinite(value),
        );
      return (
        rain.some((value) => value >= threshold) &&
        rain.some((value) => value < threshold)
      );
    });
    return {
      start,
      end,
      hs,
      complete,
      sources,
      anyWet: sources.some((source) => source.wetIntervals > 0),
      partialGusts: sources.some((source) => source.gustCoverage < 1),
      rain: max(hs.map((h) => h.rainMax)),
      gust: max(hs.map((h) => h.gust)),
      temp: mean(hs.map((h) => h.temperature)),
      share: max(hs.map((h) => h.wetShare)),
      split: rawDisagreement,
    };
  }
  const draft: Session = {
    id: "draft",
    name: sessionName,
    trackId: track.id,
    date: sessionDate,
    time: sessionTime,
    duration,
    track,
  };
  const stats = sessionStats(draft);
  const localSessions = sessions
    .filter((s) => s.trackId === track.id)
    .sort((a, b) => `${a.date}T${a.time}`.localeCompare(`${b.date}T${b.time}`));
  const dryWindows = useMemo(
    () => getDryWindows(active, now, threshold, gustLimit, duration),
    [active, now, threshold, gustLimit, duration],
  );
  const preferences = { favorites, track, disabled, threshold, gustLimit };
  function saveSession() {
    setSessionError("");
    setSessionFeedback("");
    const session: Session = {
      ...draft,
      id: editingSessionId ?? `session-${crypto.randomUUID()}`,
      name: sessionName.trim(),
    };
    if (
      !validSession(session) ||
      !Number.isFinite(localEpoch(session.date, session.time, track.timezone))
    ) {
      setSessionError(
        "Enter a valid name, date, duration and local time. Skipped or repeated daylight-saving times cannot be used; choose an unambiguous local hour.",
      );
      return;
    }
    const duplicate = sessions.find(
      (s) =>
        s.id !== session.id &&
        s.trackId === session.trackId &&
        s.name === session.name &&
        s.date === session.date &&
        s.time === session.time &&
        s.duration === session.duration,
    );
    if (duplicate) {
      setSessionError(
        "This session is already saved. Select it below to edit it.",
      );
      return;
    }
    setSessions((saved) =>
      editingSessionId
        ? saved.map((s) => (s.id === editingSessionId ? session : s))
        : [...saved, session],
    );
    setEditingSessionId(session.id);
    setSessionFeedback(
      `${editingSessionId ? "Updated" : "Saved"} ${session.name} for ${niceDate(session.date)} at ${session.time}.`,
    );
  }
  function exportCalendar() {
    try {
      download(
        `pitwall-${track.id}-sessions.ics`,
        sessionsCalendar(localSessions, [...TRACKS, ...favorites, track]),
        "text/calendar;charset=utf-8",
      );
      setSessionFeedback(
        "Calendar file downloaded. Import it into your calendar to add these session times.",
      );
    } catch (error) {
      setSessionError(
        error instanceof Error
          ? error.message
          : "The calendar could not be exported.",
      );
    }
  }
  async function importBackup(file: File | undefined) {
    if (!file) return;
    setBackupMessage("");
    try {
      if (file.size > 1048576)
        throw new Error("Choose a Pitwall backup smaller than 1 MB.");
      const merged = mergeBackup(
        preferences,
        sessions,
        parseBackup(await file.text()),
        () => `session-${crypto.randomUUID()}`,
      );
      setFavorites(merged.preferences.favorites);
      setTrack(merged.preferences.track);
      setDisabled(merged.preferences.disabled);
      setThreshold(merged.preferences.threshold);
      setGustLimit(merged.preferences.gustLimit);
      setSessions(merged.sessions);
      setEditingSessionId(null);
      setCanSave(true);
      setBackupMessage(
        `Backup restored: ${merged.added} session${merged.added === 1 ? "" : "s"} added. Existing circuits and sessions were kept; backup preferences applied.`,
      );
    } catch (error) {
      setBackupMessage(
        error instanceof Error
          ? error.message
          : "The backup could not be imported. Existing data are unchanged.",
      );
    } finally {
      if (backupInput.current) backupInput.current.value = "";
    }
  }
  function exportHistory() {
    download(
      `pitwall-${track.id}-history.csv`,
      toCsv([
        [
          "location",
          "latitude",
          "longitude",
          "timezone",
          "source",
          "fetched_at_utc",
          "forecast_time_utc",
          "temperature_C",
          "precipitation_mm_hour",
          "wind_km_h",
        ],
        ...history.map((p) => [
          track.name,
          track.lat,
          track.lon,
          track.timezone,
          p.provider,
          p.fetchedAt,
          new Date(p.forecastTime * 1000).toISOString(),
          p.temperature,
          p.precipitation,
          p.wind,
        ]),
      ]),
    );
  }
  const filteredTracks = TRACKS.filter((t) =>
    `${t.name} ${t.country}`.toLowerCase().includes(query.toLowerCase()),
  );
  const dateLabel = new Intl.DateTimeFormat("en-GB", {
    timeZone: track.timezone,
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format();
  const validHistoryHours = [
    ...new Set(history.map((p) => p.forecastTime)),
  ].sort((a, b) => a - b);
  const selectedHistoryHour = validHistoryHours.includes(historyValidHour)
    ? historyValidHour
    : validHistoryHours.find((t) => t + 3600 > now) ||
      validHistoryHours[0] ||
      0;
  const historyForHour = history.filter(
    (p) => p.forecastTime === selectedHistoryHour,
  );
  const historyLabel =
    historyMetric === "temperature"
      ? "air temperature"
      : historyMetric === "precipitation"
        ? "hourly rainfall"
        : "wind speed";
  const historyUnit =
    historyMetric === "temperature"
      ? "°C"
      : historyMetric === "precipitation"
        ? "mm/h"
        : "km/h";
  const historySourceIds = [...new Set(historyForHour.map((p) => p.provider))];
  const historySeries = historySourceIds.map((id) => ({
    id,
    points: historyForHour
      .filter((p) => p.provider === id)
      .map((p) => ({
        time: new Date(p.fetchedAt).getTime() / 1000,
        value: p[historyMetric],
      }))
      .sort((a, b) => a.time - b.time),
  }));
  const hasHistoryEvolution = historySeries.some(
    (series) =>
      new Set(series.points.filter((p) => p.value !== null).map((p) => p.time))
        .size >= 2,
  );
  const historyByFetch = [...new Set(historyForHour.map((p) => p.fetchedAt))]
    .map((f) => {
      const ps = historyForHour.filter((p) => p.fetchedAt === f);
      const row: Record<string, any> = { time: new Date(f).getTime() / 1000 };
      ps.forEach((p) => (row[p.provider] = p[historyMetric]));
      return row;
    })
    .sort((a, b) => a.time - b.time);
  return (
    <div className="app-shell">
      <aside
        id="saved-circuits"
        className={`sidebar ${mobileNav ? "open" : ""}`}
      >
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setView("overview");
          }}
        >
          <span className="brand-mark">
            <i />
            <i />
            <i />
            <i />
            <i />
          </span>
          <span>
            Pitwall<span className="brand-period">.</span>
            <small>RACE WEATHER</small>
          </span>
        </a>
        <div className="workspace-label">
          <span className="tiny-dot lime" /> YOUR WEATHER DESK
        </div>
        <div className="sidebar-heading">
          MY CIRCUITS{" "}
          <span>{favorites.length.toString().padStart(2, "0")}</span>
        </div>
        <div className="circuit-list">
          {favorites.map((f, i) => (
            <button
              key={f.id}
              className={`circuit-item ${f.id === track.id ? "active" : ""}`}
              onClick={() => choose(f)}
            >
              <span className="circuit-number">
                {(i + 1).toString().padStart(2, "0")}
              </span>
              <span>
                <strong>{f.name}</strong>
                <small>{f.country}</small>
              </span>
              {f.id === track.id ? (
                <span className="selected-point" />
              ) : (
                <ChevronRight size={12} />
              )}
            </button>
          ))}
        </div>
        <button
          className="add-circuit"
          onClick={() => {
            setCoordinateMode(false);
            setSearchOpen(true);
          }}
        >
          <Plus size={15} /> Add a circuit or location
        </button>
        <div className="sidebar-bottom">
          <InstallApp pwa={pwa} />
          <div className="sidebar-note">
            <Compass size={19} />
            <strong>
              One circuit.
              <br />
              Every perspective.
            </strong>
            <p>
              Compare the forecast.
              <br />
              Understand the uncertainty.
            </p>
          </div>
          <button
            className="sidebar-settings"
            onClick={() => setSettings(true)}
          >
            <SlidersHorizontal size={15} /> Weather preferences{" "}
            <ChevronRight size={12} />
          </button>
          <span className="version">
            PITWALL / V1.1 <span>LOCAL WORKSPACE</span>
          </span>
        </div>
      </aside>
      {mobileNav && (
        <button
          className="sidebar-scrim"
          aria-label="Close circuits"
          onClick={() => setMobileNav(false)}
        />
      )}
      <main className="workspace">
        <header className="topbar">
          <div className="breadcrumbs">
            <button
              className="mobile-menu"
              onClick={() => setMobileNav((v) => !v)}
              aria-label="Open saved circuits"
              aria-expanded={mobileNav}
              aria-controls="saved-circuits"
            >
              <Flag size={17} />
            </button>
            <span>Weather desk</span>
            <ChevronRight size={12} />
            <strong>{track.name}</strong>
          </div>
          <div className="topbar-right">
            <span className="timezone-label">
              {track.timezone.replace("_", " ")}
            </span>
            <span className="topbar-divider" />
            <span className="unit">°C · km/h</span>
            <button
              className="icon-button"
              onClick={() => setSettings(true)}
              aria-label="Weather preferences"
            >
              <Settings2 size={16} />
            </button>
          </div>
        </header>
        <div className="main-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                {track.country.toUpperCase()}{" "}
                <span className="dot-separator">/</span>{" "}
                {track.lengthKm
                  ? `${track.lengthKm.toFixed(3)} KM CIRCUIT`
                  : "CUSTOM WEATHER LOCATION"}
              </div>
              <h1>
                {track.name}
                <span className="heading-dot" />
              </h1>
              <p>
                {dateLabel}
                <span className="dot-separator">·</span>
                {track.lat.toFixed(4)}°, {track.lon.toFixed(4)}°
              </p>
            </div>
            <div className="heading-actions">
              <button
                className="button secondary"
                aria-label="Export data"
                onClick={exportForecast}
                disabled={!data?.forecasts.length}
              >
                <ArrowDownToLine size={14} />
                <span>Export data</span>
              </button>
              <button
                className="button"
                onClick={refreshWeather}
                disabled={loading}
              >
                <RefreshCw size={14} className={loading ? "spin" : ""} />
                {loading ? "Updating" : "Refresh"}
              </button>
            </div>
          </div>
          <nav className="view-tabs" aria-label="Weather views">
            {TABS.map(([id, label, Icon]) => (
              <button
                key={id}
                className={view === id ? "active" : ""}
                aria-current={view === id ? "page" : undefined}
                onClick={() => setView(id)}
              >
                <Icon size={15} />
                {label}
              </button>
            ))}
            <span className="updated-label">
              {loading ? (
                <>
                  <span className="tiny-dot amber" />
                  Fetching sources
                </>
              ) : data ? (
                <>
                  <span
                    className={`tiny-dot ${cachedSources.length ? "amber" : "lime"}`}
                  />
                  {cachedSources.length
                    ? "Saved data · "
                    : data.delivery === "cache"
                      ? "Cached · "
                      : ""}
                  Fetched{" "}
                  {time(
                    new Date(data.fetchedAt).getTime() / 1000,
                    track.timezone,
                  )}
                </>
              ) : (
                "Awaiting data"
              )}
            </span>
          </nav>
          {data?.forecasts.length ? (
            <div className="forecast-provenance">
              <span>
                {active.length} enabled feed{active.length === 1 ? "" : "s"} ·{" "}
                {families} model famil{families === 1 ? "y" : "ies"}
              </span>
              <span
                title={
                  oldestFetch === null
                    ? undefined
                    : `Oldest enabled forecast fetched ${time(oldestFetch, track.timezone, true)}`
                }
              >
                {oldestAge === null
                  ? "No source enabled"
                  : `Oldest fetch ${oldestAge < 60 ? `${oldestAge} min` : `${Math.floor(oldestAge / 60)}h ${oldestAge % 60}m`} ago`}
              </span>
            </div>
          ) : null}
          {pwa.offline && (
            <div className="offline-banner" role="status">
              <Info size={17} />
              <div>
                <strong>You are offline</strong>
                <p>
                  Saved circuits and sessions are available on this device.
                  Forecasts and radar require a connection; anything still on
                  screen may be out of date.
                </p>
              </div>
            </div>
          )}
          {cachedSources.length > 0 && (
            <div className="offline-banner" role="status">
              <History size={17} />
              <div>
                <strong>
                  {data?.delivery === "stale"
                    ? "Showing saved forecasts"
                    : "Some sources are using saved forecasts"}
                </strong>
                <p>
                  {cachedSources
                    .map(
                      (s) =>
                        `${s.name} (${s.fetchedAt ? time(Date.parse(s.fetchedAt) / 1000, track.timezone, true) : "fetch time unavailable"})`,
                    )
                    .join(" · ")}
                  . These sources could not refresh. Their original fetch times
                  and missing values are preserved.
                </p>
              </div>
            </div>
          )}
          {(storageMessage ||
            (data?.storage &&
              !data.storage.saved &&
              data.forecasts.length > 0)) && (
            <div className="offline-banner" role="status">
              <Info size={17} />
              <div>
                <strong>Device storage needs attention</strong>
                <p>{storageMessage || data?.storage?.message}</p>
              </div>
              <button
                className="button secondary"
                onClick={() => setSettings(true)}
              >
                Backups
              </button>
            </div>
          )}
          {error && (
            <div className="error-banner" role="alert">
              <Info size={18} />
              <div>
                <strong>Forecast unavailable</strong>
                <p>{error}</p>
              </div>
              <button onClick={refreshWeather} disabled={loading}>
                Try again <RefreshCw size={13} />
              </button>
            </div>
          )}
          {!loading &&
          data?.forecasts.length &&
          data.statuses.some((s) => s.status === "error") ? (
            <div className="error-banner" role="status">
              <Info size={18} />
              <div>
                <strong>Some forecast sources are unavailable</strong>
                <p>
                  {data.statuses.filter((s) => s.status === "error").length}{" "}
                  sources could not respond.{" "}
                  {data.statuses.some(
                    (s) =>
                      s.status === "error" && s.message.includes("rate limit"),
                  )
                    ? "The provider has rate-limited requests from this connection. Remaining sources still update."
                    : "The comparison uses only the sources that returned data."}
                </p>
              </div>
              <button onClick={() => setView("history")}>
                View source status <ChevronRight size={13} />
              </button>
            </div>
          ) : null}
          {loading && (
            <div className="loading-banner" role="status">
              <Loader2 size={16} className="spin" />
              Comparing weather sources for {track.name}…
              <span>Each source can succeed independently.</span>
            </div>
          )}
          {view === "overview" && (
            <>
              <div className="metric-grid">
                <div className="metric-card">
                  <div className="metric-label">
                    AIR TEMPERATURE <Thermometer size={16} />
                  </div>
                  <div className="metric-value">
                    {n(current?.temperature, 1)}
                    <span>°C</span>
                  </div>
                  <div className="metric-bottom">
                    <span>Model median</span>
                    <span>
                      {n(current?.tempMin, 1)}–{n(current?.tempMax, 1)}° range
                    </span>
                  </div>
                  <svg
                    className="metric-mini"
                    viewBox="0 0 140 28"
                    aria-hidden="true"
                  >
                    <path d="M0 27H140" stroke="#27322b" fill="none" />
                    {upcoming.length > 1 &&
                      upcoming.every((h) => h.temperature !== null) && (
                        <polyline
                          points={upcoming
                            .map(
                              (h, i) =>
                                `${(i / (upcoming.length - 1)) * 140},${27 - (((h.temperature ?? 0) - (min(upcoming.map((x) => x.temperature)) ?? 0)) / Math.max(1, (max(upcoming.map((x) => x.temperature)) ?? 0) - (min(upcoming.map((x) => x.temperature)) ?? 0))) * 22}`,
                            )
                            .join(" ")}
                          fill="none"
                          stroke="#e2fa76"
                          strokeWidth="1.5"
                        />
                      )}
                  </svg>
                </div>
                <div className="metric-card">
                  <div className="metric-label">
                    FIRST WET SIGNAL <CloudRain size={16} />
                  </div>
                  <div
                    className={`metric-value time-value ${!hasRainEvidence ? "missing-value" : ""}`}
                  >
                    {wetHour
                      ? time(wetHour.time, track.timezone)
                      : hasRainEvidence
                        ? "None"
                        : "Unavailable"}
                    <span>{wetHour ? "interval" : ""}</span>
                  </div>
                  <div className="metric-bottom">
                    <span>
                      {wetHour
                        ? `${wetSignalSources.length} source${wetSignalSources.length === 1 ? "" : "s"} · ${wetHour.wetCount}/${wetHour.count} families`
                        : "Next 24 forecast hours"}
                    </span>
                    <span className={wetHour ? "text-blue" : ""}>
                      {wetHour ? `≥${threshold} mm/h` : "Above threshold"}
                    </span>
                  </div>
                  <div className="metric-track">
                    {upcoming.map((h) => (
                      <span
                        key={h.time}
                        style={{
                          background:
                            h.wetShare === null
                              ? "#273032"
                              : `rgba(134,179,233,${0.12 + (h.wetShare || 0) * 0.7})`,
                        }}
                      />
                    ))}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">
                    WIND / PEAK GUST <Wind size={16} />
                  </div>
                  <div className="metric-value">
                    {n(current?.wind)}
                    <span>km/h</span>
                    <small className="gust-value">
                      {n(current?.gust)}
                      <span>gust</span>
                    </small>
                  </div>
                  <div className="metric-bottom">
                    <span className="wind-direction">
                      <Compass
                        size={12}
                        style={{
                          transform: `rotate(${current?.direction ?? 0}deg)`,
                        }}
                      />
                      {compass(current?.direction ?? null)}
                    </span>
                    <span>Gust = highest source</span>
                  </div>
                  <div className="wind-bars">
                    {upcoming.map((h) => (
                      <i
                        key={h.time}
                        style={{
                          height: `${Math.max(2, Math.min(25, (h.wind || 0) / 2))}px`,
                        }}
                      />
                    ))}
                  </div>
                </div>
                <div className="metric-card agreement-card">
                  <div className="metric-label">
                    MODEL AGREEMENT <Layers size={16} />
                  </div>
                  <div
                    className={`metric-value agreement-value ${current?.agreement === "unavailable" ? "missing-value" : ""}`}
                  >
                    {!current
                      ? "—"
                      : current.agreement === "unavailable"
                        ? "Unavailable"
                        : current.agreement === "limited"
                          ? "Limited"
                          : current.agreement === "aligned"
                            ? "Aligned"
                            : current.agreement === "split"
                              ? "Split"
                              : "Mixed"}
                    <span className={`signal ${current?.agreement || ""}`} />
                  </div>
                  <div className="metric-bottom">
                    <span>{families} model families</span>
                    <span>
                      {active.length}/{availableCount} sources on
                    </span>
                  </div>
                  <div className="family-track">
                    {Array.from({ length: Math.max(1, families) }).map(
                      (_, i) => (
                        <span key={i} />
                      ),
                    )}
                  </div>
                </div>
              </div>
              <div className={`consensus-banner ${dissent ? "uncertain" : ""}`}>
                <div className="consensus-symbol">
                  <Activity size={19} />
                </div>
                <div>
                  <span className="eyebrow">THE PADDOCK BRIEF</span>
                  <p>{narrative}</p>
                </div>
                <button onClick={() => setView("comparison")}>
                  Inspect models <ArrowRight size={15} />
                </button>
              </div>
              <div className="overview-main">
                <CircuitMap track={track} />
                <section className="panel next-hours">
                  <div className="panel-head">
                    <div>
                      <div className="eyebrow">NEXT 12 HOURS</div>
                      <h2>The session outlook</h2>
                    </div>
                    <span className="subtle-chip">Local time</span>
                  </div>
                  <div className="hours-table">
                    <div className="hours-table-head">
                      <span>TIME</span>
                      <span>FORECAST</span>
                      <span>RAIN</span>
                      <span>WET VOTE</span>
                    </div>
                    {upcoming.length ? (
                      upcoming.map((h) => (
                        <div
                          className={`hour-row ${h.time <= now ? "now" : ""}`}
                          key={h.time}
                        >
                          <span className="hour-time">
                            {time(h.time, track.timezone)}
                            {h.time <= now && <small>NOW*</small>}
                          </span>
                          <span className="hour-temperature">
                            <WeatherIcon
                              rain={h.rainMedian}
                              cloud={h.cloud}
                              size={17}
                            />
                            {n(h.temperature)}°
                          </span>
                          <span>
                            {n(h.rainMedian, 1)} <small>mm</small>
                          </span>
                          <span
                            className={`vote ${h.wetShare && h.wetShare > 0 ? "wet" : ""}`}
                          >
                            {h.wetShare === null
                              ? "—"
                              : `${h.wetCount}/${h.count}`}
                            <i
                              style={{ width: `${(h.wetShare ?? 0) * 100}%` }}
                            />
                          </span>
                        </div>
                      ))
                    ) : (
                      <Empty
                        title="Waiting for the forecast"
                        detail="The hourly outlook appears when a source returns data."
                      />
                    )}
                  </div>
                  <p className="table-footnote">
                    * Current hourly forecast, not an on-track reading. Wet vote
                    counts model families, not rain probability.
                  </p>
                </section>
              </div>
              <section className="panel forecast-panel">
                <div className="panel-head">
                  <div>
                    <div className="eyebrow">
                      WHERE MODELS MEET — AND DIFFER
                    </div>
                    <h2>
                      Precipitation outlook{" "}
                      <span className="title-unit">mm per hourly interval</span>
                    </h2>
                  </div>
                  <div className="date-tabs">
                    {days.map((d) => (
                      <button
                        key={d}
                        className={shownDay === d ? "active" : ""}
                        onClick={() => setSelectedDay(d)}
                      >
                        {niceDate(d)}
                      </button>
                    ))}
                  </div>
                </div>
                <RainChart
                  hours={hours}
                  forecasts={active}
                  tz={track.timezone}
                />
                <div className="chart-legend">
                  <span>
                    <i style={{ background: "#e2fa76" }} />
                    Family median
                  </span>
                  {active.map((f) => (
                    <span key={f.id}>
                      <i style={{ background: f.color }} />
                      {f.name}
                    </span>
                  ))}
                  <span className="legend-note">
                    Forecast uncertainty remains even when models agree.
                  </span>
                </div>
              </section>
              <div className="two-charts">
                <section className="panel">
                  <div className="panel-head">
                    <div>
                      <div className="eyebrow">THERMAL PICTURE</div>
                      <h2>
                        Air & dew point <span className="title-unit">°C</span>
                      </h2>
                    </div>
                    <Thermometer size={18} className="muted" />
                  </div>
                  <MetricChart
                    hours={hours}
                    tz={track.timezone}
                    metric="temperature"
                  />
                  <p className="chart-note">
                    Air temperature only. Track surface temperature requires a
                    measurement or a separate model.
                  </p>
                </section>
                <section className="panel">
                  <div className="panel-head">
                    <div>
                      <div className="eyebrow">WIND EXPOSURE</div>
                      <h2>
                        Wind & gusts <span className="title-unit">km/h</span>
                      </h2>
                    </div>
                    <Wind size={18} className="muted" />
                  </div>
                  <MetricChart
                    hours={hours}
                    tz={track.timezone}
                    metric="wind"
                  />
                  <p className="chart-note">
                    Solid: median wind. Dashed: highest available gust.
                    Direction and exposure vary around the lap.
                  </p>
                </section>
              </div>
              <section className="panel atmosphere-panel">
                <div className="panel-head">
                  <div>
                    <div className="eyebrow">THE REST OF THE PICTURE</div>
                    <h2>
                      Atmospheric detail{" "}
                      <span className="title-unit">
                        Current hourly model estimate
                      </span>
                    </h2>
                  </div>
                  <CloudDrizzle size={18} className="muted" />
                </div>
                <div className="atmosphere-grid">
                  <div>
                    <span>RELATIVE HUMIDITY</span>
                    <strong>
                      {n(current?.humidity)}
                      <small>%</small>
                    </strong>
                  </div>
                  <div>
                    <span>DEW POINT</span>
                    <strong>
                      {n(current?.dewpoint, 1)}
                      <small>°C</small>
                    </strong>
                  </div>
                  <div>
                    <span>AIR − DEW POINT</span>
                    <strong>
                      {n(current?.dewpointSpread, 1)}
                      <small>°C</small>
                    </strong>
                  </div>
                  <div>
                    <span>CLOUD COVER</span>
                    <strong>
                      {n(current?.cloud)}
                      <small>%</small>
                    </strong>
                  </div>
                  <div>
                    <span>PRESSURE</span>
                    <strong>
                      {n(current?.pressure)}
                      <small>hPa</small>
                    </strong>
                  </div>
                  <div>
                    <span>VISIBILITY</span>
                    <strong>
                      {current?.visibility === null ||
                      current?.visibility === undefined
                        ? "—"
                        : n(current.visibility / 1000, 1)}
                      <small>km</small>
                    </strong>
                  </div>
                </div>
                <p className="chart-note">
                  A small air–dew point spread indicates near-saturated air; it
                  does not establish surface condensation. A dash means this
                  field was not reported by the enabled sources.
                </p>
              </section>
            </>
          )}
          {view === "comparison" && (
            <>
              <div className="section-intro">
                <div>
                  <div className="eyebrow">A SECOND OPINION. AND A THIRD.</div>
                  <h2>See the disagreement.</h2>
                  <p>
                    Compare the same valid hour across the enabled sources. A
                    family gets one consensus vote, even when multiple services
                    use it.
                  </p>
                </div>
                <button
                  className="button secondary"
                  onClick={() => setSettings(true)}
                >
                  <SlidersHorizontal size={14} />
                  Choose sources
                </button>
              </div>
              <section className="panel">
                <div className="panel-head">
                  <div>
                    <h2>Rain by source</h2>
                    <p className="subtext">
                      Precipitation · mm in the hourly interval beginning at the
                      indicated time
                    </p>
                  </div>
                  <select
                    aria-label="Forecast hours displayed"
                    value={horizon}
                    onChange={(e) => setHorizon(+e.target.value)}
                  >
                    <option value={12}>12 hours</option>
                    <option value={24}>24 hours</option>
                    <option value={48}>48 hours</option>
                    <option value={72}>72 hours</option>
                  </select>
                </div>
                <RainChart
                  hours={future.slice(0, horizon)}
                  forecasts={active}
                  tz={track.timezone}
                  height={280}
                />
                <div className="chart-legend">
                  {active.map((f) => (
                    <button
                      className="legend-source"
                      key={f.id}
                      onClick={() => toggleSource(f.id)}
                      title="Hide this source"
                    >
                      <i style={{ background: f.color }} />
                      {f.name}
                    </button>
                  ))}
                </div>
              </section>
              <section className="panel heatmap-panel">
                <div className="panel-head">
                  <div>
                    <div className="eyebrow">MODEL RAINFALL MATRIX</div>
                    <h2>A wet hour, at a glance.</h2>
                  </div>
                  <span className="subtle-chip">
                    Wet threshold ≥ {threshold} mm/h
                  </span>
                </div>
                <div className="heatmap-scroll">
                  <table className="heatmap">
                    <thead>
                      <tr>
                        <th>FORECAST SOURCE</th>
                        {future.slice(0, 24).map((h) => (
                          <th key={h.time}>
                            {time(h.time, track.timezone).slice(0, 2)}
                            <small>
                              {day(h.time, track.timezone) !==
                              day(future[0].time, track.timezone)
                                ? "+1d"
                                : ""}
                            </small>
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {active.map((f) => (
                        <tr key={f.id}>
                          <th>
                            <i style={{ background: f.color }} />
                            {f.name}
                            <small>{f.resolution}</small>
                          </th>
                          {future.slice(0, 24).map((h) => {
                            const v =
                              f.hours.find((x) => x.time === h.time)
                                ?.precipitation ?? null;
                            return (
                              <td
                                key={h.time}
                                title={`${f.name} · ${time(h.time, track.timezone, true)} · ${n(v, 2)} mm`}
                                style={{
                                  background:
                                    v === null
                                      ? "#171c1e"
                                      : v >= threshold
                                        ? `rgba(127,177,224,${Math.min(0.8, 0.15 + v * 0.25)})`
                                        : "#ffffff03",
                                  color:
                                    v === null
                                      ? "#50585e"
                                      : v >= threshold
                                        ? "#d2e9ff"
                                        : "#6c767a",
                                }}
                              >
                                {n(v, 1)}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                      <tr className="consensus-row">
                        <th>
                          Wet family vote<small>Not probability</small>
                        </th>
                        {future.slice(0, 24).map((h) => (
                          <td
                            key={h.time}
                            className={
                              h.agreement === "split" || h.agreement === "mixed"
                                ? "split-cell"
                                : ""
                            }
                          >
                            {h.wetShare === null
                              ? "—"
                              : `${h.wetCount}/${h.count}`}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p className="chart-note">
                  A dash means unavailable; it is never treated as zero rain.
                  Hourly amounts can conceal short, intense showers.
                </p>
              </section>
              <div className="section-label">
                THE SOURCES BEHIND YOUR FORECAST{" "}
                <span>{availableCount} returned data</span>
              </div>
              <div className="sources-grid">
                {data?.forecasts.map((f) => (
                  <SourceCard
                    key={f.id}
                    forecast={f}
                    disabled={disabled.includes(f.id)}
                    toggle={() => toggleSource(f.id)}
                    tz={track.timezone}
                  />
                ))}
              </div>
              <div className="method-note">
                <Info size={18} />
                <div>
                  <strong>Agreement is a signal, not a guarantee.</strong>
                  <p>
                    The median summarizes enabled, available model families.
                    Related services are grouped before counting votes.
                    Different models share observations and methods, and their
                    errors can be correlated. More sources do not automatically
                    mean better accuracy.
                  </p>
                </div>
              </div>
            </>
          )}
          {view === "planner" && (
            <>
              <div className="section-intro">
                <div>
                  <div className="eyebrow">PREPARE FOR YOUR TIME ON TRACK</div>
                  <h2>The session comes first.</h2>
                  <p>
                    Inspect the forecast over a session window. Rain and gust
                    summaries use all overlapping hourly intervals.
                  </p>
                </div>
                <span className="subtle-chip">
                  <MapPin size={12} />
                  {track.name}
                </span>
              </div>
              <div className="planner-grid">
                <section className="panel session-form">
                  <div className="panel-head">
                    <h2>
                      {editingSessionId ? "Edit session" : "Plan a session"}
                    </h2>
                    <CalendarDays size={18} className="muted" />
                  </div>
                  <div className="form-body">
                    <label>
                      SESSION NAME
                      <input
                        value={sessionName}
                        maxLength={60}
                        onChange={(e) => setSessionName(e.target.value)}
                        placeholder="Qualifying, Race 1, Practice…"
                      />
                    </label>
                    <div className="form-pair">
                      <label>
                        DATE
                        <input
                          type="date"
                          aria-label="Session date"
                          value={sessionDate}
                          onChange={(e) => setSessionDate(e.target.value)}
                        />
                      </label>
                      <label>
                        START · LOCAL TIME
                        <input
                          type="time"
                          aria-label="Session start time"
                          value={sessionTime}
                          onChange={(e) => setSessionTime(e.target.value)}
                        />
                      </label>
                    </div>
                    <div className="form-pair">
                      <label>
                        DURATION
                        <select
                          value={duration}
                          onChange={(e) => setDuration(+e.target.value)}
                        >
                          <option value={15}>15 minutes</option>
                          <option value={20}>20 minutes</option>
                          <option value={30}>30 minutes</option>
                          <option value={45}>45 minutes</option>
                          <option value={60}>1 hour</option>
                          <option value={90}>90 minutes</option>
                          <option value={120}>2 hours</option>
                          <option value={180}>3 hours</option>
                          <option value={360}>6 hours</option>
                          <option value={720}>12 hours</option>
                          <option value={1440}>24 hours</option>
                          {![
                            15, 20, 30, 45, 60, 90, 120, 180, 360, 720, 1440,
                          ].includes(duration) && (
                            <option value={duration}>{duration} minutes</option>
                          )}
                        </select>
                      </label>
                      <label>
                        GUST REVIEW THRESHOLD
                        <select
                          value={gustLimit}
                          onChange={(e) => setGustLimit(+e.target.value)}
                        >
                          <option value={25}>25 km/h</option>
                          <option value={30}>30 km/h</option>
                          <option value={40}>40 km/h</option>
                          <option value={50}>50 km/h</option>
                          <option value={60}>60 km/h</option>
                        </select>
                      </label>
                    </div>
                    <p className="field-note">
                      Times use {track.timezone}. The gust threshold is your
                      review preference, not a safety or race-control limit.
                    </p>
                    {sessionError && (
                      <p className="inline-warning">{sessionError}</p>
                    )}
                    <button className="button full-width" onClick={saveSession}>
                      {editingSessionId ? (
                        <Check size={15} />
                      ) : (
                        <Plus size={15} />
                      )}
                      {editingSessionId
                        ? "Update saved session"
                        : "Save session on this device"}
                    </button>
                    {editingSessionId && (
                      <button
                        className="button secondary full-width"
                        onClick={() => {
                          setEditingSessionId(null);
                          setSessionName("Practice");
                          setSessionError("");
                          setSessionFeedback("");
                        }}
                      >
                        <Plus size={15} />
                        Plan another session
                      </button>
                    )}
                    {sessionFeedback && (
                      <p className="session-feedback" role="status">
                        {sessionFeedback}
                      </p>
                    )}
                  </div>
                </section>
                <section className="panel session-summary">
                  <div className="panel-head">
                    <div>
                      <div className="eyebrow">
                        {niceDate(draft.date)} · {sessionTime}
                      </div>
                      <h2>
                        {sessionName || "Your session"}{" "}
                        <span className="title-unit">{duration} min</span>
                      </h2>
                    </div>
                    <span
                      className={`status-pill ${stats.complete ? "" : "amber"}`}
                    >
                      {stats.complete
                        ? "Rain coverage complete"
                        : "Incomplete rain coverage"}
                    </span>
                  </div>
                  {stats.hs.length ? (
                    <>
                      <div className="session-metrics">
                        <div>
                          <span>MAX HOURLY RAIN</span>
                          <strong>
                            {n(stats.rain, 1)}
                            <small> mm</small>
                          </strong>
                          <p>Highest source, overlapping hours</p>
                        </div>
                        <div>
                          <span>PEAK GUST</span>
                          <strong>
                            {n(stats.gust)}
                            <small> km/h</small>
                          </strong>
                          <p>
                            {stats.gust !== null && stats.gust >= gustLimit
                              ? "Above your review threshold"
                              : stats.partialGusts
                                ? "Some sources do not report gusts"
                                : "Compared with your threshold"}
                          </p>
                        </div>
                        <div>
                          <span>MEDIAN AIR</span>
                          <strong>
                            {n(stats.temp, 1)}
                            <small> °C</small>
                          </strong>
                          <p>Mean of hourly family medians</p>
                        </div>
                        <div>
                          <span>MAX WET VOTE</span>
                          <strong>
                            {stats.share === null
                              ? "—"
                              : `${Math.round(stats.share * 100)}%`}
                            <small> families</small>
                          </strong>
                          <p>Not a chance of precipitation</p>
                        </div>
                      </div>
                      <div
                        className={`session-assessment ${stats.anyWet || (stats.gust !== null && stats.gust >= gustLimit) ? "review" : ""}`}
                      >
                        <Activity size={20} />
                        <div>
                          <strong>
                            {!stats.complete
                              ? "Incomplete forecast coverage"
                              : stats.split
                                ? "Models disagree during this window"
                                : stats.anyWet
                                  ? "Rain appears in this window"
                                  : stats.gust !== null &&
                                      stats.gust >= gustLimit
                                    ? "Gusts exceed your review threshold"
                                    : "No wet signal above your threshold"}
                          </strong>
                          <p>
                            {!stats.complete
                              ? "Some enabled sources or hourly rain intervals are missing. Inspect the source coverage below; unavailable rain is not dry weather."
                              : stats.split
                                ? "Inspect each source and radar before the session."
                                : stats.anyWet
                                  ? `At least one source reaches ${threshold} mm/h. Hourly forecasts cannot resolve exact shower onset.`
                                  : "This describes forecast rainfall, not grip, standing water, or whether the surface has dried."}
                          </p>
                        </div>
                      </div>
                      <RainChart
                        hours={stats.hs}
                        forecasts={active}
                        tz={track.timezone}
                        height={170}
                      />
                    </>
                  ) : (
                    <Empty
                      title="No forecast for this window"
                      detail="Choose a time within the available forecast horizon, then refresh if needed."
                    />
                  )}
                </section>
              </div>
              <section className="panel session-source-panel">
                <div className="panel-head">
                  <div>
                    <div className="eyebrow">
                      EVERY SOURCE DURING YOUR SESSION
                    </div>
                    <h2>What each forecast says</h2>
                  </div>
                  <span className="subtle-chip">
                    {duration} min · {track.timezone}
                  </span>
                </div>
                {stats.sources.length ? (
                  <div
                    className="session-table-scroll"
                    tabIndex={0}
                    role="region"
                    aria-label="Per-source session forecasts, scroll horizontally"
                  >
                    <table className="session-source-table">
                      <caption className="sr-only">
                        Forecast evidence for {sessionName},{" "}
                        {niceDate(draft.date)} at {draft.time}, {duration}{" "}
                        minutes.
                      </caption>
                      <thead>
                        <tr>
                          <th scope="col">Source · fetched</th>
                          <th scope="col">
                            Peak hourly rain
                            <br />
                            mm/h
                          </th>
                          <th scope="col">
                            Session rain estimate
                            <br />
                            mm
                          </th>
                          <th scope="col">
                            Peak gust
                            <br />
                            km/h
                          </th>
                          <th scope="col">
                            Air range
                            <br />
                            °C
                          </th>
                          <th scope="col">Rain coverage</th>
                          <th scope="col">Gust coverage</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stats.sources.map((source) => (
                          <tr key={source.id}>
                            <th scope="row">
                              <span
                                className="tiny-dot"
                                style={{ background: source.color }}
                              />
                              {source.name}
                              <small>
                                {time(
                                  Date.parse(source.fetchedAt) / 1000,
                                  track.timezone,
                                  true,
                                )}
                              </small>
                            </th>
                            <td
                              className={
                                source.wetIntervals ? "text-amber" : ""
                              }
                            >
                              {n(source.peakRain, 2)}
                            </td>
                            <td>
                              {n(source.rainEstimate, 2)}
                              {source.rainCoverage > 0 &&
                              source.rainCoverage < 1
                                ? "*"
                                : ""}
                            </td>
                            <td
                              className={
                                source.peakGust !== null &&
                                source.peakGust >= gustLimit
                                  ? "text-amber"
                                  : ""
                              }
                            >
                              {n(source.peakGust)}
                            </td>
                            <td>
                              {n(source.minTemperature, 1)}–
                              {n(source.maxTemperature, 1)}
                            </td>
                            <td>
                              <span
                                className={`status-pill ${source.rainCoverage === 1 ? "" : "amber"}`}
                              >
                                {Math.round(source.rainCoverage * 100)}%
                              </span>
                            </td>
                            <td>
                              <span
                                className={`status-pill ${source.gustCoverage === 1 ? "" : "amber"}`}
                              >
                                {Math.round(source.gustCoverage * 100)}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <Empty
                    title="No enabled forecasts"
                    detail="Enable a source or refresh to inspect the session."
                  />
                )}
                <p className="chart-note">
                  Session rain is a rough estimate: hourly amounts are prorated
                  over the session’s overlap. It does not resolve shower timing.
                  * Partial coverage totals include reported intervals only.
                  Coverage is the fraction of your session with that field
                  available; related feeds remain visible separately.
                </p>
              </section>
              <div className="two-charts">
                <section className="panel">
                  <div className="panel-head">
                    <div>
                      <div className="eyebrow">A WINDOW TO INVESTIGATE</div>
                      <h2>Model-dry windows</h2>
                    </div>
                    <Sun size={18} className="text-lime" />
                  </div>
                  <div className="dry-windows">
                    {dryWindows.length ? (
                      dryWindows.slice(0, 5).map((w, i) => (
                        <div className="dry-window" key={i}>
                          <span className="window-icon">
                            <Sun size={16} />
                          </span>
                          <div>
                            <strong>
                              {time(w.start, track.timezone)} –{" "}
                              {time(w.end, track.timezone)}
                            </strong>
                            <span>
                              {niceDate(day(w.start, track.timezone))}
                              {day(w.start, track.timezone) !==
                              day(w.end, track.timezone)
                                ? ` → ${niceDate(day(w.end, track.timezone))}`
                                : ""}{" "}
                              · {n((w.end - w.start) / 3600, 1)}h available
                              <br />
                              {w.sourceCount} rain sources · gusts from ≥
                              {w.minGustSources}/{w.sourceCount} sources
                            </span>
                          </div>
                          <span className="status-pill">
                            {n(w.peakGust)} km/h gust
                          </span>
                          <button
                            className="button secondary window-use"
                            onClick={() => {
                              setSessionDate(day(w.start, track.timezone));
                              setSessionTime(time(w.start, track.timezone));
                              setEditingSessionId(null);
                              setSessionError("");
                              setSessionFeedback(
                                `Selected a window for your ${duration}-minute session.`,
                              );
                              document
                                .querySelector(".session-form")
                                ?.scrollIntoView({ block: "center" });
                            }}
                          >
                            Use window <ArrowRight size={12} />
                          </button>
                        </div>
                      ))
                    ) : (
                      <Empty
                        title="No qualifying window"
                        detail={`Needs ${duration} contiguous minutes, rain below ${threshold} mm/h from every enabled source, and gusts from at least two families below ${gustLimit} km/h.`}
                      />
                    )}
                  </div>
                  <p className="chart-note">
                    Every enabled source must report rain below {threshold} mm/h
                    throughout a window that fits your {duration}-minute
                    session. Highest reported gust stays below {gustLimit} km/h,
                    with at least two gust-reporting families. Missing gust
                    sources are counted above. This does not establish a dry
                    racing surface.
                  </p>
                </section>
                <section className="panel">
                  <div className="panel-head">
                    <div>
                      <div className="eyebrow">SAVED ON THIS DEVICE</div>
                      <h2>
                        Your sessions{" "}
                        <span className="title-unit">
                          {localSessions.length}
                        </span>
                      </h2>
                    </div>
                    <Flag size={18} className="muted" />
                  </div>
                  <div className="session-list-actions">
                    <button
                      className="button secondary"
                      disabled={!localSessions.length}
                      onClick={exportCalendar}
                    >
                      <ArrowDownToLine size={14} />
                      Export calendar (.ics)
                    </button>
                  </div>
                  {deletedSession && (
                    <div className="undo-session" role="status">
                      <span>Removed {deletedSession.name}.</span>
                      <button
                        onClick={() => {
                          setSessions((saved) =>
                            saved.some((s) => s.id === deletedSession.id)
                              ? saved
                              : [...saved, deletedSession],
                          );
                          setDeletedSession(null);
                        }}
                      >
                        Undo
                      </button>
                    </div>
                  )}
                  <div className="saved-sessions">
                    {localSessions.length ? (
                      localSessions.map((s) => {
                        const ss = sessionStats(s);
                        return (
                          <div className="saved-session" key={s.id}>
                            <button
                              onClick={() => {
                                setSessionName(s.name);
                                setSessionDate(s.date);
                                setSessionTime(s.time);
                                setDuration(s.duration);
                                setEditingSessionId(s.id);
                                setSessionError("");
                                setSessionFeedback("");
                                document
                                  .querySelector(".session-form")
                                  ?.scrollIntoView({ block: "center" });
                              }}
                            >
                              <strong>
                                {s.name}
                                <ChevronRight size={13} />
                              </strong>
                              <span>
                                {niceDate(s.date)} · {s.time} · {s.duration} min
                              </span>
                              <small>
                                {ss.complete
                                  ? `${n(ss.rain, 1)} mm max hourly rain · ${n(ss.gust)} km/h peak gust`
                                  : "Forecast not fully available yet"}
                              </small>
                            </button>
                            <button
                              className="icon-button delete-session"
                              onClick={() => {
                                setDeletedSession(s);
                                setSessions((a) =>
                                  a.filter((x) => x.id !== s.id),
                                );
                                if (editingSessionId === s.id)
                                  setEditingSessionId(null);
                              }}
                              aria-label={`Delete ${s.name}`}
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        );
                      })
                    ) : (
                      <Empty
                        title="Your next session starts here"
                        detail="Save practice, qualifying and race windows for this circuit."
                      />
                    )}
                  </div>
                </section>
              </div>
            </>
          )}
          {view === "history" && (
            <>
              <div className="section-intro">
                <div>
                  <div className="eyebrow">
                    PROVENANCE, WITHOUT THE GUESSWORK
                  </div>
                  <h2>Know what you are looking at.</h2>
                  <p>
                    Every source has a different model, resolution and update
                    cycle. These details matter when you compare forecasts.
                  </p>
                </div>
                <button
                  className="button secondary"
                  onClick={() => setHistoryRefresh((v) => v + 1)}
                  disabled={historyLoading}
                >
                  <RefreshCw size={14} />
                  Reload history
                </button>
              </div>
              <section className="panel">
                <div className="panel-head">
                  <div>
                    <div className="eyebrow">LOCAL FETCH LOG</div>
                    <h2>
                      Forecast evolution{" "}
                      <span className="title-unit">
                        {history.length} recorded rows
                      </span>
                    </h2>
                  </div>
                  <div className="history-controls">
                    <label className="history-hour-select">
                      METRIC
                      <select
                        aria-label="Forecast evolution metric"
                        value={historyMetric}
                        onChange={(e) =>
                          setHistoryMetric(
                            e.target.value as typeof historyMetric,
                          )
                        }
                      >
                        <option value="temperature">
                          Air temperature · °C
                        </option>
                        <option value="precipitation">
                          Hourly rainfall · mm/h
                        </option>
                        <option value="wind">Wind speed · km/h</option>
                      </select>
                    </label>
                    <label className="history-hour-select">
                      FORECAST VALID HOUR
                      <select
                        aria-label="Forecast valid hour"
                        value={selectedHistoryHour}
                        onChange={(e) => setHistoryValidHour(+e.target.value)}
                      >
                        {validHistoryHours.map((t) => (
                          <option key={t} value={t}>
                            {time(t, track.timezone, true)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      className="button secondary"
                      disabled={!history.length || historyLoading}
                      onClick={exportHistory}
                    >
                      <ArrowDownToLine size={14} />
                      Export history
                    </button>
                  </div>
                </div>
                {historyLoading ? (
                  <div className="empty-state">
                    <Loader2 className="spin" size={24} />
                    <p>Loading recorded snapshots…</p>
                  </div>
                ) : hasHistoryEvolution ? (
                  <>
                    <div className="history-chart">
                      <ResponsiveContainer
                        width="100%"
                        height="100%"
                        initialDimension={{ width: 320, height: 185 }}
                      >
                        <LineChart
                          data={historyByFetch}
                          margin={{ top: 15, right: 20, left: 0, bottom: 0 }}
                        >
                          <CartesianGrid stroke="#ffffff0c" vertical={false} />
                          <XAxis
                            dataKey="time"
                            type="number"
                            domain={["dataMin", "dataMax"]}
                            scale="time"
                            tickFormatter={(v) => time(v, track.timezone)}
                            stroke="#58616b"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                          />
                          <YAxis
                            stroke="#58616b"
                            fontSize={10}
                            unit={historyUnit}
                            tickLine={false}
                            axisLine={false}
                          />
                          <Tooltip content={<ChartTip tz={track.timezone} />} />
                          {historySeries.map(({ id, points }, i) => (
                            <Line
                              key={id}
                              data={points}
                              dataKey="value"
                              name={`${data?.forecasts.find((f) => f.id === id)?.name || id} · ${historyUnit}`}
                              stroke={
                                data?.forecasts.find((f) => f.id === id)
                                  ?.color ||
                                ["#e2fa76", "#91b9ec", "#bd9de5", "#e9bd76"][
                                  i % 4
                                ]
                              }
                              strokeWidth={2}
                              dot={{ r: 3 }}
                              connectNulls={false}
                            />
                          ))}
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                    <p className="chart-note">
                      Each point is a real fetched prediction for the same
                      selected valid hour. Lines show how each source changed
                      its {historyLabel} forecast ({historyUnit}). The
                      horizontal axis is fetch time; this is not observed
                      weather or an accuracy score.
                    </p>
                  </>
                ) : (
                  <Empty
                    title={
                      historyByFetch.length
                        ? "Your history is beginning."
                        : "No logged history yet."
                    }
                    detail={`Forecast evolution needs at least two fetched ${historyLabel} values from the same source for this valid hour. ${historyMessage || "Snapshots accumulate from real fetches on this device."}`}
                  />
                )}
              </section>
              <div className="section-label">
                CONNECTION STATUS{" "}
                <span>
                  {data?.statuses.filter((s) => s.status === "ok").length || 0}{" "}
                  sources responding
                </span>
              </div>
              <div className="connection-list">
                {data?.statuses.map((s) => (
                  <div key={s.id} className="connection-row">
                    <span className={`connection-symbol ${s.status}`}>
                      <span className="tiny-dot" />
                    </span>
                    <strong>{s.name}</strong>
                    <span className="connection-message">{s.message}</span>
                    <span
                      className={`status-pill ${s.status === "ok" ? "" : s.status === "unconfigured" ? "neutral" : "amber"}`}
                    >
                      {s.status === "ok"
                        ? "Available"
                        : s.status === "cached"
                          ? "Saved forecast"
                          : s.status === "unconfigured"
                            ? "Optional · not configured"
                            : "Unavailable"}
                    </span>
                  </div>
                ))}
              </div>
              <div className="sources-grid">
                {data?.forecasts.map((f) => (
                  <SourceCard
                    key={f.id}
                    forecast={f}
                    disabled={disabled.includes(f.id)}
                    toggle={() => toggleSource(f.id)}
                    tz={track.timezone}
                  />
                ))}
              </div>
              <section className="panel methodology">
                <div className="panel-head">
                  <div>
                    <div className="eyebrow">HOW TO READ PITWALL</div>
                    <h2>Useful evidence. Visible limits.</h2>
                  </div>
                  <Info size={18} className="muted" />
                </div>
                <div className="method-grid">
                  <div>
                    <span>01 / CONSENSUS</span>
                    <h3>One model family, one vote.</h3>
                    <p>
                      Related services are grouped. Each family’s available
                      outputs are summarized by their median for an hour; the
                      median across families describes the center. Wet vote is
                      the fraction of reporting families at or above your rain
                      threshold. It is not a calibrated rain probability.
                    </p>
                  </div>
                  <div>
                    <span>02 / TIME & RAIN</span>
                    <h3>Hourly forecasts, local clock.</h3>
                    <p>
                      Series are aligned to the same UTC valid times and shown
                      in the selected circuit’s timezone. Precipitation is an
                      hourly amount. Providers are normalized to the following
                      interval: 14:00 rain describes 14:00–15:00. Instantaneous
                      fields such as air temperature remain at the hour
                      timestamp. Exact shower arrival is not known.
                    </p>
                  </div>
                  <div>
                    <span>03 / RADAR</span>
                    <h3>Recent observation, not prediction.</h3>
                    <p>
                      RainViewer supplies recent radar frames. The frame
                      timestamp is not necessarily each underlying radar scan’s
                      time. Native zoom 7 limits detail; zooming closer cannot
                      resolve the weather at individual corners. Coverage gaps
                      and delayed scans matter.
                    </p>
                  </div>
                  <div>
                    <span>04 / THE SURFACE</span>
                    <h3>Track conditions need context.</h3>
                    <p>
                      Air temperature, dew point and rain signals do not measure
                      grip, surface water, drying rate, or track temperature.
                      Compare radar with trackside observations and official
                      race-control information.
                    </p>
                  </div>
                </div>
                {data?.notes?.length ? (
                  <div className="provider-notes">
                    {data.notes.map((note, i) => (
                      <p key={i}>
                        <Info size={12} />
                        {note}
                      </p>
                    ))}
                  </div>
                ) : null}
                <div className="attributions">
                  <a
                    href="https://open-meteo.com/en/docs"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open-Meteo documentation ↗
                  </a>
                  <a
                    href="https://api.met.no/doc/ForecastJSON"
                    target="_blank"
                    rel="noreferrer"
                  >
                    MET Norway documentation ↗
                  </a>
                  <a
                    href="https://www.rainviewer.com/api/weather-maps-api.html"
                    target="_blank"
                    rel="noreferrer"
                  >
                    RainViewer documentation ↗
                  </a>
                  <a
                    href="https://www.openstreetmap.org/copyright"
                    target="_blank"
                    rel="noreferrer"
                  >
                    OpenStreetMap attribution ↗
                  </a>
                </div>
              </section>
            </>
          )}
          <footer className="footer">
            <span className="footer-brand">
              <span className="tiny-dot lime" />
              PITWALL{" "}
              <small>Weather intelligence for your time on track.</small>
            </span>
            <span>
              Forecasts ≠ trackside measurements{" "}
              <span className="dot-separator">/</span>
              <button onClick={() => setView("history")}>
                Sources & methodology <ArrowRight size={12} />
              </button>
            </span>
          </footer>
        </div>
      </main>
      {searchOpen && (
        <div className="modal-scrim" onClick={() => setSearchOpen(false)}>
          <section
            className="modal search-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="search-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-head">
              <div>
                <div className="eyebrow">EXPAND YOUR WEATHER DESK</div>
                <h2 id="search-title">Find your circuit.</h2>
              </div>
              <button
                className="icon-button"
                onClick={() => setSearchOpen(false)}
                aria-label="Close location search"
              >
                <X size={19} />
              </button>
            </div>
            <div className="modal-tabs">
              <button
                className={!coordinateMode ? "active" : ""}
                onClick={() => setCoordinateMode(false)}
              >
                Search locations
              </button>
              <button
                className={coordinateMode ? "active" : ""}
                onClick={() => setCoordinateMode(true)}
              >
                Coordinates
              </button>
            </div>
            {coordinateMode ? (
              <div className="form-body">
                <label>
                  LOCATION NAME
                  <input
                    autoFocus
                    value={coordName}
                    maxLength={80}
                    onChange={(e) => setCoordName(e.target.value)}
                    placeholder="Your circuit or test location"
                  />
                </label>
                <div className="form-pair">
                  <label>
                    LATITUDE
                    <input
                      type="number"
                      min="-90"
                      max="90"
                      step="any"
                      value={coordLat}
                      onChange={(e) => setCoordLat(e.target.value)}
                      placeholder="37.2319"
                    />
                  </label>
                  <label>
                    LONGITUDE
                    <input
                      type="number"
                      min="-180"
                      max="180"
                      step="any"
                      value={coordLon}
                      onChange={(e) => setCoordLon(e.target.value)}
                      placeholder="−8.6267"
                    />
                  </label>
                </div>
                <label>
                  TIMEZONE
                  <input
                    value={coordTz}
                    onChange={(e) => setCoordTz(e.target.value)}
                    placeholder="Europe/Paris"
                  />
                </label>
                {searchError && <p className="inline-warning">{searchError}</p>}
                <button className="button full-width" onClick={addCoordinates}>
                  <Plus size={15} />
                  Add location
                </button>
                <p className="field-note">
                  Use the circuit’s local IANA timezone. Forecast and radar are
                  requested for these coordinates.
                </p>
              </div>
            ) : (
              <>
                <div className="search-input">
                  <Search size={18} />
                  <input
                    autoFocus
                    placeholder="Search a circuit, city or region…"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                  {searching && <Loader2 size={16} className="spin" />}
                </div>
                <div className="search-results">
                  <div className="search-group-label">
                    {query ? "CIRCUITS" : "POPULAR CIRCUITS"}
                  </div>
                  {filteredTracks.length ? (
                    filteredTracks.map((t) => (
                      <button key={t.id} onClick={() => choose(t)}>
                        <span className="search-pin">
                          <Flag size={16} />
                        </span>
                        <span>
                          <strong>{t.name}</strong>
                          <small>
                            {t.country}
                            {t.lengthKm ? ` · ${t.lengthKm} km` : ""}
                          </small>
                        </span>
                        {favorites.some((f) => f.id === t.id) ? (
                          <Check size={15} className="text-lime" />
                        ) : (
                          <Plus size={15} />
                        )}
                      </button>
                    ))
                  ) : (
                    <p className="search-no-results">
                      No matching circuit in the curated list. Try the city
                      search below or enter coordinates.
                    </p>
                  )}
                  {query.length >= 2 && (
                    <>
                      <div className="search-group-label">
                        PLACES · OPEN-METEO GEOCODING
                      </div>
                      {searchResults.map((t) => (
                        <button key={t.id} onClick={() => choose(t)}>
                          <span className="search-pin">
                            <MapPin size={16} />
                          </span>
                          <span>
                            <strong>{t.name}</strong>
                            <small>
                              {t.country} · {t.lat.toFixed(3)},{" "}
                              {t.lon.toFixed(3)}
                            </small>
                          </span>
                          <Plus size={15} />
                        </button>
                      ))}
                      {!searching && !searchResults.length && (
                        <p className="search-no-results">
                          {searchError ||
                            "No places found. Enter exact coordinates for a circuit."}
                        </p>
                      )}
                    </>
                  )}
                </div>
              </>
            )}
            <div className="modal-footnote">
              <ShieldCheck size={13} />
              Saved locations stay on this browser. City search may not locate
              the exact track.
            </div>
          </section>
        </div>
      )}
      {settings && (
        <div className="modal-scrim" onClick={() => setSettings(false)}>
          <section
            className="modal preferences-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="preferences-title"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-head">
              <div>
                <div className="eyebrow">MAKE THE COMPARISON YOURS</div>
                <h2 id="preferences-title">Weather preferences</h2>
              </div>
              <button
                className="icon-button"
                onClick={() => setSettings(false)}
                aria-label="Close preferences"
              >
                <X size={19} />
              </button>
            </div>
            <div className="form-body">
              <label>
                WET VOTE THRESHOLD
                <select
                  value={threshold}
                  onChange={(e) => setThreshold(+e.target.value)}
                >
                  <option value={0.1}>0.1 mm per hour · trace-sensitive</option>
                  <option value={0.2}>0.2 mm per hour</option>
                  <option value={0.5}>0.5 mm per hour</option>
                  <option value={1}>1.0 mm per hour</option>
                </select>
              </label>
              <p className="field-note">
                A family votes wet when its hourly precipitation reaches this
                amount. This is an analytical threshold, not a tyre or grip
                recommendation.
              </p>
              <div className="settings-section-label">
                ENABLED FORECAST SOURCES
              </div>
              {data?.forecasts.length ? (
                data.forecasts.map((f) => (
                  <label className="source-toggle" key={f.id}>
                    <span
                      className="tiny-dot"
                      style={{ background: f.color }}
                    />
                    <span>
                      <strong>{f.name}</strong>
                      <small>
                        {f.provider} · {f.family}
                      </small>
                    </span>
                    <input
                      type="checkbox"
                      checked={!disabled.includes(f.id)}
                      onChange={() => toggleSource(f.id)}
                    />
                  </label>
                ))
              ) : (
                <p className="field-note">
                  Sources appear after a successful forecast fetch.
                </p>
              )}
              <div className="settings-section-label">SAVED CIRCUITS</div>
              {favorites.map((f) => (
                <div className="favorite-setting" key={f.id}>
                  <span>{f.name}</span>
                  <button
                    disabled={favorites.length <= 1 || f.id === track.id}
                    onClick={() =>
                      setFavorites((a) => a.filter((x) => x.id !== f.id))
                    }
                    aria-label={`Remove ${f.name} from saved circuits`}
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              <div className="settings-section-label">DEVICE BACKUP</div>
              <p className="field-note">
                Export your circuits, weather preferences and {sessions.length}{" "}
                saved session{sessions.length === 1 ? "" : "s"}. Import adds
                missing circuits and sessions, keeps existing plans, and applies
                the backup’s preferences. Forecast history and provider caches
                are separate; export forecast history as CSV from History &amp;
                sources.
              </p>
              <div className="backup-actions">
                <button
                  className="button secondary"
                  onClick={() => {
                    download(
                      `pitwall-backup-${day(now, "UTC")}.json`,
                      JSON.stringify(
                        createBackup(preferences, sessions),
                        null,
                        2,
                      ),
                      "application/json",
                    );
                    setBackupMessage(
                      "Device backup downloaded. Keep the file somewhere you can recover it.",
                    );
                  }}
                >
                  <ArrowDownToLine size={14} />
                  Export backup
                </button>
                <button
                  className="button secondary"
                  onClick={() => backupInput.current?.click()}
                >
                  <Upload size={14} />
                  Import backup
                </button>
                <input
                  ref={backupInput}
                  type="file"
                  accept="application/json,.json"
                  className="sr-only"
                  tabIndex={-1}
                  aria-label="Import Pitwall device backup"
                  onChange={(e) => void importBackup(e.target.files?.[0])}
                />
              </div>
              {backupMessage && (
                <p className="backup-feedback" role="status">
                  {backupMessage}
                </p>
              )}
              <button
                className="button full-width"
                onClick={() => setSettings(false)}
              >
                Done <Check size={14} />
              </button>
              <p className="field-note">
                Preferences and sessions are stored on this device. Forecast
                snapshots are recorded in this browser’s local database when
                storage is available. They do not sync between devices.
              </p>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
function SourceCard({
  forecast: f,
  disabled,
  toggle,
  tz,
}: {
  forecast: Forecast;
  disabled: boolean;
  toggle: () => void;
  tz: string;
}) {
  return (
    <article className={`panel source-card ${disabled ? "disabled" : ""}`}>
      <div className="source-card-top">
        <span className="source-swatch" style={{ background: f.color }} />
        <span className="source-provider">{f.provider}</span>
        <label className="toggle-switch">
          <input
            type="checkbox"
            checked={!disabled}
            onChange={toggle}
            aria-label={`Include ${f.name} in comparison`}
          />
          <span />
        </label>
      </div>
      <h3>{f.name}</h3>
      <div className="source-detail">
        <span>MODEL FAMILY</span>
        <strong>{f.family}</strong>
      </div>
      <div className="source-detail">
        <span>GRID / RESOLUTION</span>
        <strong>{f.resolution}</strong>
      </div>
      <div className="source-detail">
        <span>DELIVERED THROUGH</span>
        <strong>{f.transport}</strong>
      </div>
      <div className="source-detail">
        <span>FETCHED · LOCAL TIME</span>
        <strong>{time(new Date(f.fetchedAt).getTime() / 1000, tz)}</strong>
      </div>
      {f.caveat && (
        <p className="source-caveat">
          <Info size={12} />
          {f.caveat}
        </p>
      )}
    </article>
  );
}
