"use client";

import React, { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { 
  Sparkles, 
  Map as MapIcon, 
  Layers, 
  Play, 
  Pause, 
  Calendar, 
  TrendingUp, 
  TableProperties, 
  ShieldAlert, 
  Info,
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
  Compass
} from "lucide-react";

import * as api from "../lib/api";
import CanalCommandTwin from "../components/CanalCommandTwin";
import IrrigationAdvisory from "../components/IrrigationAdvisory";
import PredictiveCharts from "../components/PredictiveCharts";
import AlertManager from "../components/AlertManager";
import AICopilotPanel from "../components/AICopilotPanel";
import CropSuitability from "../components/CropSuitability";
import InsuranceAuditor from "../components/InsuranceAuditor";

// Dynamically load Leaflet Map component to prevent window SSR crashes
const MapboxDashboard = dynamic(() => import("../components/MapboxDashboard"), { 
  ssr: false,
  loading: () => (
    <div className="h-[480px] w-full flex items-center justify-center bg-slate-950 border border-gray-900 rounded-xl">
      <div className="text-gray-400 animate-pulse text-xs">Loading Earth Observation Map...</div>
    </div>
  )
});

export default function DashboardPage() {
  // Top level GIS states
  const [fieldsGeojson, setFieldsGeojson] = useState<any>(null);
  const [canalsGeojson, setCanalsGeojson] = useState<any>(null);
  const [commandGeojson, setCommandGeojson] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [villageReports, setVillageReports] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  
  // Selected Context States
  const [selectedFieldId, setSelectedFieldId] = useState<number | null>(null);
  const [fieldAdvisories, setFieldAdvisories] = useState<any[]>([]);
  const [activeLayer, setActiveLayer] = useState<"crops" | "stress" | "moisture" >("crops");
  const [satelliteOverlay, setSatelliteOverlay] = useState<"none" | "ndvi" | "ndwi" | "sar">("none");
  
  // Global Geocoding & Weather States
  const [activeLocationInfo, setActiveLocationInfo] = useState<any>(null);
  const [flyToCenter, setFlyToCenter] = useState<[number, number] | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [geminiKey, setGeminiKey] = useState("");
  const [activeSideTab, setActiveSideTab] = useState<"twin" | "location">("twin");
  
  // Temporal Playback Slider States
  const [timeStep, setTimeStep] = useState<number>(5); // 0-5
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  
  // Highlighting states for AI Copilot
  const [copilotHighlight, setCopilotHighlight] = useState<any>(null);
  
  // Loading indicators
  const [advLoading, setAdvLoading] = useState<boolean>(false);
  const [classLoading, setClassLoading] = useState<boolean>(false);

  // Load initial telemetry from backend / fallback mock client
  useEffect(() => {
    async function loadData() {
      const summaryData = await api.getSummary();
      const fields = await api.getFieldsGeoJSON();
      const canals = await api.getCanalsGeoJSON();
      const command = await api.getCommandAreasGeoJSON();
      const reports = await api.getVillageReports();
      const alertList = await api.getAlerts();

      setSummary(summaryData);
      setFieldsGeojson(fields);
      setCanalsGeojson(canals);
      setCommandGeojson(command);
      setVillageReports(reports);
      setAlerts(alertList);

      // Load Gemini key if available
      const savedKey = localStorage.getItem("gemini_api_key");
      if (savedKey) setGeminiKey(savedKey);
    }
    loadData();
  }, []);

  // Sync field-specific advisory history on selection
  useEffect(() => {
    if (selectedFieldId !== null) {
      const loadFieldAdvisories = async () => {
        const list = await api.getAdvisories(selectedFieldId);
        setFieldAdvisories(list);
      };
      loadFieldAdvisories();
    }
  }, [selectedFieldId]);

  // Handle temporal playback loop
  useEffect(() => {
    let interval: any;
    if (isPlaying) {
      interval = setInterval(() => {
        setTimeStep((prev) => (prev + 1) % 6);
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Global Geocoding search handler (OSM Nominatim API)
  const handleGeocodeSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearchLoading(true);
    try {
      const searchUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery)}&format=json&limit=1`;
      const res = await fetch(searchUrl, {
        headers: { "User-Agent": "AgriSense-GIS-Satellite-Intelligence-v2" }
      });
      const data = await res.json();

      if (data && data.length > 0) {
        const result = data[0];
        const lat = parseFloat(result.lat);
        const lon = parseFloat(result.lon);
        setFlyToCenter([lat, lon]);

        // Automatically trigger weather and reverse geocoding lookup
        const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min,rain_sum,et0_fao_evapotranspiration&timezone=auto`;
        const weatherRes = await fetch(weatherUrl);
        const weatherData = await weatherRes.json();

        const locationInfo = {
          lat,
          lon,
          address: result.display_name,
          addressDetails: {},
          weather: {
            temp: weatherData.current_weather?.temperature || 25,
            windSpeed: weatherData.current_weather?.windspeed || 10,
            windDirection: weatherData.current_weather?.winddirection || 0,
            weatherCode: weatherData.current_weather?.weathercode || 0,
            dailyMaxTemp: weatherData.daily?.temperature_2m_max?.[0] || 28,
            dailyMinTemp: weatherData.daily?.temperature_2m_min?.[0] || 20,
            rainSum: weatherData.daily?.rain_sum?.[0] || 0.0,
            et0: weatherData.daily?.et0_fao_evapotranspiration?.[0] || 4.2
          }
        };

        setActiveLocationInfo(locationInfo);
        setActiveSideTab("location");
      } else {
        alert("Location not found. Try searching for cities, states, or country bounds.");
      }
    } catch (err) {
      console.error("Geocoding failed", err);
    } finally {
      setSearchLoading(false);
    }
  };

  // Save Gemini Key handler
  const handleSaveGeminiKey = (val: string) => {
    setGeminiKey(val);
    localStorage.setItem("gemini_api_key", val);
  };

  // Handle actions triggered from map popups
  const handleTriggerClassification = async (fieldId: number) => {
    setClassLoading(true);
    const result = await api.triggerClassification(fieldId);
    
    setFieldsGeojson((prevGeojson: any) => {
      if (!prevGeojson) return prevGeojson;
      const updatedFeatures = prevGeojson.features.map((feat: any) => {
        if (feat.id === fieldId) {
          return {
            ...feat,
            properties: {
              ...feat.properties,
              crop_type: result.crop_type,
            }
          };
        }
        return feat;
      });
      return { ...prevGeojson, features: updatedFeatures };
    });
    setClassLoading(false);
  };

  const handleTriggerAdvisory = async (fieldId: number) => {
    setAdvLoading(true);
    const result = await api.triggerAdvisory(fieldId);
    setFieldAdvisories(prev => [result, ...prev]);
    setAdvLoading(false);
  };

  const handleMarkAlertRead = async (alertId: number) => {
    await api.markAlertRead(alertId);
    setAlerts(prev => prev.filter(a => a.id !== alertId));
  };

  // Handle location clicked on Leaflet map
  const handleLocationSelected = (info: any) => {
    setActiveLocationInfo(info);
    setActiveSideTab("location");
  };

  const selectedField = fieldsGeojson?.features?.find((f: any) => f.id === selectedFieldId);
  const stepLabels = ["Day -10", "Day -8", "Day -6", "Day -4", "Day -2", "Latest (Observed)"];

  return (
    <div className="min-h-screen bg-darkBg text-gray-200 flex flex-col">
      {/* Top Banner Navigation */}
      <header className="border-b border-gray-900 bg-slate-950 bg-opacity-80 backdrop-blur-md sticky top-0 z-[1000] px-6 py-4 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Droplets className="w-6 h-6 text-indigo-400 animate-bounce" />
            <h1 className="font-extrabold text-lg tracking-tight text-white">
              AgriSense AI <span className="text-gray-400 font-normal">Platform</span>
            </h1>
            <span className="text-[10px] font-semibold bg-indigo-950 text-indigo-400 px-2 py-0.5 rounded border border-indigo-850 uppercase">
              v2.0.0 Global
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Global GIS Search, Crop Intelligence, FAO-56 Reference Weather & Gemini AI Copilot
          </p>
        </div>

        {/* Live Satellite status ticker */}
        <div className="flex flex-wrap items-center gap-4 text-xs bg-slate-900 border border-gray-800 rounded-lg px-4 py-2">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="font-semibold text-gray-450">OSM Geocoder:</span>
            <span className="text-emerald-400 font-bold">Online</span>
          </div>
          <div className="h-4 w-px bg-gray-800 hidden sm:block" />
          <div className="flex items-center gap-1.5">
            <Activity className="w-4 h-4 text-sky-400" />
            <span className="font-semibold text-gray-450">Open-Meteo Forecasts:</span>
            <span className="text-sky-400 font-bold">Synchronized</span>
          </div>
        </div>
      </header>

      {/* Global Toolbar Bar */}
      <section className="bg-slate-950 border-b border-gray-900 px-6 py-3 flex flex-col sm:flex-row justify-between items-center gap-3">
        {/* Nominatim Search Input */}
        <form onSubmit={handleGeocodeSearch} className="relative w-full sm:max-w-md">
          <input
            type="text"
            placeholder="Search global coordinates, cities, or states..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900 border border-gray-800 rounded-lg py-1.5 pl-9 pr-20 text-xs text-gray-200 placeholder-gray-550 focus:outline-none focus:border-indigo-650 transition"
          />
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2" />
          <button
            type="submit"
            disabled={searchLoading}
            className="absolute right-1.5 top-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 text-white text-[10px] font-bold py-1 px-3.5 rounded transition"
          >
            {searchLoading ? "Flying..." : "Search"}
          </button>
        </form>

        {/* Gemini Key Config */}
        <div className="flex items-center gap-2 w-full sm:max-w-xs bg-slate-900 border border-gray-800 rounded-lg px-2.5 py-1">
          <Key className="w-4 h-4 text-amber-500 flex-shrink-0" />
          <input
            type="password"
            placeholder="Enter Gemini API Key..."
            value={geminiKey}
            onChange={(e) => handleSaveGeminiKey(e.target.value)}
            className="w-full bg-transparent border-none text-xs text-gray-200 placeholder-gray-500 focus:outline-none"
          />
        </div>
      </section>

      {/* Main Content Dashboard */}
      <main className="flex-1 p-6 space-y-6 max-w-7xl mx-auto w-full">
        {/* Core telemetry cards */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-gray-800 bg-slate-900 bg-opacity-40 flex justify-between items-center relative overflow-hidden">
            <div>
              <div className="text-[10px] text-gray-550 uppercase font-bold">Hectares Under Command</div>
              <div className="text-2xl font-black text-white mt-1">1,875 ha</div>
              <div className="text-[9px] text-gray-400 mt-0.5">Across Sirhind Command Area</div>
            </div>
            <MapIcon className="w-10 h-10 text-gray-700 opacity-20 absolute right-3" />
          </div>

          <div className="p-4 rounded-xl border border-gray-800 bg-slate-900 bg-opacity-40 flex justify-between items-center relative overflow-hidden">
            <div>
              <div className="text-[10px] text-gray-550 uppercase font-bold">Average Water Stress Score</div>
              <div className="text-2xl font-black text-rose-400 mt-1">
                {summary ? summary.average_stress_score : "0.24"}
              </div>
              <div className="text-[9px] text-gray-400 mt-0.5">Scale [0.0 - 1.0] (FAO-56 Indices)</div>
            </div>
            <ShieldAlert className="w-10 h-10 text-gray-700 opacity-20 absolute right-3" />
          </div>

          <div className="p-4 rounded-xl border border-gray-800 bg-slate-900 bg-opacity-40 flex justify-between items-center relative overflow-hidden">
            <div>
              <div className="text-[10px] text-gray-550 uppercase font-bold">Canal Intake Flow</div>
              <div className="text-2xl font-black text-sky-400 mt-1">
                {summary ? summary.active_command_canal_flow_cusec : "1250"} Cusec
              </div>
              <div className="text-[9px] text-gray-400 mt-0.5">Sirhind feeder distributary</div>
            </div>
            <Droplets className="w-10 h-10 text-gray-700 opacity-20 absolute right-3" />
          </div>

          <div className="p-4 rounded-xl border border-gray-800 bg-slate-900 bg-opacity-40 flex justify-between items-center relative overflow-hidden">
            <div>
              <div className="text-[10px] text-gray-550 uppercase font-bold">Estimated Water Saved</div>
              <div className="text-2xl font-black text-emerald-400 mt-1">
                {summary ? summary.total_water_saved_m3 : "3840"} m³
              </div>
              <div className="text-[9px] text-gray-400 mt-0.5">Via precision irrigation depth advice</div>
            </div>
            <Award className="w-10 h-10 text-gray-700 opacity-20 absolute right-3" />
          </div>
        </section>

        {/* Row 1: Geospatial visualizer + Digital Twin side panel */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">            <div className="p-4 rounded-xl border border-gray-800 bg-slate-900 bg-opacity-20 flex flex-col gap-4">
              <div className="flex flex-col md:flex-row justify-between md:items-center gap-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-semibold text-gray-300">Observation Map Control</span>
                </div>
                
                {/* Visual Layer selectors */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setActiveLayer("crops")}
                    className={`text-[10px] font-bold px-3 py-1.5 rounded-lg border transition ${
                      activeLayer === "crops"
                        ? "bg-amber-600 border-amber-500 text-white"
                        : "bg-slate-950 border-gray-800 text-gray-400 hover:text-gray-255"
                    }`}
                  >
                    Crop Types Map
                  </button>
                  <button
                    onClick={() => setActiveLayer("stress")}
                    className={`text-[10px] font-bold px-3 py-1.5 rounded-lg border transition ${
                      activeLayer === "stress"
                        ? "bg-rose-600 border-rose-500 text-white"
                        : "bg-slate-950 border-gray-800 text-gray-400 hover:text-gray-255"
                    }`}
                  >
                    Moisture Stress Map
                  </button>
                  <button
                    onClick={() => setActiveLayer("moisture")}
                    className={`text-[10px] font-bold px-3 py-1.5 rounded-lg border transition ${
                      activeLayer === "moisture"
                        ? "bg-blue-600 border-blue-500 text-white"
                        : "bg-slate-950 border-gray-800 text-gray-400 hover:text-gray-255"
                    }`}
                  >
                    Soil Moisture Grid
                  </button>
                </div>
              </div>

              {/* Dynamic Satellite Overlay Controls */}
              <div className="flex flex-col md:flex-row justify-between md:items-center gap-3 border-t border-gray-900 pt-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400 animate-pulse" />
                  <span className="text-xs font-semibold text-gray-300">Dynamic Satellite Overlay</span>
                </div>
                
                <div className="flex gap-2">
                  {(["none", "ndvi", "ndwi", "sar"] as const).map((layer) => (
                    <button
                      key={layer}
                      onClick={() => setSatelliteOverlay(layer)}
                      className={`text-[10px] font-bold px-3 py-1.5 rounded-lg border transition uppercase ${
                        satelliteOverlay === layer
                          ? "bg-indigo-650 border-indigo-500 text-white"
                          : "bg-slate-950 border-gray-800 text-gray-400 hover:text-gray-200"
                      }`}
                    >
                      {layer === "none" ? "No Overlay" : layer}
                    </button>
                  ))}
                </div>
              </div>

              {/* Dynamic Leaflet Geospatial Render */}
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

              {/* Temporal Slider Controls (for animated phenology/growth & stress evolution) */}
              <div className="p-3 bg-slate-950 border border-gray-900 rounded-lg flex items-center gap-4">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white p-2 rounded-lg transition"
                  title={isPlaying ? "Pause Playback" : "Start Playback"}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-white" />}
                </button>
                
                <div className="flex-1 flex flex-col gap-1.5">
                  <div className="flex justify-between text-[10px] text-gray-500 font-semibold uppercase">
                    <span>Temporal Composite Timeline</span>
                    <span className="text-indigo-400 font-bold">{stepLabels[timeStep]}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="5"
                    value={timeStep}
                    onChange={(e) => setTimeStep(parseInt(e.target.value))}
                    className="w-full accent-indigo-500 bg-slate-900 h-1.5 rounded-lg appearance-none cursor-pointer"
                  />
                  <div className="flex justify-between text-[9px] text-gray-600">
                    <span>Day -10 (Sowing)</span>
                    <span>Day -8</span>
                    <span>Day -6 (Emergence)</span>
                    <span>Day -4</span>
                    <span>Day -2 (Vegetative)</span>
                    <span>Latest Observed</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Side Panel: Digital Twin / Location Weather Metrics */}
          <div className="h-full flex flex-col gap-4">
            {/* Tab Controllers */}
            <div className="flex border border-gray-800 rounded-lg bg-slate-950 p-1">
              <button
                onClick={() => setActiveSideTab("twin")}
                className={`flex-1 text-[11px] font-bold py-1.5 rounded-md transition ${
                  activeSideTab === "twin"
                    ? "bg-slate-800 text-white"
                    : "text-gray-450 hover:text-gray-200"
                }`}
              >
                Distributary Twin
              </button>
              <button
                onClick={() => setActiveSideTab("location")}
                className={`flex-1 text-[11px] font-bold py-1.5 rounded-md transition ${
                  activeSideTab === "location"
                    ? "bg-slate-800 text-white"
                    : "text-gray-455 hover:text-gray-200"
                }`}
              >
                Weather Analysis
              </button>
            </div>

            {activeSideTab === "twin" ? (
              <CanalCommandTwin summary={summary} fieldsGeojson={fieldsGeojson} />
            ) : (
              <div className="p-5 rounded-xl border border-gray-850 bg-slate-900 bg-opacity-40 flex-1 flex flex-col justify-between min-h-[300px]">
                {!activeLocationInfo ? (
                  <div className="flex flex-col items-center justify-center text-center py-20 text-gray-500 gap-2">
                    <MapPin className="w-10 h-10 text-gray-650 animate-bounce" />
                    <div className="text-xs font-semibold">No location selected</div>
                    <div className="text-[10px]">Click anywhere on the map to query weather patterns.</div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="border-b border-gray-800 pb-3">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-400">
                        <MapPin className="w-4 h-4" />
                        Selected Area Details
                      </div>
                      <div className="text-[11px] text-gray-300 mt-1 leading-relaxed">
                        {activeLocationInfo.address}
                      </div>
                      <div className="text-[9px] text-gray-500 mt-1 font-mono">
                        Latitude: {activeLocationInfo.lat.toFixed(5)}, Longitude: {activeLocationInfo.lon.toFixed(5)}
                      </div>
                    </div>

                    {activeLocationInfo.weather ? (
                      <div className="space-y-3">
                        <div className="text-[10px] uppercase font-bold text-gray-450">Live Meteorology</div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="p-2.5 rounded bg-slate-950 border border-gray-850 flex items-center gap-2">
                            <Thermometer className="w-4 h-4 text-rose-455" />
                            <div>
                              <div className="text-[9px] text-gray-500">Temperature</div>
                              <div className="font-bold text-gray-200">{activeLocationInfo.weather.temp}°C</div>
                            </div>
                          </div>

                          <div className="p-2.5 rounded bg-slate-950 border border-gray-850 flex items-center gap-2">
                            <Wind className="w-4 h-4 text-sky-400" />
                            <div>
                              <div className="text-[9px] text-gray-500">Wind Speed</div>
                              <div className="font-bold text-gray-200">{activeLocationInfo.weather.windSpeed} km/h</div>
                            </div>
                          </div>

                          <div className="p-2.5 rounded bg-slate-950 border border-gray-850 flex items-center gap-2">
                            <CloudRain className="w-4 h-4 text-blue-400" />
                            <div>
                              <div className="text-[9px] text-gray-500">Expected Rain</div>
                              <div className="font-bold text-gray-200">{activeLocationInfo.weather.rainSum} mm</div>
                            </div>
                          </div>

                          <div className="p-2.5 rounded bg-slate-950 border border-gray-850 flex items-center gap-2">
                            <Compass className="w-4 h-4 text-emerald-400" />
                            <div>
                              <div className="text-[9px] text-gray-500">Reference ET0</div>
                              <div className="font-bold text-gray-200">{activeLocationInfo.weather.et0} mm/day</div>
                            </div>
                          </div>
                        </div>

                        <div className="p-3 rounded bg-indigo-950 bg-opacity-20 border border-indigo-900 text-[10px] text-indigo-300 leading-relaxed">
                          📌 **Evapotranspiration Factor:** Reference evapotranspiration (ET0) is estimated at **{activeLocationInfo.weather.et0} mm/day** based on real-time solar radiation and thermal calculations. You can query the Copilot to analyze precision irrigation scheduling for this exact climate.
                        </div>
                      </div>
                    ) : (
                      <div className="text-xs text-rose-400 bg-rose-950 bg-opacity-20 p-3 rounded border border-rose-900">
                        Could not resolve weather forecasts for these coordinates.
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Row 2: Precision Advisory + Crop Forecasting + AI Copilot chat */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <IrrigationAdvisory
              advisories={fieldAdvisories}
              selectedField={selectedField}
              onTriggerAdvisory={handleTriggerAdvisory}
              loading={advLoading}
            />
          </div>

          <div>
            <PredictiveCharts selectedField={selectedField} />
          </div>

          <div>
            <AICopilotPanel 
              onCopilotHighlight={setCopilotHighlight} 
              activeLocationInfo={activeLocationInfo}
            />
          </div>
        </section>

        {/* Row 3: Admin Village reports & Alert trigger panel */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Village reports */}
          <div className="lg:col-span-2 p-5 rounded-xl border border-gray-800 glass-panel">
            <h3 className="font-bold text-gray-100 flex items-center gap-2 mb-4">
              <TableProperties className="w-5 h-5 text-gray-400" />
              Village moisture stress index summary
            </h3>

            <div className="overflow-x-auto text-xs">
              <table className="min-w-full divide-y divide-gray-850">
                <thead>
                  <tr className="text-gray-400 font-bold border-b border-gray-800">
                    <th className="pb-2 text-left">Village</th>
                    <th className="pb-2 text-left">District</th>
                    <th className="pb-2 text-center">Total Plots</th>
                    <th className="pb-2 text-center">Stressed Plots</th>
                    <th className="pb-2 text-center">% Stressed</th>
                    <th className="pb-2 text-center">Avg Stress Score</th>
                    <th className="pb-2 text-center">Priority</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-900 text-gray-300">
                  {villageReports.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-900 hover:bg-opacity-25 transition">
                      <td className="py-2.5 font-semibold text-gray-200">{item.village}</td>
                      <td className="py-2.5 text-gray-400">{item.district}</td>
                      <td className="py-2.5 text-center">{item.total_fields}</td>
                      <td className="py-2.5 text-center text-rose-400">{item.stressed_fields}</td>
                      <td className="py-2.5 text-center font-bold text-rose-300">{item.pct_stressed.toFixed(0)}%</td>
                      <td className="py-2.5 text-center">{item.average_stress_score.toFixed(2)}</td>
                      <td className="py-2.5 text-center">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          item.advisory_priority === "High"
                            ? "bg-rose-950 text-rose-400 border border-rose-800"
                            : item.advisory_priority === "Medium"
                            ? "bg-amber-950 text-amber-400 border border-amber-800"
                            : "bg-emerald-950 text-emerald-400 border border-emerald-800"
                        }`}>
                          {item.advisory_priority}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Alert Manager */}
          <div>
            <AlertManager alerts={alerts} onMarkRead={handleMarkAlertRead} />
          </div>
        </section>

        {/* Row 4: Crop Suitability & Claims Evidence Auditor */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <CropSuitability locationInfo={activeLocationInfo} />
          <InsuranceAuditor selectedField={selectedField} />
        </section>
      </main>

      {/* Footer Info */}
      <footer className="border-t border-gray-950 bg-slate-950 py-4.5 px-6 text-center text-[10px] text-gray-600 mt-auto">
        &copy; {new Date().getFullYear()} AgriSense AI Systems. All rights reserved. Powered by Google DeepMind Advanced Agentic Coding.
      </footer>
    </div>
  );
}
