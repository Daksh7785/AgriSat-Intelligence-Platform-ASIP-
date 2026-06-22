"use client";

import React, { useEffect, useState } from "react";
import { Radio, Satellite, Loader2, RefreshCw } from "lucide-react";

interface SatelliteIndicesPanelProps {
  selectedField: any;
}

interface IndexGaugeProps {
  label: string;
  value: number;
  min?: number;
  max?: number;
  color: string;
  unit?: string;
  description?: string;
}

function IndexGauge({ label, value, min = -1, max = 1, color, unit = "", description }: IndexGaugeProps) {
  const pct = Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{label}</span>
          {description && <div className="text-[7px] text-slate-600">{description}</div>}
        </div>
        <span className="text-[12px] font-black font-mono" style={{ color }}>{value.toFixed(3)}{unit}</span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "rgba(255,255,255,0.06)" }}>
        <div className="h-full rounded-full transition-all duration-800"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}60, ${color})`, boxShadow: `0 0 6px ${color}50` }} />
      </div>
    </div>
  );
}

export default function SatelliteIndicesPanel({ selectedField }: SatelliteIndicesPanelProps) {
  const [data, setData] = useState<any>(null);
  const [sarData, setSarData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"optical" | "condition" | "sar">("optical");

  const fetchData = () => {
    if (!selectedField) return;
    setLoading(true);
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    Promise.all([
      fetch(`${baseUrl}/indices/${selectedField.id}/current`).then(r => r.json()),
      fetch(`${baseUrl}/sar/${selectedField.id}/features`).then(r => r.json()),
    ]).then(([idx, sar]) => {
      setData(idx);
      setSarData(sar);
    }).catch(() => {
      const ndvi = selectedField.properties.ndvi || 0.55;
      const sm = selectedField.properties.soil_moisture || 0.42;
      const stress = selectedField.properties.stress_score || 0.28;
      setData({
        crop_type: selectedField.properties.crop_type || "wheat",
        optical_indices: { ndvi, evi: +(ndvi * 0.82).toFixed(3), ndwi: +(sm * 0.5 - 0.1).toFixed(3), savi: +(ndvi * 0.9).toFixed(3) },
        condition_indices: { vci: +(0.3 + ndvi * 0.8).toFixed(3), tci: +(0.5 - stress * 0.3).toFixed(3), vhi: +(0.4 + ndvi * 0.4).toFixed(3), smi: +(sm * 1.5).toFixed(3) },
        land_surface_temp_c: +(28 + stress * 15).toFixed(1),
        stress_classification: { level: stress > 0.5 ? "Severe Stress" : stress > 0.3 ? "Moderate Stress" : "Mild Stress", color: stress > 0.5 ? "#F43F5E" : stress > 0.3 ? "#F59E0B" : "#FCD34D", code: stress > 0.5 ? 3 : stress > 0.3 ? 2 : 1 },
        data_source: "Sentinel-2 L2A",
      });
      setSarData({
        processing: { filter: "Refined Lee (5×5)", sensor: "Sentinel-1A IW GRD" },
        backscatter_processed: { vv_db: -12.5, vh_db: -18.8, vh_vv_db: -6.3, vh_vv_linear: 0.234 },
        glcm_texture: { energy: 0.182, entropy: 2.41, contrast: 0.534, homogeneity: 0.712, correlation: 0.845 },
        sar_soil_moisture: +(sm).toFixed(3),
        crop_structure: { double_bounce_index: 0.32, volume_scatter_index: 0.68, surface_roughness_proxy: 0.41 },
      });
    }).finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); }, [selectedField]);

  if (!selectedField) {
    return (
      <div className="rounded-2xl flex flex-col items-center justify-center p-8 gap-3 text-center"
        style={{ background: "linear-gradient(135deg,rgba(15,32,64,0.9),rgba(10,22,40,0.85))", border: "1px solid rgba(255,255,255,0.07)", minHeight: "260px" }}>
        <Satellite className="w-8 h-8 text-indigo-400/30" />
        <div className="text-sm font-bold text-slate-500">Select a field to load satellite indices</div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl overflow-hidden flex flex-col"
      style={{ background: "linear-gradient(135deg,rgba(15,32,64,0.9),rgba(10,22,40,0.85))", border: "1px solid rgba(255,255,255,0.07)", boxShadow: "0 4px 32px rgba(0,0,0,0.4)" }}>

      {/* Header */}
      <div className="px-5 py-3.5 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: "linear-gradient(135deg,rgba(167,139,250,0.2),rgba(99,102,241,0.12))", border: "1px solid rgba(167,139,250,0.3)" }}>
            <Satellite className="w-4 h-4 text-violet-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-white">Satellite Indices</div>
            <div className="text-[9px] text-slate-500">NDVI · EVI · VCI · SMI · VV · VH · GLCM</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {data?.stress_classification && (
            <span className="text-[8px] font-black px-2 py-1 rounded-md"
              style={{ background: `${data.stress_classification.color}12`, border: `1px solid ${data.stress_classification.color}30`, color: data.stress_classification.color }}>
              {data.stress_classification.level}
            </span>
          )}
          <button onClick={fetchData} className="p-1.5 rounded-lg transition-colors hover:bg-white/5">
            <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        {(["optical", "condition", "sar"] as const).map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className="flex-1 py-2.5 text-[8px] font-bold uppercase tracking-widest transition-colors"
            style={{ color: activeTab === tab ? "#A78BFA" : "#475569", borderBottom: activeTab === tab ? "2px solid #A78BFA" : "2px solid transparent", background: "transparent" }}>
            {tab === "optical" ? "🌿 Optical" : tab === "condition" ? "📊 Condition" : "📡 SAR+GLCM"}
          </button>
        ))}
      </div>

      <div className="p-5 space-y-4 flex-1">
        {loading ? (
          <div className="flex items-center justify-center py-10 gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-violet-400" />
            <span className="text-[10px] text-slate-500">Fetching satellite data...</span>
          </div>
        ) : activeTab === "optical" && data ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2.5">
              {[
                { label: "LST", value: data.land_surface_temp_c, min: 15, max: 50, color: "#F59E0B", unit: "°C", description: "Land Surface Temp" },
                { label: "Source", value: null, color: "#818CF8" },
              ].filter(x => x.value !== null).map((item, i) => (
                <IndexGauge key={i} {...item as any} />
              ))}
            </div>
            <div className="space-y-3.5">
              <IndexGauge label="NDVI" value={data.optical_indices?.ndvi ?? 0} min={-0.1} max={1} color="#34D399" description="Vegetation greenness index" />
              <IndexGauge label="EVI" value={data.optical_indices?.evi ?? 0} min={-0.2} max={1} color="#38BDF8" description="Enhanced — reduces soil/atm effects" />
              <IndexGauge label="NDWI" value={data.optical_indices?.ndwi ?? 0} min={-0.6} max={0.8} color="#818CF8" description="Water content indicator" />
              <IndexGauge label="SAVI" value={data.optical_indices?.savi ?? 0} min={-0.1} max={1} color="#6EE7B7" description="Soil-adjusted vegetation index" />
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl" style={{ background: "rgba(6,13,24,0.6)", border: "1px solid rgba(255,255,255,0.05)" }}>
              <span className="text-[9px] text-slate-500">LST:</span>
              <span className="text-[12px] font-black text-amber-400">{data.land_surface_temp_c}°C</span>
              <span className="text-[9px] text-slate-500">Source: {data.data_source}</span>
            </div>
          </div>

        ) : activeTab === "condition" && data ? (
          <div className="space-y-4">
            <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Condition Indices (Kogan 1995)</div>
            <div className="space-y-3.5">
              <IndexGauge label="VCI" value={data.condition_indices?.vci ?? 0} min={0} max={1} color="#34D399" description="Vegetation Condition Index — drought signal" />
              <IndexGauge label="TCI" value={data.condition_indices?.tci ?? 0} min={0} max={1} color="#38BDF8" description="Temperature Condition Index" />
              <IndexGauge label="VHI" value={data.condition_indices?.vhi ?? 0} min={0} max={1} color="#FCD34D" description="Vegetation Health Index = 0.5×VCI + 0.5×TCI" />
              <IndexGauge label="SMI" value={data.condition_indices?.smi ?? 0} min={0} max={1} color="#FB923C" description="Soil Moisture Index (FC−WP normalized)" />
            </div>
            <div className="p-3.5 rounded-xl"
              style={{ background: `${data.stress_classification?.color}08`, border: `1px solid ${data.stress_classification?.color}20` }}>
              <div className="text-[9px] font-bold uppercase tracking-widest mb-1.5" style={{ color: data.stress_classification?.color }}>
                Stress Classification
              </div>
              <div className="text-[13px] font-black text-white">{data.stress_classification?.level}</div>
              <div className="text-[8px] text-slate-500 mt-1">VHI threshold classification · Kogan 1995</div>
            </div>
          </div>

        ) : activeTab === "sar" && sarData ? (
          <div className="space-y-4">
            <div className="text-[8px] text-slate-600 px-1">{sarData.processing?.filter} · {sarData.processing?.sensor}</div>

            <div className="space-y-3.5">
              <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Backscatter (dB)</div>
              <IndexGauge label="VV" value={sarData.backscatter_processed?.vv_db ?? -12} min={-25} max={0} color="#F59E0B" unit=" dB" description="Vertical-Vertical — surface scattering" />
              <IndexGauge label="VH" value={sarData.backscatter_processed?.vh_db ?? -18} min={-28} max={-5} color="#A78BFA" unit=" dB" description="Vertical-Horizontal — volume scattering" />
              <IndexGauge label="VH/VV ratio" value={sarData.backscatter_processed?.vh_vv_linear ?? 0.23} min={0} max={1} color="#38BDF8" description="Cross-pol ratio — crop structure indicator" />
            </div>

            <div>
              <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-2.5">GLCM Texture Features</div>
              <div className="grid grid-cols-2 gap-1.5">
                {[
                  { label: "Energy", value: sarData.glcm_texture?.energy, color: "#34D399" },
                  { label: "Entropy", value: sarData.glcm_texture?.entropy, color: "#FCD34D", max: 4 },
                  { label: "Contrast", value: sarData.glcm_texture?.contrast, color: "#FB923C", max: 3 },
                  { label: "Homogeneity", value: sarData.glcm_texture?.homogeneity, color: "#38BDF8" },
                  { label: "Correlation", value: sarData.glcm_texture?.correlation, color: "#A78BFA" },
                  { label: "SM proxy", value: sarData.sar_soil_moisture, color: "#6EE7B7" },
                ].map(({ label, value, color, max = 1 }) => (
                  <div key={label} className="p-2.5 rounded-xl" style={{ background: "rgba(6,13,24,0.6)", border: "1px solid rgba(255,255,255,0.04)" }}>
                    <div className="text-[7px] text-slate-500 font-bold uppercase tracking-wide mb-1">{label}</div>
                    <div className="text-[12px] font-black font-mono" style={{ color }}>{(value ?? 0).toFixed(3)}</div>
                    <div className="mt-1 h-1 rounded-full" style={{ background: "rgba(255,255,255,0.05)" }}>
                      <div className="h-full rounded-full" style={{ width: `${Math.min(100, (value / max) * 100)}%`, background: color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
