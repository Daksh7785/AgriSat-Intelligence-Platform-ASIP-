"use client";

import React, { useEffect, useState } from "react";
import {
  Leaf, Calendar, Clock, Target, TrendingUp, AlertTriangle,
  ChevronRight, Loader2, FlaskConical
} from "lucide-react";

interface PhenologyStagePanelProps {
  selectedField: any;
}

const STAGE_CONFIG = [
  { name: "Sowing",       icon: "🌱", color: "#94A3B8" },
  { name: "Emergence",    icon: "🌿", color: "#6EE7B7" },
  { name: "Vegetative",   icon: "🍀", color: "#34D399" },
  { name: "Reproductive", icon: "🌸", color: "#FB923C" },
  { name: "Grain Fill",   icon: "🌾", color: "#FCD34D" },
  { name: "Maturity",     icon: "🟡", color: "#A78BFA" },
];

export default function PhenologyStagePanel({ selectedField }: PhenologyStagePanelProps) {
  const [data, setData] = useState<any>(null);
  const [calendarData, setCalendarData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedField) return;
    setLoading(true);
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    Promise.all([
      fetch(`${baseUrl}/phenology/${selectedField.id}/current`).then(r => r.json()),
      fetch(`${baseUrl}/phenology/${selectedField.id}/growth-stages`).then(r => r.json()),
    ]).then(([curr, cal]) => {
      setData(curr);
      setCalendarData(cal);
    }).catch(() => {
      // Synthetic fallback
      const today = new Date();
      setData({
        crop_type: selectedField.properties.crop_type || "wheat",
        days_since_sowing: 72,
        days_to_harvest: 58,
        lgp_days: 130,
        current_stage: { name: "Reproductive", icon: "🌸", order: 3, kc: 1.15, progress_pct: 48, days_in_stage: 12, stage_duration_days: 25 },
        phenology_metrics: {
          sos_date: new Date(today.getFullYear(), 10, 1).toISOString().split("T")[0],
          peak_ndvi_date: new Date(today.getFullYear(), 1, 14).toISOString().split("T")[0],
          eos_date: new Date(today.getFullYear(), 3, 1).toISOString().split("T")[0],
          lgp_days: 130,
          gdd_accumulated: 864,
          gdd_required: 1430,
          gdd_pct: 60.4,
        },
        current_indices: { ndvi: selectedField.properties.ndvi || 0.55, soil_moisture: selectedField.properties.soil_moisture || 0.42, stress_score: selectedField.properties.stress_score || 0.28 },
        all_stages: STAGE_CONFIG.map((s, i) => ({ stage: s.name, order: i, days: [i * 22, (i + 1) * 22], kc: 0.5 + i * 0.15 })),
      });
      setCalendarData({
        stage_stress_history: STAGE_CONFIG.map((s, i) => ({
          stage: s.name, icon: s.icon,
          start_date: new Date(today.getFullYear(), 10, 1 + i * 22).toISOString().split("T")[0],
          duration_days: 22, kc: 0.5 + i * 0.15,
          stress_level: [0.05, 0.10, 0.25, 0.55, 0.35, 0.10][i],
          stress_class: ["None", "None", "Mild", "Severe", "Moderate", "None"][i],
          vci: [0.78, 0.72, 0.60, 0.32, 0.48, 0.80][i],
          smi: [0.75, 0.68, 0.52, 0.28, 0.45, 0.72][i],
          vhi: [0.765, 0.70, 0.56, 0.30, 0.465, 0.76][i],
        })),
        current_stage: "Reproductive",
      });
    }).finally(() => setLoading(false));
  }, [selectedField]);

  if (!selectedField) {
    return (
      <div className="rounded-2xl flex flex-col items-center justify-center text-center p-10 gap-4"
        style={{ background: "linear-gradient(135deg,rgba(15,32,64,0.9),rgba(10,22,40,0.85))", border: "1px solid rgba(255,255,255,0.07)", minHeight: "300px" }}>
        <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.15)" }}>
          <Leaf className="w-7 h-7 text-indigo-400/40" />
        </div>
        <div className="text-sm font-bold text-slate-400 mb-1">No Field Selected</div>
        <div className="text-[11px] text-slate-600 max-w-[200px] mx-auto leading-relaxed">Select a field on the map to view its phenological stage and growth calendar.</div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl overflow-hidden flex flex-col"
      style={{ background: "linear-gradient(135deg,rgba(15,32,64,0.9),rgba(10,22,40,0.85))", border: "1px solid rgba(255,255,255,0.07)", boxShadow: "0 4px 32px rgba(0,0,0,0.4)" }}>

      {/* Header */}
      <div className="px-5 py-4 flex items-center justify-between" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: "linear-gradient(135deg,rgba(52,211,153,0.2),rgba(16,185,129,0.12))", border: "1px solid rgba(52,211,153,0.3)" }}>
            <Leaf className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-none">Phenology Tracker</div>
            <div className="text-[9px] text-slate-500 mt-0.5">SOS · Peak NDVI · LGP · Stage-wise Stress</div>
          </div>
        </div>
        {data && (
          <span className="chip text-[9px] font-bold" style={{ background: "rgba(52,211,153,0.12)", border: "1px solid rgba(52,211,153,0.25)", color: "#34D399" }}>
            {data.current_stage?.icon} {data.current_stage?.name}
          </span>
        )}
      </div>

      <div className="p-5 flex-1 space-y-5">
        {loading ? (
          <div className="flex flex-col items-center gap-2.5 py-10">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
            <div className="text-[11px] text-slate-500">Fetching phenology data...</div>
          </div>
        ) : data ? (
          <>
            {/* Stage Progress Bar */}
            <div>
              <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-3">Growth Stage Timeline</div>
              <div className="relative flex items-center gap-0">
                {STAGE_CONFIG.map((s, i) => {
                  const isActive = data.current_stage?.name === s.name;
                  const isPast = data.current_stage?.order > i;
                  return (
                    <div key={i} className="flex items-center flex-1">
                      <div className="flex flex-col items-center gap-1 relative flex-1">
                        <div className="relative">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm transition-all z-10 relative ${isActive ? "ring-2 ring-offset-1 ring-offset-[#060D18]" : ""}`}
                            style={{
                              background: isActive ? `${s.color}25` : isPast ? `${s.color}12` : "rgba(6,13,24,0.8)",
                              border: `2px solid ${isActive ? s.color : isPast ? s.color + "60" : "rgba(255,255,255,0.08)"}`,
                              boxShadow: isActive ? `0 0 12px ${s.color}40` : "none",
                              ringColor: s.color,
                            }}>
                            <span className={`text-sm leading-none ${!isPast && !isActive ? "opacity-30" : ""}`}>{s.icon}</span>
                          </div>
                          {isActive && (
                            <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-[#060D18]"
                              style={{ background: s.color, boxShadow: `0 0 6px ${s.color}` }} />
                          )}
                        </div>
                        <div className={`text-[8px] font-bold text-center leading-tight ${isActive ? "text-white" : isPast ? "text-slate-500" : "text-slate-700"}`} style={{ maxWidth: "44px" }}>
                          {s.name}
                        </div>
                      </div>
                      {i < STAGE_CONFIG.length - 1 && (
                        <div className="h-px flex-shrink-0 w-2 mb-5"
                          style={{ background: isPast ? `${STAGE_CONFIG[i].color}60` : "rgba(255,255,255,0.06)" }} />
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Current stage progress */}
              <div className="mt-3 space-y-1.5">
                <div className="flex justify-between text-[9px] text-slate-500">
                  <span>Stage progress</span>
                  <span className="text-white font-bold">{data.current_stage.progress_pct}%</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill-emerald" style={{ width: `${data.current_stage.progress_pct}%`, transition: "width 1s ease" }} />
                </div>
                <div className="text-[9px] text-slate-600">{data.current_stage.days_in_stage} / {data.current_stage.stage_duration_days} days · Kc = {data.current_stage.kc}</div>
              </div>
            </div>

            {/* Phenology Key Dates */}
            <div className="grid grid-cols-2 gap-2.5">
              {[
                { label: "Days Since Sowing", value: `${data.days_since_sowing}d`, icon: <Clock className="w-3.5 h-3.5 text-sky-400" />, color: "#38BDF8" },
                { label: "Days to Harvest", value: `${data.days_to_harvest}d`, icon: <Target className="w-3.5 h-3.5 text-amber-400" />, color: "#FCD34D" },
                { label: "GDD Accumulated", value: `${data.phenology_metrics.gdd_pct}%`, icon: <TrendingUp className="w-3.5 h-3.5 text-violet-400" />, color: "#A78BFA" },
                { label: "Season Length", value: `${data.lgp_days}d`, icon: <Calendar className="w-3.5 h-3.5 text-emerald-400" />, color: "#34D399" },
              ].map(({ label, value, icon, color }) => (
                <div key={label} className="p-3 rounded-xl" style={{ background: "rgba(6,13,24,0.7)", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div className="flex items-center gap-1.5 mb-1">{icon}<div className="text-[8px] text-slate-500 font-bold uppercase tracking-wide">{label}</div></div>
                  <div className="text-[15px] font-black" style={{ color }}>{value}</div>
                </div>
              ))}
            </div>

            {/* SOS / Peak / EOS dates */}
            <div className="space-y-2" style={{ borderTop: "1px solid rgba(255,255,255,0.04)", paddingTop: "12px" }}>
              <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-2">Key Phenological Dates</div>
              {[
                { label: "Start of Season (SOS)", date: data.phenology_metrics.sos_date, color: "#34D399" },
                { label: "Peak NDVI Date", date: data.phenology_metrics.peak_ndvi_date, color: "#FCD34D" },
                { label: "End of Season (EOS)", date: data.phenology_metrics.eos_date, color: "#FB923C" },
              ].map(({ label, date: d, color }) => (
                <div key={label} className="flex items-center justify-between px-3 py-2 rounded-lg" style={{ background: "rgba(6,13,24,0.5)", border: "1px solid rgba(255,255,255,0.04)" }}>
                  <span className="text-[10px] text-slate-500">{label}</span>
                  <span className="text-[10px] font-bold font-mono" style={{ color }}>{d}</span>
                </div>
              ))}
            </div>

            {/* Stage-wise stress history */}
            {calendarData?.stage_stress_history && (
              <div style={{ borderTop: "1px solid rgba(255,255,255,0.04)", paddingTop: "12px" }}>
                <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-2">Stage-wise Stress History</div>
                <div className="space-y-2 max-h-[200px] overflow-y-auto pr-0.5">
                  {calendarData.stage_stress_history.map((s: any, i: number) => {
                    const stressColor = s.stress_class === "Severe" ? "#F43F5E" : s.stress_class === "Moderate" ? "#F59E0B" : s.stress_class === "Mild" ? "#FCD34D" : "#34D399";
                    const isActive = s.stage === calendarData.current_stage;
                    return (
                      <div key={i} className="flex items-center justify-between p-2.5 rounded-xl"
                        style={{ background: isActive ? "rgba(99,102,241,0.08)" : "rgba(6,13,24,0.5)", border: `1px solid ${isActive ? "rgba(99,102,241,0.2)" : "rgba(255,255,255,0.04)"}` }}>
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{s.icon}</span>
                          <div>
                            <div className="text-[10px] font-bold text-slate-200">{s.stage}</div>
                            <div className="text-[8px] text-slate-600">VCI {s.vci} · SMI {s.smi} · VHI {s.vhi}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="text-right">
                            <div className="text-[9px] font-black" style={{ color: stressColor }}>{s.stress_class}</div>
                            <div className="text-[8px] text-slate-600">Kc {s.kc}</div>
                          </div>
                          {isActive && <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-xs text-rose-400 text-center py-8">Failed to load phenology data.</div>
        )}
      </div>
    </div>
  );
}
