"use client";

import { Droplets, Activity, Percent, ArrowDown } from "lucide-react";

interface CanalCommandTwinProps {
  summary: any;
  fieldsGeojson: any;
}

export default function CanalCommandTwin({ summary, fieldsGeojson }: CanalCommandTwinProps) {
  // Compute priority list based on moisture stress scores of fields
  const fields = fieldsGeojson?.features || [];
  const priorityFields = [...fields]
    .filter((f: any) => f.properties.stress_score > 0.15)
    .sort((a: any, b: any) => b.properties.stress_score - a.properties.stress_score);

  // Compute Reservoir Stats
  const reservoirCapacity = 500000; // Acre-feet
  const reservoirStorage = 385420;  // Current Storage Acre-feet
  const storagePercentage = (reservoirStorage / reservoirCapacity) * 100;
  
  return (
    <div className="p-5 rounded-xl border border-gray-800 glass-panel h-full">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-bold text-gray-100 flex items-center gap-2">
          <Activity className="w-5 h-5 text-sky-400" />
          Digital Twin Command Simulation
        </h3>
        <span className="text-[10px] uppercase font-bold text-sky-400 bg-sky-950 px-2 py-0.5 rounded border border-sky-800">
          Live Flow Network
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        {/* Reservoir Status */}
        <div className="p-4 rounded-lg bg-slate-900 border border-gray-800 relative overflow-hidden flex flex-col justify-between min-h-[140px]">
          {/* Animated Water Wave background */}
          <div className="absolute inset-x-0 bottom-0 bg-blue-950 bg-opacity-20 h-1/2 overflow-hidden pointer-events-none">
            <div className="w-[200%] h-[200%] bg-sky-900 opacity-20 rounded-[40%] absolute -bottom-1/2 -left-1/2 animate-spin duration-[15s]" />
          </div>
          
          <div className="relative z-10">
            <div className="text-xs text-gray-400 uppercase font-semibold">Bhakra Reservoir Level</div>
            <div className="text-2xl font-black mt-1 text-sky-400">{reservoirStorage.toLocaleString()} AF</div>
            <div className="text-[10px] text-gray-500 mt-0.5">Capacity: {reservoirCapacity.toLocaleString()} AF</div>
          </div>
          
          <div className="relative z-10 flex items-center justify-between border-t border-gray-800 pt-2 mt-4">
            <span className="text-[11px] text-gray-400 flex items-center gap-1">
              <Percent className="w-3.5 h-3.5 text-sky-400" /> Storage Capacity
            </span>
            <span className="font-bold text-xs text-sky-300">{storagePercentage.toFixed(1)}%</span>
          </div>
        </div>

        {/* Total Irrigation Outflow */}
        <div className="p-4 rounded-lg bg-slate-900 border border-gray-800 flex flex-col justify-between min-h-[140px]">
          <div>
            <div className="text-xs text-gray-400 uppercase font-semibold">Canal Command Flow Rate</div>
            <div className="text-2xl font-black mt-1 text-emerald-400">
              {summary?.active_command_canal_flow_cusec || 1250} cusec
            </div>
            <div className="text-[10px] text-gray-500 mt-0.5">Assigned Capacity: 1,500 cusec</div>
          </div>

          <div className="flex items-center justify-between border-t border-gray-800 pt-2 mt-4">
            <span className="text-[11px] text-gray-400 flex items-center gap-1">
              <Droplets className="w-3.5 h-3.5 text-emerald-400" /> Active Canal Delivery
            </span>
            <span className="font-bold text-xs text-emerald-300">
              {((summary?.active_command_canal_flow_cusec || 1250) / 1500 * 100).toFixed(0)}% Utilized
            </span>
          </div>
        </div>
      </div>

      {/* Irrigation Priority Zones */}
      <div>
        <h4 className="text-xs font-semibold text-gray-400 uppercase mb-2">Canal Delivery Priority Zones</h4>
        <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1">
          {priorityFields.length === 0 ? (
            <div className="text-center text-xs text-gray-500 py-6">
              All zones saturated. Normal flow operations.
            </div>
          ) : (
            priorityFields.map((f: any, idx: number) => {
              const priority = f.properties.stress_score > 0.6 ? "Immediate" : "Medium";
              return (
                <div key={idx} className="flex justify-between items-center p-2 rounded bg-slate-900 bg-opacity-50 border border-gray-800 hover:border-gray-700 transition">
                  <div className="text-xs">
                    <div className="font-semibold text-gray-200">{f.properties.name}</div>
                    <div className="text-[10px] text-gray-500">Village: {f.properties.village}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] text-gray-400 capitalize">{f.properties.crop_type}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      priority === "Immediate" 
                        ? "bg-rose-950 text-rose-400 border border-rose-800" 
                        : "bg-amber-950 text-amber-400 border border-amber-800"
                    }`}>
                      {priority}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
