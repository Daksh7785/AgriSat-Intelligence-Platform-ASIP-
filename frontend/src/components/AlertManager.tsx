"use client";

import { AlertOctagon, Mail, ShieldAlert, Check } from "lucide-react";

interface AlertManagerProps {
  alerts: any[];
  onMarkRead: (id: number) => void;
}

export default function AlertManager({ alerts, onMarkRead }: AlertManagerProps) {
  return (
    <div className="p-5 rounded-xl border border-gray-800 glass-panel h-full flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-bold text-gray-100 flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-500" />
            Active Warning Dispatch
          </h3>
          <span className="text-[9px] bg-rose-950 text-rose-400 font-bold px-1.5 py-0.5 rounded border border-rose-800 flex items-center gap-1">
            <ShieldAlert className="w-3 h-3" />
            {alerts.length} Warnings
          </span>
        </div>

        <div className="space-y-3.5 max-h-[175px] overflow-y-auto pr-1">
          {alerts.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-xs">
              System normal. All agricultural metrics are within optimal safety bounds.
            </div>
          ) : (
            alerts.map((item) => (
              <div
                key={item.id}
                className={`p-3 rounded-lg border flex flex-col gap-1.5 transition ${
                  item.severity === "critical"
                    ? "bg-rose-950 bg-opacity-20 border-rose-900"
                    : "bg-amber-950 bg-opacity-20 border-amber-900"
                }`}
              >
                <div className="flex justify-between items-start gap-2">
                  <div className="text-[11px] font-semibold text-gray-200 leading-relaxed">
                    {item.message}
                  </div>
                  <button
                    onClick={() => onMarkRead(item.id)}
                    className="p-1 rounded bg-slate-900 hover:bg-slate-800 text-gray-400 hover:text-emerald-400 transition"
                    title="Mark Acknowledged"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </button>
                </div>
                
                <div className="flex justify-between items-center text-[9px] text-gray-500 font-medium">
                  <span className="flex items-center gap-1">
                    <Mail className="w-3.5 h-3.5 text-gray-400" /> Sent to Admin & Farmer
                  </span>
                  <span>{new Date(item.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="text-[9px] text-gray-500 mt-4 border-t border-gray-800 pt-3 text-center">
        Alerts trigger automatically when moisture depletion models violate critical bounds.
      </div>
    </div>
  );
}
