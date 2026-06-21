"use client";

import { Droplets, Activity, Percent, ArrowRight, Waves } from "lucide-react";

interface CanalCommandTwinProps {
  summary: any;
  fieldsGeojson: any;
}

export default function CanalCommandTwin({ summary, fieldsGeojson }: CanalCommandTwinProps) {
  const fields = fieldsGeojson?.features || [];
  const priorityFields = [...fields]
    .filter((f: any) => f.properties.stress_score > 0.15)
    .sort((a: any, b: any) => b.properties.stress_score - a.properties.stress_score);

  const reservoirCapacity = 500000;
  const reservoirStorage = 385420;
  const storagePercentage = (reservoirStorage / reservoirCapacity) * 100;
  const canalFlow = summary?.active_command_canal_flow_cusec || 1250;
  const canalUtilization = (canalFlow / 1500) * 100;

  return (
    <div
      className="rounded-2xl flex flex-col"
      style={{
        background: "linear-gradient(135deg, rgba(15,32,64,0.9) 0%, rgba(10,22,40,0.85) 100%)",
        border: "1px solid rgba(255,255,255,0.07)",
        boxShadow: "0 4px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
      }}
    >
      {/* Header */}
      <div
        className="px-5 py-4 flex items-center justify-between flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{
              background: "linear-gradient(135deg, rgba(56,189,248,0.2), rgba(14,165,233,0.15))",
              border: "1px solid rgba(56,189,248,0.3)",
            }}
          >
            <Activity className="w-4 h-4 text-sky-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-none">Digital Canal Twin</div>
            <div className="text-[9px] text-slate-500 mt-0.5">Sirhind Command Network Simulation</div>
          </div>
        </div>
        <span
          className="flex items-center gap-1.5 text-[9px] font-bold px-2 py-1 rounded-lg"
          style={{ background: "rgba(56,189,248,0.1)", border: "1px solid rgba(56,189,248,0.25)", color: "#38BDF8" }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
          LIVE
        </span>
      </div>

      <div className="p-4 space-y-4 flex-1">
        {/* Reservoir + Canal cards */}
        <div className="grid grid-cols-2 gap-3">
          {/* Reservoir */}
          <div
            className="relative rounded-xl p-4 overflow-hidden flex flex-col justify-between"
            style={{ background: "rgba(6,13,24,0.7)", border: "1px solid rgba(56,189,248,0.15)", minHeight: "130px" }}
          >
            {/* Water level visual */}
            <div
              className="absolute inset-x-0 bottom-0 rounded-b-xl pointer-events-none transition-all"
              style={{
                height: `${storagePercentage}%`,
                background: "linear-gradient(180deg, rgba(14,165,233,0.12) 0%, rgba(2,132,199,0.06) 100%)",
              }}
            />
            {/* Animated wave */}
            <div
              className="absolute left-0 right-0 h-1 pointer-events-none"
              style={{
                bottom: `${storagePercentage}%`,
                background: "linear-gradient(90deg, transparent, rgba(56,189,248,0.5), transparent)",
                animation: "shimmer 3s ease-in-out infinite",
                backgroundSize: "200% 100%",
              }}
            />
            <div className="relative z-10">
              <div className="text-[9px] font-bold uppercase tracking-widest text-sky-400/60 mb-1">
                Bhakra Reservoir
              </div>
              <div className="text-xl font-black text-sky-300">
                {(reservoirStorage / 1000).toFixed(0)}k AF
              </div>
              <div className="text-[9px] text-slate-600 mt-0.5">
                of {(reservoirCapacity / 1000).toFixed(0)}k AF capacity
              </div>
            </div>
            <div className="relative z-10 mt-3">
              <div className="flex justify-between text-[9px] text-slate-500 mb-1">
                <span>Storage Level</span>
                <span className="text-sky-400 font-bold">{storagePercentage.toFixed(1)}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill-indigo" style={{ width: `${storagePercentage}%` }} />
              </div>
            </div>
          </div>

          {/* Canal Flow */}
          <div
            className="rounded-xl p-4 flex flex-col justify-between"
            style={{ background: "rgba(6,13,24,0.7)", border: "1px solid rgba(16,185,129,0.15)", minHeight: "130px" }}
          >
            <div>
              <div className="text-[9px] font-bold uppercase tracking-widest text-emerald-400/60 mb-1">
                Canal Intake Flow
              </div>
              <div className="text-xl font-black text-emerald-300">
                {canalFlow.toLocaleString()} <span className="text-sm font-normal text-emerald-400/60">cusec</span>
              </div>
              <div className="text-[9px] text-slate-600 mt-0.5">Capacity: 1,500 cusec</div>
            </div>
            <div className="mt-3">
              <div className="flex justify-between text-[9px] text-slate-500 mb-1">
                <span>Utilization</span>
                <span className="text-emerald-400 font-bold">{canalUtilization.toFixed(0)}%</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill-emerald" style={{ width: `${canalUtilization}%` }} />
              </div>
            </div>
          </div>
        </div>

        {/* Priority zones */}
        <div>
          <div
            className="section-header mb-3"
            style={{ fontSize: "9px", letterSpacing: "0.1em" }}
          >
            <Waves className="w-3 h-3 text-sky-400" />
            Canal Delivery Priority Zones
          </div>

          <div className="space-y-2 max-h-[170px] overflow-y-auto pr-0.5">
            {priorityFields.length === 0 ? (
              <div className="text-center text-[11px] text-slate-600 py-6 flex flex-col items-center gap-2">
                <Droplets className="w-6 h-6 text-emerald-400/20" />
                All zones saturated — normal flow operations
              </div>
            ) : (
              priorityFields.map((f: any, idx: number) => {
                const isImmediate = f.properties.stress_score > 0.6;
                return (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 rounded-xl transition-all duration-200"
                    style={
                      isImmediate
                        ? { background: "rgba(244,63,94,0.06)", border: "1px solid rgba(244,63,94,0.15)" }
                        : { background: "rgba(6,13,24,0.5)", border: "1px solid rgba(255,255,255,0.05)" }
                    }
                  >
                    <div>
                      <div className="text-[11px] font-semibold text-slate-200">{f.properties.name}</div>
                      <div className="text-[9px] text-slate-600 capitalize">{f.properties.village} · {f.properties.crop_type}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <div className="text-[9px] text-slate-500">Stress</div>
                        <div
                          className="text-[11px] font-black"
                          style={{ color: isImmediate ? "#FB7185" : "#FCD34D" }}
                        >
                          {(f.properties.stress_score * 100).toFixed(0)}%
                        </div>
                      </div>
                      <span
                        className="chip text-[9px] font-bold"
                        style={
                          isImmediate
                            ? { background: "rgba(244,63,94,0.15)", border: "1px solid rgba(244,63,94,0.3)", color: "#FB7185" }
                            : { background: "rgba(245,158,11,0.15)", border: "1px solid rgba(245,158,11,0.3)", color: "#FCD34D" }
                        }
                      >
                        {isImmediate ? "🚨 Now" : "⏳ Soon"}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
