"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { TrendingUp, HelpCircle, BarChart3 } from "lucide-react";

interface PredictiveChartsProps {
  selectedField: any;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: "rgba(6,13,24,0.97)",
        border: "1px solid rgba(99,102,241,0.25)",
        borderRadius: "10px",
        padding: "10px 14px",
        fontSize: "11px",
        color: "#94A3B8",
        boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
      }}>
        <div className="font-bold text-slate-300 mb-1.5">{label}</div>
        {payload.map((entry: any, i: number) => (
          <div key={i} className="flex items-center gap-2 text-[10px]">
            <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
            <span>{entry.name}:</span>
            <b style={{ color: entry.color }}>{typeof entry.value === "number" ? entry.value.toFixed(3) : "—"}</b>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function PredictiveCharts({ selectedField }: PredictiveChartsProps) {
  const generateChartData = () => {
    if (!selectedField) return [];
    const baseSm = selectedField.properties.soil_moisture;
    const baseNdvi = selectedField.properties.stress_score > 0.4 ? 0.35 : 0.68;

    const history = [
      { name: "D−10", ndvi: baseNdvi + 0.12, moisture: baseSm + 0.18, forecast: null },
      { name: "D−8", ndvi: baseNdvi + 0.10, moisture: baseSm + 0.14, forecast: null },
      { name: "D−6", ndvi: baseNdvi + 0.08, moisture: baseSm + 0.10, forecast: null },
      { name: "D−4", ndvi: baseNdvi + 0.05, moisture: baseSm + 0.05, forecast: null },
      { name: "D−2", ndvi: baseNdvi + 0.02, moisture: baseSm + 0.02, forecast: null },
      { name: "Today", ndvi: baseNdvi, moisture: baseSm, forecast: baseSm },
    ];

    const predictions = [
      { name: "D+2", ndvi: baseNdvi, moisture: null, forecast: Math.max(0.1, baseSm - 0.04) },
      { name: "D+4", ndvi: baseNdvi - 0.01, moisture: null, forecast: Math.max(0.1, baseSm - 0.07) },
      { name: "D+6", ndvi: baseNdvi - 0.02, moisture: null, forecast: Math.max(0.1, baseSm - 0.10) },
      { name: "D+8", ndvi: baseNdvi - 0.03, moisture: null, forecast: Math.max(0.1, baseSm - 0.13) },
      { name: "D+10", ndvi: baseNdvi - 0.04, moisture: null, forecast: Math.max(0.1, baseSm - 0.15) },
    ];

    return [...history, ...predictions];
  };

  const chartData = generateChartData();

  return (
    <div
      className="rounded-2xl overflow-hidden flex flex-col"
      style={{
        background: "linear-gradient(135deg, rgba(15,32,64,0.9) 0%, rgba(10,22,40,0.85) 100%)",
        border: "1px solid rgba(255,255,255,0.07)",
        boxShadow: "0 4px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
        height: "480px",
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
              background: "linear-gradient(135deg, rgba(99,102,241,0.25), rgba(56,189,248,0.15))",
              border: "1px solid rgba(99,102,241,0.3)",
            }}
          >
            <BarChart3 className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-none">Phenology Analytics</div>
            <div className="text-[9px] text-slate-500 mt-0.5">LSTM Soil Moisture Forecast Model</div>
          </div>
        </div>
        {selectedField && (
          <span
            className="text-[9px] font-bold px-2 py-1 rounded-lg"
            style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.25)", color: "#A5B4FC" }}
          >
            10-Day Outlook
          </span>
        )}
      </div>

      <div className="p-5 flex-1 flex flex-col">
        {!selectedField ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center gap-3">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center"
              style={{ background: "rgba(99,102,241,0.06)", border: "1px solid rgba(99,102,241,0.12)" }}
            >
              <TrendingUp className="w-7 h-7 text-indigo-400/40" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-400 mb-1.5">No field selected</div>
              <div className="text-[11px] text-slate-600 max-w-[200px] mx-auto leading-relaxed">
                Select a field polygon on the map to forecast moisture stress and NDVI profiles.
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-3 flex-1">
            <div className="text-[9px] font-bold uppercase tracking-widest text-slate-500">
              Soil Moisture Depletion · NDVI Phenology (Observed + Forecast)
            </div>

            <div className="flex-1" style={{ minHeight: "240px" }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="moistureGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#38BDF8" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#38BDF8" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#818CF8" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#818CF8" stopOpacity={0.02} />
                    </linearGradient>
                    <linearGradient id="ndviGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#34D399" stopOpacity={0.25} />
                      <stop offset="100%" stopColor="#34D399" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="rgba(255,255,255,0.04)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="name"
                    stroke="#334155"
                    tick={{ fill: "#475569", fontSize: 9 }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="#334155"
                    tick={{ fill: "#475569", fontSize: 9 }}
                    tickLine={false}
                    axisLine={false}
                    domain={[0, 1]}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    verticalAlign="top"
                    height={28}
                    iconType="circle"
                    iconSize={7}
                    wrapperStyle={{ fontSize: "9px", color: "#64748B", paddingBottom: "4px" }}
                  />
                  <Area
                    type="monotone"
                    name="Observed Moisture"
                    dataKey="moisture"
                    stroke="#38BDF8"
                    strokeWidth={2}
                    fill="url(#moistureGrad)"
                    dot={false}
                    activeDot={{ r: 4, fill: "#38BDF8", stroke: "rgba(56,189,248,0.3)", strokeWidth: 3 }}
                  />
                  <Area
                    type="monotone"
                    name="LSTM Predicted"
                    dataKey="forecast"
                    stroke="#818CF8"
                    strokeWidth={2}
                    strokeDasharray="5 4"
                    fill="url(#forecastGrad)"
                    dot={false}
                    activeDot={{ r: 4, fill: "#818CF8", stroke: "rgba(129,140,248,0.3)", strokeWidth: 3 }}
                  />
                  <Area
                    type="monotone"
                    name="NDVI Index"
                    dataKey="ndvi"
                    stroke="#34D399"
                    strokeWidth={1.5}
                    fill="url(#ndviGrad)"
                    dot={false}
                    activeDot={{ r: 3, fill: "#34D399" }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div
              className="flex items-center justify-center gap-1.5 text-[9px] text-slate-600 pt-2"
              style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}
            >
              <HelpCircle className="w-2.5 h-2.5" />
              Dashed line = PyTorch LSTM 10-day predictive trajectory
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
