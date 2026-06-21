"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  Sparkles,
  Map as MapIcon,
  Layers,
  Play,
  Pause,
  TrendingUp,
  TableProperties,
  ShieldAlert,
  Droplets,
  Activity,
  Award,
  Search,
  Key,
  CloudSun,
  MapPin,
  Thermometer,
  Wind,
  CloudRain,
  Compass,
  Satellite,
  Zap,
  Globe,
  Radio,
  ChevronRight,
  BarChart3,
  Cpu,
} from "lucide-react";

import * as api from "../lib/api";
import CanalCommandTwin from "../components/CanalCommandTwin";
import IrrigationAdvisory from "../components/IrrigationAdvisory";
import PredictiveCharts from "../components/PredictiveCharts";
import AlertManager from "../components/AlertManager";
import AICopilotPanel from "../components/AICopilotPanel";
import CropSuitability from "../components/CropSuitability";
import InsuranceAuditor from "../components/InsuranceAuditor";

const MapboxDashboard = dynamic(
  () => import("../components/MapboxDashboard"),
  {
    ssr: false,
    loading: () => (
      <div className="h-[480px] w-full flex flex-col items-center justify-center gap-4 rounded-xl map-container bg-[var(--bg-surface)]">
        <div className="relative">
          <div className="w-12 h-12 rounded-full border-2 border-indigo-500/30 border-t-indigo-400 animate-spin" />
          <Satellite className="w-5 h-5 text-indigo-400 absolute inset-0 m-auto" />
        </div>
        <div className="text-xs text-[var(--text-muted)] font-medium tracking-wide">
          Initializing Earth Observation Feed...
        </div>
      </div>
    ),
  }
);

/* ── Stat Card Helper ─────────────────────────────────────────── */
interface StatCardProps {
  label: string;
  value: string | number;
  sub: string;
  icon: React.ReactNode;
  accentColor: string;
  glowColor: string;
  trend?: string;
}

function StatCard({ label, value, sub, icon, accentColor, glowColor, trend }: StatCardProps) {
  return (
    <div className="card-stat p-5">
      {/* Accent line top */}
      <div
        className="absolute top-0 left-6 right-6 h-px opacity-60"
        style={{ background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)` }}
      />
      <div className="flex items-start justify-between">
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
            {label}
          </div>
          <div
            className="text-2xl font-black tracking-tight"
            style={{ color: accentColor, textShadow: `0 0 20px ${glowColor}` }}
          >
            {value}
          </div>
          <div className="text-[10px] text-[var(--text-muted)] leading-relaxed truncate">{sub}</div>
        </div>
        <div
          className="ml-3 w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
          style={{ background: `${glowColor}18`, border: `1px solid ${glowColor}30` }}
        >
          {icon}
        </div>
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1.5">
          <TrendingUp className="w-3 h-3 text-emerald-400" />
          <span className="text-[10px] text-emerald-400 font-semibold">{trend}</span>
        </div>
      )}
    </div>
  );
}

/* ── Layer Toggle Button ──────────────────────────────────────── */
interface LayerBtnProps {
  active: boolean;
  onClick: () => void;
  label: string;
  activeClass: string;
}
function LayerBtn({ active, onClick, label, activeClass }: LayerBtnProps) {
  return (
    <button
      onClick={onClick}
      className={`text-[10px] font-bold px-3.5 py-1.5 rounded-lg border transition-all duration-200 ${
        active ? activeClass : "bg-transparent border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:border-[var(--border-subtle)]"
      }`}
    >
      {label}
    </button>
  );
}

/* ── Panel Section Title ─────────────────────────────────────── */
function PanelTitle({ icon, title, badge }: { icon: React.ReactNode; title: string; badge?: string }) {
  return (
    <div className="flex items-center gap-2.5 mb-1">
      <div className="flex items-center gap-2">
        {icon}
        <h3 className="font-bold text-[var(--text-primary)] text-sm tracking-tight">{title}</h3>
      </div>
      {badge && <span className="badge-info">{badge}</span>}
    </div>
  );
}

/* ── Main Page ───────────────────────────────────────────────── */
export default function DashboardPage() {
  const [fieldsGeojson, setFieldsGeojson] = useState<any>(null);
  const [canalsGeojson, setCanalsGeojson] = useState<any>(null);
  const [commandGeojson, setCommandGeojson] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [villageReports, setVillageReports] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null);
  const [fieldAdvisories, setFieldAdvisories] = useState<any[]>([]);
  const [activeLayer, setActiveLayer] = useState<"crops" | "stress" | "moisture">("crops");
  const [satelliteOverlay, setSatelliteOverlay] = useState<"none" | "ndvi" | "ndwi" | "sar">("none");

  const [activeLocationInfo, setActiveLocationInfo] = useState<any>(null);
  const [flyToCenter, setFlyToCenter] = useState<[number, number] | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [geminiKey, setGeminiKey] = useState("");
  const [activeSideTab, setActiveSideTab] = useState<"twin" | "location">("twin");

  const [timeStep, setTimeStep] = useState<number>(5);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [copilotHighlight, setCopilotHighlight] = useState<any>(null);
  const [advLoading, setAdvLoading] = useState<boolean>(false);
  const [classLoading, setClassLoading] = useState<boolean>(false);

  useEffect(() => {
    async function loadData() {
      const [summaryData, fields, canals, command, reports, alertList] =
        await Promise.all([
          api.getSummary(),
          api.getFieldsGeoJSON(),
          api.getCanalsGeoJSON(),
          api.getCommandAreasGeoJSON(),
          api.getVillageReports(),
          api.getAlerts(),
        ]);
      setSummary(summaryData);
      setFieldsGeojson(fields);
      setCanalsGeojson(canals);
      setCommandGeojson(command);
      setVillageReports(reports);
      setAlerts(alertList);
      const savedKey = localStorage.getItem("gemini_api_key");
      if (savedKey) setGeminiKey(savedKey);
    }
    loadData();
  }, []);

  useEffect(() => {
    if (selectedFieldId !== null) {
      api.getAdvisories(selectedFieldId).then(setFieldAdvisories);
    }
  }, [selectedFieldId]);

  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => setTimeStep((p) => (p + 1) % 6), 1500);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  const handleGeocodeSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery)}&format=json&limit=1`,
        { headers: { "User-Agent": "AgriSense-GIS-Satellite-Intelligence-v2" } }
      );
      const data = await res.json();
      if (data?.length > 0) {
        const { lat: rawLat, lon: rawLon, display_name } = data[0];
        const lat = parseFloat(rawLat), lon = parseFloat(rawLon);
        setFlyToCenter([lat, lon]);
        const wRes = await fetch(
          `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min,rain_sum,et0_fao_evapotranspiration&timezone=auto`
        );
        const wData = await wRes.json();
        setActiveLocationInfo({
          lat, lon,
          address: display_name,
          weather: {
            temp: wData.current_weather?.temperature ?? 25,
            windSpeed: wData.current_weather?.windspeed ?? 10,
            windDirection: wData.current_weather?.winddirection ?? 0,
            weatherCode: wData.current_weather?.weathercode ?? 0,
            dailyMaxTemp: wData.daily?.temperature_2m_max?.[0] ?? 28,
            dailyMinTemp: wData.daily?.temperature_2m_min?.[0] ?? 20,
            rainSum: wData.daily?.rain_sum?.[0] ?? 0,
            et0: wData.daily?.et0_fao_evapotranspiration?.[0] ?? 4.2,
          },
        });
        setActiveSideTab("location");
      } else {
        alert("Location not found. Try a city, state, or country name.");
      }
    } catch (err) {
      console.error("Geocoding error", err);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSaveGeminiKey = (val: string) => {
    setGeminiKey(val);
    localStorage.setItem("gemini_api_key", val);
  };

  const handleTriggerClassification = async (fieldId: number) => {
    setClassLoading(true);
    const result = await api.triggerClassification(fieldId);
    setFieldsGeojson((prev: any) => {
      if (!prev) return prev;
      return {
        ...prev,
        features: prev.features.map((f: any) =>
          f.id === fieldId ? { ...f, properties: { ...f.properties, crop_type: result.crop_type } } : f
        ),
      };
    });
    setClassLoading(false);
  };

  const handleTriggerAdvisory = async (fieldId: number) => {
    setAdvLoading(true);
    const result = await api.triggerAdvisory(fieldId);
    setFieldAdvisories((p) => [result, ...p]);
    setAdvLoading(false);
  };

  const handleMarkAlertRead = async (alertId: number) => {
    await api.markAlertRead(alertId);
    setAlerts((p) => p.filter((a) => a.id !== alertId));
  };

  const handleLocationSelected = (info: any) => {
    setActiveLocationInfo(info);
    setActiveSideTab("location");
  };

  const selectedField = fieldsGeojson?.features?.find((f: any) => f.id === selectedFieldId);
  const stepLabels = ["Day −10", "Day −8", "Day −6", "Day −4", "Day −2", "Latest"];

  const overlayOptions: Array<{ id: "none" | "ndvi" | "ndwi" | "sar"; label: string; color: string }> = [
    { id: "none", label: "None", color: "" },
    { id: "ndvi", label: "NDVI", color: "text-emerald-400 border-emerald-600/50 bg-emerald-900/30" },
    { id: "ndwi", label: "NDWI", color: "text-sky-400 border-sky-600/50 bg-sky-900/30" },
    { id: "sar", label: "SAR", color: "text-violet-400 border-violet-600/50 bg-violet-900/30" },
  ];

  return (
    <div className="min-h-screen flex flex-col" style={{ background: "var(--bg-base)" }}>
      {/* ── HEADER ──────────────────────────────────────────────── */}
      <header className="glass-header sticky top-0 z-[1000] px-6 py-0">
        <div className="max-w-[1600px] mx-auto w-full">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 py-4">
            {/* Brand */}
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg"
                  style={{ boxShadow: "0 0 16px rgba(99,102,241,0.5)" }}>
                  <Satellite className="w-5 h-5 text-white" />
                </div>
                <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-400 border-2 border-[var(--bg-base)]"
                  style={{ boxShadow: "0 0 6px rgba(16,185,129,0.8)" }} />
              </div>
              <div>
                <div className="flex items-center gap-2.5">
                  <h1 className="font-black text-base tracking-tight">
                    <span className="gradient-text-brand">AgriSense AI</span>
                    <span className="text-[var(--text-muted)] font-normal ml-1.5">Platform</span>
                  </h1>
                  <span className="badge-info">v2 GLOBAL</span>
                </div>
                <p className="text-[10px] text-[var(--text-muted)] mt-0.5 hidden sm:block">
                  Satellite Intelligence · FAO-56 Precision Irrigation · Gemini AI Copilot
                </p>
              </div>
            </div>

            {/* Status row */}
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                style={{ background: "rgba(16,185,129,0.08)", border: "1px solid rgba(16,185,129,0.15)" }}>
                <div className="live-dot" />
                <span className="text-[10px] font-bold text-emerald-400 tracking-wide">OSM GEOCODER LIVE</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                style={{ background: "rgba(56,189,248,0.08)", border: "1px solid rgba(56,189,248,0.15)" }}>
                <Radio className="w-3 h-3 text-sky-400" />
                <span className="text-[10px] font-bold text-sky-400 tracking-wide">OPEN-METEO SYNC</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.15)" }}>
                <Cpu className="w-3 h-3 text-indigo-400" />
                <span className="text-[10px] font-bold text-indigo-400 tracking-wide">AI COPILOT READY</span>
              </div>
            </div>
          </div>

          {/* Toolbar sub-bar */}
          <div className="flex flex-col sm:flex-row gap-3 pb-3 pt-0 border-t border-[var(--border-dim)]">
            <form onSubmit={handleGeocodeSearch} className="relative flex-1 max-w-xl pt-3">
              <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-[22px]" />
              <input
                type="text"
                placeholder="Search any global location, city, country or coordinates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-dark w-full py-2 pl-9 pr-24 text-[12px]"
              />
              <button
                type="submit"
                disabled={searchLoading}
                className="btn-primary absolute right-1.5 top-[14px]"
              >
                {searchLoading ? (
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-3 rounded-full border border-white/40 border-t-white animate-spin" />
                    Flying
                  </span>
                ) : (
                  <span className="flex items-center gap-1">
                    <Globe className="w-3 h-3" /> Search
                  </span>
                )}
              </button>
            </form>

            <div className="flex items-center gap-2 max-w-xs pt-3">
              <div className="flex items-center gap-2 input-dark px-3 py-2 flex-1">
                <Key className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                <input
                  type="password"
                  placeholder="Gemini API Key (optional)..."
                  value={geminiKey}
                  onChange={(e) => handleSaveGeminiKey(e.target.value)}
                  className="w-full bg-transparent border-none text-[11px] text-[var(--text-secondary)] placeholder:text-[var(--text-muted)] focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* ── MAIN CONTENT ─────────────────────────────────────────── */}
      <main className="flex-1 px-6 py-6 space-y-6 max-w-[1600px] mx-auto w-full">
        {/* ── ROW 0: KPI STATS ─────────────────────────────────── */}
        <section className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          <StatCard
            label="Hectares Under Command"
            value="1,875 ha"
            sub="Sirhind Command Area Active"
            icon={<MapIcon className="w-5 h-5 text-indigo-400" />}
            accentColor="#818CF8"
            glowColor="#6366F1"
            trend="+2.3% from last season"
          />
          <StatCard
            label="Avg Water Stress Index"
            value={summary?.average_stress_score ?? "0.24"}
            sub="FAO-56 Crop Depletion Score [0–1]"
            icon={<ShieldAlert className="w-5 h-5 text-rose-400" />}
            accentColor="#FB7185"
            glowColor="#F43F5E"
          />
          <StatCard
            label="Canal Intake Flow"
            value={`${summary?.active_command_canal_flow_cusec ?? "1,250"} ℓ/s`}
            sub="Sirhind Feeder Distributary"
            icon={<Droplets className="w-5 h-5 text-sky-400" />}
            accentColor="#38BDF8"
            glowColor="#0EA5E9"
            trend="Stable flow detected"
          />
          <StatCard
            label="Precision Water Saved"
            value={`${summary?.total_water_saved_m3 ?? "3,840"} m³`}
            sub="Via AI irrigation depth optimization"
            icon={<Award className="w-5 h-5 text-emerald-400" />}
            accentColor="#34D399"
            glowColor="#10B981"
            trend="↑ 18% vs. baseline"
          />
        </section>

        {/* ── ROW 1: MAP + SIDE PANEL ──────────────────────────── */}
        <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Map column */}
          <div className="xl:col-span-2 space-y-4">
            <div className="card-premium p-4 space-y-4">
              {/* Map controls row 1 */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="section-header">
                  <Layers className="w-3.5 h-3.5 text-indigo-400" />
                  Observation Layer Control
                </div>
                <div className="flex gap-2 flex-wrap">
                  <LayerBtn
                    active={activeLayer === "crops"}
                    onClick={() => setActiveLayer("crops")}
                    label="🌾 Crop Types"
                    activeClass="bg-amber-600/25 border-amber-500/60 text-amber-300"
                  />
                  <LayerBtn
                    active={activeLayer === "stress"}
                    onClick={() => setActiveLayer("stress")}
                    label="⚠ Moisture Stress"
                    activeClass="bg-rose-600/25 border-rose-500/60 text-rose-300"
                  />
                  <LayerBtn
                    active={activeLayer === "moisture"}
                    onClick={() => setActiveLayer("moisture")}
                    label="💧 Soil Moisture"
                    activeClass="bg-sky-600/25 border-sky-500/60 text-sky-300"
                  />
                </div>
              </div>

              {/* Map controls row 2 — Satellite Overlays */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-[var(--border-dim)]">
                <div className="section-header">
                  <Satellite className="w-3.5 h-3.5 text-violet-400 animate-pulse" />
                  Satellite Spectral Overlay
                </div>
                <div className="flex gap-2">
                  {overlayOptions.map(({ id, label, color }) => (
                    <button
                      key={id}
                      onClick={() => setSatelliteOverlay(id)}
                      className={`text-[10px] font-bold px-3.5 py-1.5 rounded-lg border transition-all duration-200 ${
                        satelliteOverlay === id
                          ? color || "bg-[var(--bg-elevated)] border-[var(--border-subtle)] text-[var(--text-secondary)]"
                          : "bg-transparent border-[var(--border-dim)] text-[var(--text-muted)] hover:border-[var(--border-subtle)] hover:text-[var(--text-secondary)]"
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              {/* The Map */}
              <div className="map-container">
                <MapboxDashboard
                  fieldsGeojson={fieldsGeojson}
                  canalsGeojson={canalsGeojson}
                  commandGeojson={commandGeojson}
                  activeLayer={activeLayer}
                  satelliteOverlay={satelliteOverlay}
                  timeStep={timeStep}
                  selectedFieldId={selectedFieldId}
                  onSelectField={setSelectedFieldId}
                  onTriggerClassification={handleTriggerClassification}
                  onTriggerAdvisory={handleTriggerAdvisory}
                  copilotHighlightGeojson={copilotHighlight}
                  onLocationSelected={handleLocationSelected}
                  flyToCenter={flyToCenter}
                />
              </div>

              {/* Temporal Timeline */}
              <div
                className="p-3.5 rounded-xl flex items-center gap-4"
                style={{ background: "var(--bg-surface)", border: "1px solid var(--border-dim)" }}
              >
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className={`p-2.5 rounded-xl transition-all duration-200 flex-shrink-0 ${
                    isPlaying
                      ? "bg-rose-600/20 border border-rose-500/40 text-rose-400 hover:bg-rose-600/30"
                      : "bg-indigo-600/20 border border-indigo-500/40 text-indigo-400 hover:bg-indigo-600/30"
                  }`}
                  title={isPlaying ? "Pause Playback" : "Start Temporal Playback"}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-current" />}
                </button>

                <div className="flex-1 space-y-1.5">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold uppercase tracking-widest text-[var(--text-muted)]">
                      Temporal Composite Timeline
                    </span>
                    <span
                      className="text-[11px] font-black text-indigo-400"
                      style={{ textShadow: "0 0 12px rgba(99,102,241,0.6)" }}
                    >
                      {stepLabels[timeStep]}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="5"
                    value={timeStep}
                    onChange={(e) => setTimeStep(parseInt(e.target.value))}
                    className="w-full"
                    style={{ accentColor: "#6366F1" }}
                  />
                  <div className="flex justify-between text-[9px] text-[var(--text-muted)] font-medium">
                    <span>Sowing</span>
                    <span>Emergence</span>
                    <span>Vegetative</span>
                    <span>Latest</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Side Panel */}
          <div className="flex flex-col gap-4">
            {/* Tab controller */}
            <div className="tab-bar">
              <button
                className={`tab-btn ${activeSideTab === "twin" ? "active" : ""}`}
                onClick={() => setActiveSideTab("twin")}
              >
                <div className="flex items-center justify-center gap-1.5">
                  <Activity className="w-3.5 h-3.5" />
                  Canal Twin
                </div>
              </button>
              <button
                className={`tab-btn ${activeSideTab === "location" ? "active" : ""}`}
                onClick={() => setActiveSideTab("location")}
              >
                <div className="flex items-center justify-center gap-1.5">
                  <CloudSun className="w-3.5 h-3.5" />
                  Weather
                  {activeLocationInfo && (
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 ml-0.5" />
                  )}
                </div>
              </button>
            </div>

            {/* Tab content */}
            {activeSideTab === "twin" ? (
              <CanalCommandTwin summary={summary} fieldsGeojson={fieldsGeojson} />
            ) : (
              <div className="card-premium p-5 flex-1 flex flex-col min-h-[320px]">
                {!activeLocationInfo ? (
                  <div className="flex flex-col items-center justify-center flex-1 text-center gap-3 py-12">
                    <div
                      className="w-14 h-14 rounded-2xl flex items-center justify-center"
                      style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.15)" }}
                    >
                      <MapPin className="w-7 h-7 text-indigo-400/60" />
                    </div>
                    <div>
                      <div className="text-sm font-bold text-[var(--text-secondary)] mb-1">
                        No location selected
                      </div>
                      <div className="text-[11px] text-[var(--text-muted)] max-w-[200px] leading-relaxed mx-auto">
                        Click anywhere on the map or use the search bar to load live weather data.
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4 animate-slide-up">
                    {/* Location header */}
                    <div>
                      <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-indigo-400 mb-2">
                        <MapPin className="w-3.5 h-3.5" />
                        Selected Location
                      </div>
                      <div className="text-[12px] text-[var(--text-secondary)] leading-relaxed line-clamp-2">
                        {activeLocationInfo.address}
                      </div>
                      <div className="font-mono text-[10px] text-[var(--text-muted)] mt-1">
                        {activeLocationInfo.lat.toFixed(5)}°N, {activeLocationInfo.lon.toFixed(5)}°E
                      </div>
                    </div>

                    {/* Weather metrics */}
                    {activeLocationInfo.weather && (
                      <>
                        <div className="section-header">
                          <CloudSun className="w-3 h-3" />
                          Live Meteorology
                        </div>
                        <div className="grid grid-cols-2 gap-2.5">
                          <div className="metric-mini">
                            <div
                              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                              style={{ background: "rgba(244,63,94,0.1)", border: "1px solid rgba(244,63,94,0.2)" }}
                            >
                              <Thermometer className="w-4 h-4 text-rose-400" />
                            </div>
                            <div>
                              <div className="text-[9px] text-[var(--text-muted)] font-semibold">TEMPERATURE</div>
                              <div className="text-[13px] font-black text-[var(--text-primary)]">
                                {activeLocationInfo.weather.temp}°C
                              </div>
                            </div>
                          </div>
                          <div className="metric-mini">
                            <div
                              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                              style={{ background: "rgba(56,189,248,0.1)", border: "1px solid rgba(56,189,248,0.2)" }}
                            >
                              <Wind className="w-4 h-4 text-sky-400" />
                            </div>
                            <div>
                              <div className="text-[9px] text-[var(--text-muted)] font-semibold">WIND</div>
                              <div className="text-[13px] font-black text-[var(--text-primary)]">
                                {activeLocationInfo.weather.windSpeed} km/h
                              </div>
                            </div>
                          </div>
                          <div className="metric-mini">
                            <div
                              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                              style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)" }}
                            >
                              <CloudRain className="w-4 h-4 text-indigo-400" />
                            </div>
                            <div>
                              <div className="text-[9px] text-[var(--text-muted)] font-semibold">RAIN SUM</div>
                              <div className="text-[13px] font-black text-[var(--text-primary)]">
                                {activeLocationInfo.weather.rainSum} mm
                              </div>
                            </div>
                          </div>
                          <div className="metric-mini">
                            <div
                              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                              style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)" }}
                            >
                              <Compass className="w-4 h-4 text-emerald-400" />
                            </div>
                            <div>
                              <div className="text-[9px] text-[var(--text-muted)] font-semibold">REF ET0</div>
                              <div className="text-[13px] font-black text-[var(--text-primary)]">
                                {activeLocationInfo.weather.et0} mm/d
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* ET0 advisory callout */}
                        <div
                          className="p-3 rounded-xl text-[11px] leading-relaxed text-indigo-300"
                          style={{
                            background: "rgba(99,102,241,0.07)",
                            border: "1px solid rgba(99,102,241,0.2)",
                          }}
                        >
                          <div className="flex items-start gap-2">
                            <Zap className="w-3.5 h-3.5 text-indigo-400 mt-0.5 flex-shrink-0" />
                            <span>
                              Reference ET₀ is <b className="text-indigo-200">{activeLocationInfo.weather.et0} mm/day</b>. 
                              Query the AI Copilot below for precision irrigation scheduling at this location.
                            </span>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* ── ROW 2: ADVISORY + CHARTS + COPILOT ───────────────── */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <IrrigationAdvisory
            advisories={fieldAdvisories}
            selectedField={selectedField}
            onTriggerAdvisory={handleTriggerAdvisory}
            loading={advLoading}
          />
          <PredictiveCharts selectedField={selectedField} />
          <AICopilotPanel
            onCopilotHighlight={setCopilotHighlight}
            activeLocationInfo={activeLocationInfo}
          />
        </section>

        {/* ── ROW 3: VILLAGE TABLE + ALERTS ────────────────────── */}
        <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Village reports table */}
          <div className="xl:col-span-2 card-premium p-5">
            <PanelTitle
              icon={<TableProperties className="w-4.5 h-4.5 text-indigo-400" />}
              title="Village Moisture Stress Index"
              badge={`${villageReports.length} Villages`}
            />
            <p className="text-[10px] text-[var(--text-muted)] mb-4">
              Real-time FAO-56 crop depletion aggregates by village command unit
            </p>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Village</th>
                    <th>District</th>
                    <th className="text-center">Total Plots</th>
                    <th className="text-center">Stressed</th>
                    <th className="text-center">% Stress</th>
                    <th className="text-center">Avg Score</th>
                    <th className="text-center">Priority</th>
                  </tr>
                </thead>
                <tbody>
                  {villageReports.map((item, idx) => (
                    <tr key={idx}>
                      <td className="font-semibold text-[var(--text-primary)]">{item.village}</td>
                      <td>{item.district}</td>
                      <td className="text-center">{item.total_fields}</td>
                      <td className="text-center text-rose-400 font-bold">{item.stressed_fields}</td>
                      <td className="text-center font-bold text-rose-300">{item.pct_stressed.toFixed(0)}%</td>
                      <td className="text-center font-mono text-[var(--text-secondary)]">
                        {item.average_stress_score.toFixed(2)}
                      </td>
                      <td className="text-center">
                        <span
                          className={`chip font-bold ${
                            item.advisory_priority === "High"
                              ? "bg-rose-900/40 text-rose-300 border border-rose-700/50"
                              : item.advisory_priority === "Medium"
                              ? "bg-amber-900/40 text-amber-300 border border-amber-700/50"
                              : "bg-emerald-900/40 text-emerald-300 border border-emerald-700/50"
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              item.advisory_priority === "High"
                                ? "bg-rose-400"
                                : item.advisory_priority === "Medium"
                                ? "bg-amber-400"
                                : "bg-emerald-400"
                            }`}
                          />
                          {item.advisory_priority}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {villageReports.length === 0 && (
                <div className="py-12 text-center text-[var(--text-muted)] text-xs">
                  Loading village stress reports from backend...
                </div>
              )}
            </div>
          </div>

          {/* Alert Manager */}
          <AlertManager alerts={alerts} onMarkRead={handleMarkAlertRead} />
        </section>

        {/* ── ROW 4: CROP SUITABILITY + INSURANCE AUDITOR ──────── */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <CropSuitability locationInfo={activeLocationInfo} />
          <InsuranceAuditor selectedField={selectedField} />
        </section>
      </main>

      {/* ── FOOTER ─────────────────────────────────────────────── */}
      <footer
        className="mt-auto py-5 px-6 text-center"
        style={{ borderTop: "1px solid var(--border-dim)", background: "var(--bg-void)" }}
      >
        <div className="flex flex-col sm:flex-row items-center justify-center gap-2 text-[10px] text-[var(--text-muted)]">
          <span className="flex items-center gap-1.5">
            <Satellite className="w-3 h-3 text-indigo-400/50" />
            <span className="gradient-text-brand font-bold">AgriSense AI Systems</span>
          </span>
          <span className="hidden sm:block">·</span>
          <span>© {new Date().getFullYear()} All rights reserved</span>
          <span className="hidden sm:block">·</span>
          <span className="flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-violet-400/50" />
            Powered by Google DeepMind Advanced Agentic Coding
          </span>
        </div>
      </footer>
    </div>
  );
}
