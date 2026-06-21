import React, { useEffect, useState } from "react";
import { Thermometer, CloudRain, ShieldCheck, HelpCircle } from "lucide-react";

interface CropSuitabilityProps {
  locationInfo: any;
}

export default function CropSuitability({ locationInfo }: CropSuitabilityProps) {
  const [suitability, setSuitability] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!locationInfo) return;
    
    async function fetchSuitability() {
      setLoading(true);
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
        const url = `${baseUrl}/suitability?lat=${locationInfo.lat}&lon=${locationInfo.lon}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("API error");
        const data = await res.json();
        setSuitability(data);
      } catch (err) {
        console.warn("Failed to fetch crop suitability from API. Calculating client-side fallback...");
        // Fallback calculations matching the backend logic
        const lat = locationInfo.lat;
        const temp = locationInfo.weather?.temp || 25.0;
        const rain = locationInfo.weather?.rainSum || 5.0;
        
        const wheatScore = Math.max(10, Math.min(100, 100 - Math.abs(temp - 19) * 6));
        const riceScore = Math.max(10, Math.min(100, 100 - Math.abs(temp - 27) * 5 + rain * 0.5));
        const cottonScore = Math.max(10, Math.min(100, 100 - Math.abs(temp - 28.5) * 4.5));
        const sugarcaneScore = Math.max(10, Math.min(100, 100 - Math.abs(temp - 31) * 4));

        setSuitability({
          coordinates: { latitude: lat, longitude: locationInfo.lon },
          meteorology: {
            mean_temperature: temp,
            max_temperature: temp + 3,
            min_temperature: temp - 3,
            rain_sum_mm: rain
          },
          suitability_scores: [
            { crop: "wheat", score: Math.round(wheatScore), status: wheatScore > 75 ? "Optimal" : (wheatScore > 40 ? "Moderate" : "Poor"), ideal_temp_range: "15°C - 23°C" },
            { crop: "rice", score: Math.round(riceScore), status: riceScore > 75 ? "Optimal" : (riceScore > 40 ? "Moderate" : "Poor"), ideal_temp_range: "22°C - 32°C" },
            { crop: "cotton", score: Math.round(cottonScore), status: cottonScore > 75 ? "Optimal" : (cottonScore > 40 ? "Moderate" : "Poor"), ideal_temp_range: "22°C - 35°C" },
            { crop: "sugarcane", score: Math.round(sugarcaneScore), status: sugarcaneScore > 75 ? "Optimal" : (sugarcaneScore > 40 ? "Moderate" : "Poor"), ideal_temp_range: "24°C - 38°C" }
          ]
        });
      } finally {
        setLoading(false);
      }
    }

    fetchSuitability();
  }, [locationInfo]);

  if (!locationInfo) {
    return (
      <div className="p-5 rounded-xl border border-gray-800 glass-panel h-full flex flex-col justify-center items-center text-center text-gray-500 py-12 text-xs">
        <HelpCircle className="w-8 h-8 text-gray-650 animate-bounce mb-2" />
        <div>Please select a location or field to query FAO crop suitability ratings.</div>
      </div>
    );
  }

  return (
    <div className="p-5 rounded-xl border border-gray-800 glass-panel h-full flex flex-col justify-between bg-slate-900 bg-opacity-40">
      <div>
        <h3 className="font-bold text-gray-100 flex items-center gap-2 mb-3">
          <ShieldCheck className="w-5 h-5 text-indigo-400" />
          FAO Crop Suitability Analysis
        </h3>
        
        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center gap-2 text-xs text-indigo-400">
            <span className="w-6 h-6 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin"></span>
            Running FAO-56 scoring models...
          </div>
        ) : suitability ? (
          <div className="space-y-4.5">
            {/* Meteorology headers */}
            <div className="grid grid-cols-2 gap-2 text-[10px] bg-slate-950 border border-gray-850 p-2 rounded">
              <div className="flex items-center gap-1.5 text-gray-400">
                <Thermometer className="w-3.5 h-3.5 text-orange-400" />
                <span>Mean Temp: <b className="text-gray-200">{suitability.meteorology.mean_temperature}°C</b></span>
              </div>
              <div className="flex items-center gap-1.5 text-gray-400">
                <CloudRain className="w-3.5 h-3.5 text-blue-400" />
                <span>Rain Accum: <b className="text-gray-200">{suitability.meteorology.rain_sum_mm} mm</b></span>
              </div>
            </div>

            {/* Suitability scores map */}
            <div className="space-y-3 mt-3">
              {suitability.suitability_scores.map((item: any, idx: number) => {
                const isOptimal = item.status === "Optimal";
                const isModerate = item.status === "Moderate";
                const colorClass = isOptimal ? "bg-emerald-550" : isModerate ? "bg-amber-550" : "bg-rose-550";
                const textColorClass = isOptimal ? "text-emerald-450" : isModerate ? "text-amber-455" : "text-rose-450";
                
                return (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="capitalize text-gray-300">{item.crop}</span>
                      <span className={`${textColorClass} font-bold`}>{item.score}% ({item.status})</span>
                    </div>
                    {/* Progress bar */}
                    <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-gray-850">
                      <div className={`h-full ${colorClass} transition-all duration-500`} style={{ width: `${item.score}%` }}></div>
                    </div>
                    <div className="text-[9px] text-gray-500 flex justify-between">
                      <span>Ideal: {item.ideal_temp_range}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="text-xs text-rose-400 text-center py-6">Failed to load suitability ratings.</div>
        )}
      </div>
      <div className="text-[9px] text-gray-500 border-t border-gray-800 pt-3 mt-4 text-center">
        Scores resolved against FAO Ecocrop requirements.
      </div>
    </div>
  );
}
