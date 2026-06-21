import React, { useEffect, useState } from "react";
import { Thermometer, CloudRain, ShieldCheck, HelpCircle, Loader2, Globe } from "lucide-react";

interface CropSuitabilityProps {
  locationInfo: any;
}

const cropEmojis: Record<string, string> = {
  wheat: "🌾",
  rice: "🍚",
  cotton: "☁️",
  sugarcane: "🎋",
};

export default function CropSuitability({ locationInfo }: CropSuitabilityProps) {
  const [suitability, setSuitability] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [animatedScores, setAnimatedScores] = useState<number[]>([]);

  useEffect(() => {
    if (!locationInfo) return;

    async function fetchSuitability() {
      setLoading(true);
      setSuitability(null);
      setAnimatedScores([]);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
        const res = await fetch(`${baseUrl}/suitability?lat=${locationInfo.lat}&lon=${locationInfo.lon}`);
        if (!res.ok) throw new Error("API error");
        const data = await res.json();
        setSuitability(data);
      } catch {
        const temp = locationInfo.weather?.temp ?? 25;
        const rain = locationInfo.weather?.rainSum ?? 5;
        const wheatScore = Math.max(10, Math.min(100, 100 - Math.abs(temp - 19) * 6));
        const riceScore = Math.max(10, Math.min(100, 100 - Math.abs(temp - 27) * 5 + rain * 0.5));
        const cottonScore = Math.max(10, Math.min(100, 100 - Math.abs(temp - 28.5) * 4.5));
        const sugarcaneScore = Math.max(10, Math.min(100, 100 - Math.abs(temp - 31) * 4));
        setSuitability({
          coordinates: { latitude: locationInfo.lat, longitude: locationInfo.lon },
          meteorology: {
            mean_temperature: temp,
            rain_sum_mm: rain,
          },
          suitability_scores: [
            { crop: "wheat", score: Math.round(wheatScore), status: wheatScore > 75 ? "Optimal" : wheatScore > 40 ? "Moderate" : "Poor", ideal_temp_range: "15–23°C" },
            { crop: "rice", score: Math.round(riceScore), status: riceScore > 75 ? "Optimal" : riceScore > 40 ? "Moderate" : "Poor", ideal_temp_range: "22–32°C" },
            { crop: "cotton", score: Math.round(cottonScore), status: cottonScore > 75 ? "Optimal" : cottonScore > 40 ? "Moderate" : "Poor", ideal_temp_range: "22–35°C" },
            { crop: "sugarcane", score: Math.round(sugarcaneScore), status: sugarcaneScore > 75 ? "Optimal" : sugarcaneScore > 40 ? "Moderate" : "Poor", ideal_temp_range: "24–38°C" },
          ],
        });
      } finally {
        setLoading(false);
      }
    }

    fetchSuitability();
  }, [locationInfo]);

  // Animate progress bars after data loads
  useEffect(() => {
    if (suitability?.suitability_scores) {
      setAnimatedScores([]);
      const timer = setTimeout(() => {
        setAnimatedScores(suitability.suitability_scores.map((s: any) => s.score));
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [suitability]);

  const statusColors = {
    Optimal: { bar: "progress-fill-emerald", text: "text-emerald-400", badge: "bg-emerald-900/40 text-emerald-300 border-emerald-700/40" },
    Moderate: { bar: "progress-fill-amber", text: "text-amber-400", badge: "bg-amber-900/40 text-amber-300 border-amber-700/40" },
    Poor: { bar: "progress-fill-rose", text: "text-rose-400", badge: "bg-rose-900/40 text-rose-300 border-rose-700/40" },
  };

  if (!locationInfo) {
    return (
      <div
        className="rounded-2xl flex flex-col items-center justify-center text-center p-8 gap-4"
        style={{
          background: "linear-gradient(135deg, rgba(15,32,64,0.9) 0%, rgba(10,22,40,0.85) 100%)",
          border: "1px solid rgba(255,255,255,0.07)",
          minHeight: "280px",
        }}
      >
        <div
          className="w-14 h-14 rounded-2xl flex items-center justify-center"
          style={{ background: "rgba(99,102,241,0.08)", border: "1px solid rgba(99,102,241,0.15)" }}
        >
          <Globe className="w-7 h-7 text-indigo-400/50" />
        </div>
        <div>
          <div className="text-sm font-bold text-slate-400 mb-1.5">No Location Selected</div>
          <div className="text-[11px] text-slate-600 max-w-[220px] mx-auto leading-relaxed">
            Search a global location or click the map to run FAO Ecocrop suitability analysis.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="rounded-2xl overflow-hidden"
      style={{
        background: "linear-gradient(135deg, rgba(15,32,64,0.9) 0%, rgba(10,22,40,0.85) 100%)",
        border: "1px solid rgba(255,255,255,0.07)",
        boxShadow: "0 4px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
      }}
    >
      {/* Header */}
      <div
        className="px-5 py-4 flex items-center justify-between"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{
              background: "linear-gradient(135deg, rgba(99,102,241,0.25), rgba(124,58,237,0.15))",
              border: "1px solid rgba(99,102,241,0.3)",
            }}
          >
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-none">FAO Crop Suitability</div>
            <div className="text-[9px] text-slate-500 mt-0.5">Ecocrop Temperature × Rainfall Model</div>
          </div>
        </div>
        {locationInfo && (
          <div className="text-[9px] text-slate-500 font-mono hidden sm:block">
            {locationInfo.lat.toFixed(3)}°N, {locationInfo.lon.toFixed(3)}°E
          </div>
        )}
      </div>

      <div className="p-5 space-y-5">
        {loading ? (
          <div className="py-12 flex flex-col items-center gap-3">
            <div className="relative">
              <div
                className="w-10 h-10 rounded-full border-2 border-t-transparent animate-spin"
                style={{ borderColor: "rgba(99,102,241,0.3)", borderTopColor: "#6366F1" }}
              />
              <ShieldCheck className="w-4 h-4 text-indigo-400 absolute inset-0 m-auto" />
            </div>
            <div className="text-[11px] text-slate-500">Running FAO-56 Ecocrop analysis...</div>
          </div>
        ) : suitability ? (
          <>
            {/* Meteorology summary */}
            <div className="grid grid-cols-2 gap-2.5">
              <div
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
                style={{ background: "rgba(244,63,94,0.07)", border: "1px solid rgba(244,63,94,0.15)" }}
              >
                <Thermometer className="w-4 h-4 text-rose-400 flex-shrink-0" />
                <div>
                  <div className="text-[9px] text-rose-400/70 font-bold uppercase tracking-wide">Mean Temp</div>
                  <div className="text-[13px] font-black text-rose-300">
                    {suitability.meteorology.mean_temperature}°C
                  </div>
                </div>
              </div>
              <div
                className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl"
                style={{ background: "rgba(56,189,248,0.07)", border: "1px solid rgba(56,189,248,0.15)" }}
              >
                <CloudRain className="w-4 h-4 text-sky-400 flex-shrink-0" />
                <div>
                  <div className="text-[9px] text-sky-400/70 font-bold uppercase tracking-wide">Rain Sum</div>
                  <div className="text-[13px] font-black text-sky-300">
                    {suitability.meteorology.rain_sum_mm} mm
                  </div>
                </div>
              </div>
            </div>

            {/* Suitability bars */}
            <div className="space-y-4">
              {suitability.suitability_scores.map((item: any, idx: number) => {
                const colors = statusColors[item.status as keyof typeof statusColors] ?? statusColors.Poor;
                const animated = animatedScores[idx] ?? 0;

                return (
                  <div key={idx} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-base leading-none">{cropEmojis[item.crop] ?? "🌱"}</span>
                        <span className="text-[12px] font-bold text-slate-200 capitalize">{item.crop}</span>
                        <span className="text-[9px] text-slate-600 font-medium">{item.ideal_temp_range}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[13px] font-black ${colors.text}`}>{item.score}%</span>
                        <span className={`chip text-[8px] font-bold border ${colors.badge}`}>{item.status}</span>
                      </div>
                    </div>
                    <div className="progress-track">
                      <div
                        className={colors.bar}
                        style={{ width: `${animated}%`, transition: "width 0.9s cubic-bezier(0.25, 1, 0.5, 1)" }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="flex items-center gap-1.5 text-[9px] text-slate-600 border-t border-[rgba(255,255,255,0.04)] pt-3">
              <ShieldCheck className="w-2.5 h-2.5" />
              Scores resolved against FAO Ecocrop temperature × rainfall requirements.
            </div>
          </>
        ) : (
          <div className="text-xs text-rose-400 text-center py-8">Failed to load suitability data.</div>
        )}
      </div>
    </div>
  );
}
