"use client";

import { AlertOctagon, ShieldAlert, Check, Bell, CheckCircle2, Mail } from "lucide-react";

interface AlertManagerProps {
  alerts: any[];
  onMarkRead: (id: number) => void;
}

export default function AlertManager({ alerts, onMarkRead }: AlertManagerProps) {
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
              background: alerts.length > 0
                ? "linear-gradient(135deg, rgba(244,63,94,0.2), rgba(190,18,60,0.15))"
                : "linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.15))",
              border: alerts.length > 0
                ? "1px solid rgba(244,63,94,0.3)"
                : "1px solid rgba(16,185,129,0.3)",
            }}
          >
            {alerts.length > 0
              ? <AlertOctagon className="w-4 h-4 text-rose-400" />
              : <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            }
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-none">Warning Dispatch</div>
            <div className="text-[9px] text-slate-500 mt-0.5">Automated anomaly alerts</div>
          </div>
        </div>
        {alerts.length > 0 ? (
          <span
            className="flex items-center gap-1 text-[9px] font-black px-2 py-1 rounded-lg"
            style={{ background: "rgba(244,63,94,0.15)", border: "1px solid rgba(244,63,94,0.3)", color: "#FB7185" }}
          >
            <ShieldAlert className="w-3 h-3" />
            {alerts.length} active
          </span>
        ) : (
          <span
            className="text-[9px] font-bold px-2 py-1 rounded-lg"
            style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.25)", color: "#34D399" }}
          >
            All Clear
          </span>
        )}
      </div>

      <div className="p-4 flex-1">
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center text-center gap-3 py-8">
            <div
              className="w-12 h-12 rounded-2xl flex items-center justify-center"
              style={{ background: "rgba(16,185,129,0.07)", border: "1px solid rgba(16,185,129,0.15)" }}
            >
              <Bell className="w-6 h-6 text-emerald-400/50" />
            </div>
            <div>
              <div className="text-sm font-bold text-emerald-400/70 mb-1">System Normal</div>
              <div className="text-[10px] text-slate-600 max-w-[180px] mx-auto leading-relaxed">
                All agricultural metrics within optimal FAO safety bounds.
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-2.5 max-h-[280px] overflow-y-auto pr-1">
            {alerts.map((item) => (
              <div
                key={item.id}
                className="p-3.5 rounded-xl transition-all duration-200"
                style={
                  item.severity === "critical"
                    ? { background: "rgba(244,63,94,0.08)", border: "1px solid rgba(244,63,94,0.2)" }
                    : { background: "rgba(245,158,11,0.08)", border: "1px solid rgba(245,158,11,0.2)" }
                }
              >
                <div className="flex items-start justify-between gap-2.5">
                  <div className="flex items-start gap-2 flex-1 min-w-0">
                    <div
                      className="w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 mt-0.5"
                      style={
                        item.severity === "critical"
                          ? { background: "rgba(244,63,94,0.2)" }
                          : { background: "rgba(245,158,11,0.2)" }
                      }
                    >
                      <ShieldAlert
                        className={`w-3 h-3 ${item.severity === "critical" ? "text-rose-400" : "text-amber-400"}`}
                      />
                    </div>
                    <div className="text-[11px] font-medium text-slate-200 leading-relaxed">
                      {item.message}
                    </div>
                  </div>
                  <button
                    onClick={() => onMarkRead(item.id)}
                    className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition-all duration-200 hover:scale-110"
                    style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)" }}
                    title="Acknowledge alert"
                  >
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  </button>
                </div>

                <div className="flex items-center justify-between mt-2.5 text-[9px] text-slate-600">
                  <span className="flex items-center gap-1">
                    <Mail className="w-3 h-3" />
                    Dispatched to Admin & Farmer
                  </span>
                  <span className="font-mono">
                    {new Date(item.sent_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        <div
          className="mt-4 pt-3 text-center text-[9px] text-slate-700"
          style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}
        >
          Alerts auto-trigger when FAO-56 depletion thresholds are violated
        </div>
      </div>
    </div>
  );
}
