"use client";

import { CheckCircle2, AlertTriangle, Play, HelpCircle, Save } from "lucide-react";

interface IrrigationAdvisoryProps {
  advisories: any[];
  selectedField: any;
  onTriggerAdvisory: (fieldId: number) => void;
  loading: boolean;
}

export default function IrrigationAdvisory({
  advisories,
  selectedField,
  onTriggerAdvisory,
  loading
}: IrrigationAdvisoryProps) {
  const latestAdv = advisories && advisories.length > 0 ? advisories[0] : null;

  return (
    <div className="p-5 rounded-xl border border-gray-800 glass-panel h-full flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-4.5">
          <h3 className="font-bold text-gray-100 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            Irrigation Advisory AI
          </h3>
          {selectedField && (
            <button
              onClick={() => onTriggerAdvisory(selectedField.id)}
              disabled={loading}
              className="text-[10px] bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold py-1 px-2.5 rounded transition flex items-center gap-1"
            >
              <Play className="w-3 h-3 fill-white" />
              {loading ? "Recomputing..." : "Compute Advice"}
            </button>
          )}
        </div>

        {!selectedField ? (
          <div className="text-center py-10 text-gray-500 text-xs flex flex-col items-center justify-center gap-2">
            <HelpCircle className="w-8 h-8 text-gray-600 animate-bounce" />
            Select a field polygon on the map to evaluate water stress and advisory suggestions.
          </div>
        ) : (
          <div className="space-y-4">
            {/* Field context header */}
            <div className="flex justify-between items-center p-2 rounded bg-slate-900 border border-gray-800 text-xs">
              <span className="text-gray-400 font-semibold">{selectedField.properties.name}</span>
              <span className="text-amber-400 uppercase font-bold text-[10px]">
                {selectedField.properties.crop_type}
              </span>
            </div>

            {latestAdv ? (
              <div className="space-y-4">
                {/* Advisory Action urgency band */}
                <div className={`p-3 rounded-lg border flex items-center gap-2.5 ${
                  latestAdv.recommended_action === "Immediate irrigation" 
                    ? "bg-rose-950 bg-opacity-40 border-rose-800 text-rose-300"
                    : latestAdv.recommended_action === "Irrigate in 2 days"
                    ? "bg-amber-950 bg-opacity-40 border-amber-800 text-amber-300"
                    : latestAdv.recommended_action === "Irrigate in 5 days"
                    ? "bg-yellow-950 bg-opacity-20 border-yellow-800 text-yellow-300"
                    : "bg-emerald-950 bg-opacity-20 border-emerald-800 text-emerald-300"
                }`}>
                  <AlertTriangle className="w-5 h-5 shrink-0" />
                  <div>
                    <div className="text-[10px] uppercase font-bold tracking-wider">Recommended Action</div>
                    <div className="text-xs font-black">{latestAdv.recommended_action}</div>
                  </div>
                </div>

                {/* Key Metrics */}
                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2.5 rounded bg-slate-900 border border-gray-800 text-center">
                    <div className="text-[9px] text-gray-500 uppercase">Req Depth</div>
                    <div className="text-sm font-black text-gray-100 mt-0.5">{latestAdv.recommended_depth_mm} mm</div>
                  </div>
                  <div className="p-2.5 rounded bg-slate-900 border border-gray-800 text-center">
                    <div className="text-[9px] text-gray-500 uppercase">Volume Needed</div>
                    <div className="text-sm font-black text-gray-100 mt-0.5">{Math.round(latestAdv.recommended_volume_m3)} m³</div>
                  </div>
                  <div className="p-2.5 rounded bg-slate-900 border border-gray-800 text-center flex flex-col justify-between items-center">
                    <div className="text-[9px] text-emerald-500 uppercase font-semibold flex items-center gap-0.5">
                      <Save className="w-2.5 h-2.5" /> Savings
                    </div>
                    <div className="text-sm font-black text-emerald-400 mt-0.5">{Math.round(latestAdv.water_savings_m3)} m³</div>
                  </div>
                </div>

                {/* Advisory Text */}
                <div className="p-3 rounded bg-slate-950 border border-gray-900 text-[11px] leading-relaxed text-gray-400 italic">
                  "{latestAdv.advisory_text}"
                </div>
              </div>
            ) : (
              <div className="text-center py-6 text-gray-500 text-xs">
                No active advisory found for this crop stage. Click 'Compute Advice' above to run the FAO-56 deficit engine.
              </div>
            )}
          </div>
        )}
      </div>

      {latestAdv && selectedField && (
        <div className="text-[9px] text-gray-500 border-t border-gray-800 pt-3 mt-4 text-center">
          Advisory generated using FAO-56 Penman-Monteith equations & Soil Depletion indices.
        </div>
      )}
    </div>
  );
}
