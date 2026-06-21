"use client";

import React, { useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  Play,
  HelpCircle,
  Droplets,
  Volume2,
  VolumeX,
  Zap,
  Loader2,
} from "lucide-react";

interface IrrigationAdvisoryProps {
  advisories: any[];
  selectedField: any;
  onTriggerAdvisory: (fieldId: number) => void;
  loading: boolean;
}

const urgencyConfig: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  "Immediate irrigation": {
    bg: "rgba(244,63,94,0.1)",
    border: "rgba(244,63,94,0.3)",
    text: "#FB7185",
    icon: "🚨",
  },
  "Irrigate in 2 days": {
    bg: "rgba(245,158,11,0.1)",
    border: "rgba(245,158,11,0.3)",
    text: "#FCD34D",
    icon: "⚠️",
  },
  "Irrigate in 5 days": {
    bg: "rgba(234,179,8,0.08)",
    border: "rgba(234,179,8,0.25)",
    text: "#FDE68A",
    icon: "⏳",
  },
  default: {
    bg: "rgba(16,185,129,0.08)",
    border: "rgba(16,185,129,0.25)",
    text: "#34D399",
    icon: "✅",
  },
};

export default function IrrigationAdvisory({
  advisories,
  selectedField,
  onTriggerAdvisory,
  loading,
}: IrrigationAdvisoryProps) {
  const latestAdv = advisories?.length > 0 ? advisories[0] : null;
  const [speaking, setSpeaking] = useState(false);
  const [lang, setLang] = useState<"en" | "hi">("en");

  const handleSpeak = () => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    if (speaking) {
      window.speechSynthesis.cancel();
      setSpeaking(false);
      return;
    }
    const textToSpeak =
      lang === "hi"
        ? `सिंचाई की सलाह। सिफारिश की गई कार्रवाई: ${
            latestAdv.recommended_action === "Immediate irrigation"
              ? "तुरंत सिंचाई करें।"
              : latestAdv.recommended_action === "Irrigate in 2 days"
              ? "दो दिनों में सिंचाई करें।"
              : latestAdv.recommended_action === "Irrigate in 5 days"
              ? "पांच दिनों में सिंचाई करें।"
              : "सिंचाई की आवश्यकता नहीं है।"
          } अनुशंसित गहराई: ${latestAdv.recommended_depth_mm} मिलीमीटर।`
        : `Irrigation advisory. Action: ${latestAdv.recommended_action}. Depth: ${latestAdv.recommended_depth_mm} millimeters. ${latestAdv.advisory_text}`;

    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = lang === "hi" ? "hi-IN" : "en-US";
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const urgency = latestAdv
    ? urgencyConfig[latestAdv.recommended_action] ?? urgencyConfig.default
    : urgencyConfig.default;

  return (
    <div
      className="rounded-2xl flex flex-col h-full"
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
              background: "linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.15))",
              border: "1px solid rgba(16,185,129,0.3)",
            }}
          >
            <Droplets className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-none">Irrigation Advisory</div>
            <div className="text-[9px] text-slate-500 mt-0.5">FAO-56 Penman-Monteith Engine</div>
          </div>
        </div>
        {selectedField && (
          <button
            onClick={() => onTriggerAdvisory(selectedField.id)}
            disabled={loading}
            className="flex items-center gap-1.5 text-[10px] font-bold py-1.5 px-3 rounded-xl transition-all duration-200 disabled:opacity-50"
            style={{
              background: loading
                ? "rgba(16,185,129,0.1)"
                : "linear-gradient(135deg, rgba(5,150,105,0.3), rgba(16,185,129,0.2))",
              border: "1px solid rgba(16,185,129,0.35)",
              color: "#34D399",
            }}
          >
            {loading ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Play className="w-3 h-3 fill-current" />
            )}
            {loading ? "Computing..." : "Run Analysis"}
          </button>
        )}
      </div>

      <div className="p-5 flex-1 flex flex-col">
        {!selectedField ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center gap-3 py-8">
            <div
              className="w-14 h-14 rounded-2xl flex items-center justify-center"
              style={{ background: "rgba(16,185,129,0.06)", border: "1px solid rgba(16,185,129,0.12)" }}
            >
              <HelpCircle className="w-7 h-7 text-emerald-400/40" />
            </div>
            <div>
              <div className="text-sm font-bold text-slate-400 mb-1.5">No field selected</div>
              <div className="text-[11px] text-slate-600 max-w-[200px] mx-auto leading-relaxed">
                Click a field polygon on the map to evaluate FAO-56 water stress and irrigation depth.
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4 flex-1">
            {/* Field badge */}
            <div
              className="flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs"
              style={{ background: "rgba(6,13,24,0.7)", border: "1px solid rgba(255,255,255,0.06)" }}
            >
              <span className="font-semibold text-slate-200">{selectedField.properties.name}</span>
              <span
                className="chip font-bold uppercase"
                style={{ background: "rgba(245,158,11,0.15)", border: "1px solid rgba(245,158,11,0.3)", color: "#FCD34D" }}
              >
                {selectedField.properties.crop_type}
              </span>
            </div>

            {latestAdv ? (
              <div className="space-y-3.5">
                {/* Urgency band */}
                <div
                  className="p-4 rounded-xl flex items-center gap-3"
                  style={{ background: urgency.bg, border: `1px solid ${urgency.border}` }}
                >
                  <div className="text-xl leading-none">{urgency.icon}</div>
                  <div>
                    <div className="text-[9px] font-bold uppercase tracking-widest mb-0.5" style={{ color: urgency.text, opacity: 0.7 }}>
                      Recommended Action
                    </div>
                    <div className="text-sm font-black" style={{ color: urgency.text }}>
                      {latestAdv.recommended_action}
                    </div>
                  </div>
                </div>

                {/* Metrics grid */}
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { label: "Required Depth", value: `${latestAdv.recommended_depth_mm} mm`, color: "text-sky-400" },
                    { label: "Volume Needed", value: `${Math.round(latestAdv.recommended_volume_m3)} m³`, color: "text-indigo-400" },
                    { label: "Water Saved", value: `${Math.round(latestAdv.water_savings_m3)} m³`, color: "text-emerald-400" },
                  ].map(({ label, value, color }) => (
                    <div
                      key={label}
                      className="p-3 rounded-xl text-center"
                      style={{ background: "rgba(6,13,24,0.7)", border: "1px solid rgba(255,255,255,0.05)" }}
                    >
                      <div className="text-[8px] text-slate-500 uppercase font-bold tracking-wider mb-1">{label}</div>
                      <div className={`text-[13px] font-black ${color}`}>{value}</div>
                    </div>
                  ))}
                </div>

                {/* Voice controls */}
                <div
                  className="flex items-center justify-between px-3.5 py-2.5 rounded-xl"
                  style={{ background: "rgba(6,13,24,0.5)", border: "1px solid rgba(255,255,255,0.05)" }}
                >
                  <div className="flex items-center gap-2">
                    <Volume2 className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Audio Advisor</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <select
                      value={lang}
                      onChange={(e) => setLang(e.target.value as "en" | "hi")}
                      className="input-dark select-dark text-[10px] py-1 px-2 rounded-lg cursor-pointer"
                      style={{ background: "rgba(6,13,24,0.8)", border: "1px solid rgba(255,255,255,0.08)" }}
                    >
                      <option value="en">English</option>
                      <option value="hi">हिंदी</option>
                    </select>
                    <button
                      onClick={handleSpeak}
                      className="flex items-center gap-1 text-[10px] font-bold py-1 px-2.5 rounded-lg transition-all"
                      style={
                        speaking
                          ? { background: "rgba(244,63,94,0.2)", border: "1px solid rgba(244,63,94,0.35)", color: "#FB7185" }
                          : { background: "rgba(99,102,241,0.2)", border: "1px solid rgba(99,102,241,0.35)", color: "#A5B4FC" }
                      }
                    >
                      {speaking ? <VolumeX className="w-3 h-3" /> : <Volume2 className="w-3 h-3" />}
                      {speaking ? "Stop" : "Listen"}
                    </button>
                  </div>
                </div>

                {/* Advisory text */}
                <div
                  className="p-3.5 rounded-xl text-[11px] leading-relaxed text-slate-400 italic"
                  style={{ background: "rgba(6,13,24,0.5)", border: "1px solid rgba(255,255,255,0.04)" }}
                >
                  "{latestAdv.advisory_text}"
                </div>

                {/* Footer note */}
                <div className="flex items-center gap-1.5 text-[9px] text-slate-600">
                  <Zap className="w-2.5 h-2.5" />
                  Computed via FAO-56 Penman-Monteith · Soil Water Depletion Index
                </div>
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 py-8">
                <CheckCircle2 className="w-8 h-8 text-emerald-400/30" />
                <div className="text-xs text-slate-500">
                  No active advisory. Click "Run Analysis" to compute FAO-56 deficit.
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
