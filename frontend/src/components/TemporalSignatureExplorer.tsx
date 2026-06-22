"use client";

import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, ReferenceLine } from "recharts";
import { Activity, Layers, Loader2, Radio, TrendingUp } from "lucide-react";

const CROP_COLORS: Record<string, string> = {
  wheat: "#FCD34D",
  rice: "#34D399",
  cotton: "#F472B6",
  sugarcane: "#FB923C",
  fallow: "#94A3B8",
};

const INDEX_CONFIG = [
  { key: "ndvi", label: "NDVI", color: "#34D399", dash: "" },
  { key: "evi", label: "EVI", color: "#38BDF8", dash: "5 5" },
  { key: "ndwi", label: "NDWI", color: "#818CF8", dash: "3 3" },
];

const SAR_CONFIG = [
  { key: "vv_db", label: "VV (dB)", color: "#F59E0B" },
  { key: "vh_db", label: "VH (dB)", color: "#A78BFA" },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="px-3 py-2 rounded-xl text-[9px] space-y-1"
      style={{ background: "rgba(6,13,24,0.97)", border: "1px solid rgba(255,255,255,0.1)", boxShadow: "0 8px 32px rgba(0,0,0,0.5)" }}>
      <div className="font-bold text-slate-300 mb-1.5">{label}</div>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-400 w-12">{p.name}:</span>
          <span className="font-bold text-white">{typeof p.value === "number" ? p.value.toFixed(3) : p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function TemporalSignatureExplorer() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCrops, setSelectedCrops] = useState<string[]>(["wheat", "rice"]);
  const [activeIndex, setActiveIndex] = useState<"optical" | "sar">("optical");
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    fetch(`${baseUrl}/temporal/explorer/timeseries`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        buildChartData(d, selectedCrops);
      })
      .catch(() => {
        // Fallback: synthetic signatures
        const stages = ["Sowing", "Emergence", "Veg-I", "Veg-II", "Repro.", "Flower.", "Grain-I", "Grain-II", "Late", "Senes.", "Harvest", "Post-H"];
        const fallback = {
          time_steps: stages.map((_, i) => `T+${i * 8}d`),
          stage_labels: stages,
          crops: {
            wheat:     { ndvi_profile: [0.12,0.18,0.32,0.55,0.72,0.80,0.78,0.68,0.52,0.38,0.22,0.14], evi_profile: [0.09,0.14,0.27,0.47,0.62,0.71,0.69,0.60,0.44,0.31,0.18,0.10], ndwi_profile: [-0.25,-0.18,0.05,0.18,0.30,0.35,0.32,0.20,0.08,-0.05,-0.18,-0.24], vv_profile: [-14.2,-13.8,-12.5,-11.2,-10.5,-11.0,-11.5,-12.0,-13.0,-13.8,-14.5,-15.0], vh_profile: [-20.5,-20.0,-18.8,-17.2,-15.8,-15.5,-16.0,-17.0,-18.5,-19.5,-20.5,-21.0] },
            rice:      { ndvi_profile: [0.08,0.14,0.30,0.58,0.78,0.82,0.80,0.70,0.50,0.30,0.15,0.08], evi_profile: [0.06,0.11,0.25,0.50,0.68,0.73,0.71,0.62,0.43,0.24,0.12,0.06], ndwi_profile: [0.40,0.38,0.28,0.15,0.05,0.02,0.04,0.10,0.18,0.30,0.38,0.42], vv_profile: [-8.5,-9.0,-10.5,-12.0,-11.5,-12.0,-12.5,-11.8,-10.5,-9.5,-8.8,-8.2], vh_profile: [-14.5,-15.0,-16.5,-18.0,-17.0,-17.5,-18.0,-17.2,-15.8,-14.8,-14.2,-13.8] },
            cotton:    { ndvi_profile: [0.10,0.15,0.28,0.50,0.68,0.72,0.70,0.62,0.48,0.32,0.20,0.12], evi_profile: [0.08,0.12,0.23,0.43,0.59,0.63,0.61,0.54,0.41,0.26,0.16,0.09], ndwi_profile: [-0.30,-0.22,-0.08,0.10,0.22,0.26,0.24,0.16,0.04,-0.10,-0.22,-0.28], vv_profile: [-12.5,-12.0,-11.5,-10.5,-10.0,-10.5,-11.0,-11.8,-12.5,-13.0,-13.5,-14.0], vh_profile: [-19.0,-18.5,-17.8,-16.5,-15.8,-16.0,-16.5,-17.5,-18.5,-19.0,-19.5,-20.0] },
            sugarcane: { ndvi_profile: [0.18,0.25,0.38,0.55,0.70,0.78,0.80,0.79,0.75,0.68,0.55,0.40], evi_profile: [0.15,0.21,0.32,0.48,0.62,0.70,0.72,0.71,0.67,0.60,0.48,0.34], ndwi_profile: [-0.15,-0.05,0.08,0.20,0.32,0.40,0.42,0.40,0.36,0.28,0.18,0.05], vv_profile: [-13.0,-12.5,-12.0,-11.0,-10.2,-9.8,-9.5,-9.8,-10.5,-11.0,-12.0,-13.0], vh_profile: [-19.5,-19.0,-18.0,-16.8,-15.5,-14.8,-14.5,-14.8,-15.8,-16.5,-17.8,-19.0] },
          },
        };
        setData(fallback);
        buildChartData(fallback, selectedCrops);
      })
      .finally(() => setLoading(false));
  }, []);

  function buildChartData(d: any, crops: string[]) {
    if (!d?.time_steps) return;
    const rows = d.time_steps.map((t: string, i: number) => {
      const row: any = { step: d.stage_labels?.[i] || t };
      crops.forEach(crop => {
        const sig = d.crops?.[crop];
        if (sig) {
          row[`${crop}_ndvi`] = sig.ndvi_profile?.[i] ?? null;
          row[`${crop}_evi`] = sig.evi_profile?.[i] ?? null;
          row[`${crop}_ndwi`] = sig.ndwi_profile?.[i] ?? null;
          row[`${crop}_vv`] = sig.vv_profile?.[i] ?? null;
          row[`${crop}_vh`] = sig.vh_profile?.[i] ?? null;
        }
      });
      return row;
    });
    setChartData(rows);
  }

  function toggleCrop(crop: string) {
    const next = selectedCrops.includes(crop)
      ? selectedCrops.filter(c => c !== crop)
      : [...selectedCrops, crop];
    setSelectedCrops(next);
    if (data) buildChartData(data, next);
  }

  const crops = data ? Object.keys(data.crops || {}) : ["wheat", "rice", "cotton", "sugarcane"];

  return (
    <div className="rounded-2xl overflow-hidden"
      style={{ background: "linear-gradient(135deg,rgba(15,32,64,0.9),rgba(10,22,40,0.85))", border: "1px solid rgba(255,255,255,0.07)", boxShadow: "0 4px 32px rgba(0,0,0,0.4)" }}>

      {/* Header */}
      <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: "linear-gradient(135deg,rgba(251,146,60,0.2),rgba(245,158,11,0.12))", border: "1px solid rgba(251,146,60,0.3)" }}>
            <Activity className="w-4 h-4 text-amber-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-white">Temporal Signature Explorer</div>
            <div className="text-[9px] text-slate-500 mt-0.5">PS-6: Multi-temporal spectral signature library — 8-day composites</div>
          </div>
        </div>
        <span className="chip text-[8px] font-bold" style={{ background: "rgba(251,146,60,0.1)", border: "1px solid rgba(251,146,60,0.25)", color: "#FB923C" }}>
          {data?.n_crops || 5} CROPS · 12 TIME STEPS
        </span>
      </div>

      <div className="p-5 space-y-4">
        {/* Crop toggles */}
        <div className="flex flex-wrap gap-2">
          {crops.map(crop => (
            <button key={crop}
              onClick={() => toggleCrop(crop)}
              className="text-[9px] font-black px-3 py-1.5 rounded-lg border transition-all duration-200"
              style={{
                background: selectedCrops.includes(crop) ? `${CROP_COLORS[crop]}18` : "transparent",
                borderColor: selectedCrops.includes(crop) ? CROP_COLORS[crop] : "rgba(255,255,255,0.1)",
                color: selectedCrops.includes(crop) ? CROP_COLORS[crop] : "#64748B",
                boxShadow: selectedCrops.includes(crop) ? `0 0 10px ${CROP_COLORS[crop]}25` : "none",
              }}>
              {crop.charAt(0).toUpperCase() + crop.slice(1)}
            </button>
          ))}

          {/* Index type toggle */}
          <div className="ml-auto flex items-center gap-1 p-0.5 rounded-lg" style={{ background: "rgba(6,13,24,0.7)", border: "1px solid rgba(255,255,255,0.08)" }}>
            {(["optical", "sar"] as const).map(t => (
              <button key={t} onClick={() => setActiveIndex(t)}
                className="text-[9px] font-bold px-2.5 py-1 rounded-md transition-all"
                style={{ background: activeIndex === t ? "rgba(99,102,241,0.2)" : "transparent", color: activeIndex === t ? "#818CF8" : "#64748B", border: activeIndex === t ? "1px solid rgba(99,102,241,0.3)" : "1px solid transparent" }}>
                {t === "optical" ? "🌿 Optical" : "📡 SAR"}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16 gap-3">
            <Loader2 className="w-5 h-5 animate-spin text-amber-400" />
            <span className="text-[11px] text-slate-500">Loading signature library...</span>
          </div>
        ) : (
          <>
            {/* Main chart */}
            <div>
              <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-2.5">
                {activeIndex === "optical" ? "NDVI · EVI · NDWI Time Series" : "VV · VH Backscatter (dB)"} — Previous Season Profile
              </div>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={chartData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
                  <XAxis dataKey="step" tick={{ fill: "#64748B", fontSize: 7 }} axisLine={false} tickLine={false} interval={1} />
                  <YAxis tick={{ fill: "#64748B", fontSize: 8 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  {activeIndex === "optical" && selectedCrops.map(crop =>
                    ["ndvi", "evi", "ndwi"].map((idx, ii) => (
                      <Line key={`${crop}_${idx}`} type="monotone" dataKey={`${crop}_${idx}`}
                        name={`${crop.slice(0, 4)} ${idx.toUpperCase()}`}
                        stroke={CROP_COLORS[crop]} strokeWidth={ii === 0 ? 2.5 : 1.5}
                        strokeDasharray={ii === 1 ? "4 4" : ii === 2 ? "2 2" : ""} dot={false} />
                    ))
                  )}
                  {activeIndex === "sar" && selectedCrops.map(crop =>
                    ["vv", "vh"].map((pol, pi) => (
                      <Line key={`${crop}_${pol}`} type="monotone" dataKey={`${crop}_${pol}`}
                        name={`${crop.slice(0, 4)} ${pol.toUpperCase()}`}
                        stroke={CROP_COLORS[crop]} strokeWidth={pi === 0 ? 2.5 : 1.5}
                        strokeDasharray={pi === 1 ? "4 4" : ""} dot={false} />
                    ))
                  )}
                  {activeIndex === "optical" && <ReferenceLine y={0.15} stroke="rgba(255,255,255,0.06)" strokeDasharray="2 2" />}
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Signature stats table */}
            {data && (
              <div className="overflow-x-auto">
                <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-2">Peak NDVI · SOS · EOS · LGP</div>
                <div className="space-y-1.5">
                  {selectedCrops.map(crop => {
                    const sig = data.crops?.[crop];
                    if (!sig) return null;
                    return (
                      <div key={crop} className="flex items-center gap-3 px-3 py-2 rounded-lg" style={{ background: "rgba(6,13,24,0.5)", border: "1px solid rgba(255,255,255,0.04)" }}>
                        <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: CROP_COLORS[crop] }} />
                        <span className="text-[9px] font-bold text-slate-300 w-20">{crop.charAt(0).toUpperCase() + crop.slice(1)}</span>
                        <span className="text-[9px] text-slate-500">Peak: <span className="text-white font-bold">{sig.peak_ndvi?.toFixed(2) ?? "—"}</span></span>
                        <span className="text-[9px] text-slate-500">SOS: <span className="text-emerald-400 font-bold">T+{(sig.sos_step ?? 0) * 8}d</span></span>
                        <span className="text-[9px] text-slate-500">EOS: <span className="text-amber-400 font-bold">T+{(sig.eos_step ?? 11) * 8}d</span></span>
                        <span className="text-[9px] text-slate-500">LGP: <span className="text-violet-400 font-bold">{((sig.eos_step ?? 11) - (sig.sos_step ?? 0)) * 8}d</span></span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="text-[8px] text-slate-600 pt-1">
              Source: Sentinel-2 L2A + Sentinel-1 GRD multi-temporal composites · Punjab Canal Command Area 2022–2025
            </div>
          </>
        )}
      </div>
    </div>
  );
}
