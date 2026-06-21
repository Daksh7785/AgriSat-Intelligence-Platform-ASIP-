"use client";

import React, { useState } from "react";
import { MessageSquare, Send, Sparkles, CloudSun, Bot, User, Loader2 } from "lucide-react";
import { copilotQuery } from "../lib/api";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

interface AICopilotPanelProps {
  onCopilotHighlight: (geojson: any) => void;
  activeLocationInfo: any;
}

interface Message {
  sender: "user" | "copilot";
  text: string;
  displayType?: "text" | "table" | "chart" | "map";
  data?: any;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: "rgba(6,13,24,0.97)",
        border: "1px solid rgba(99,102,241,0.3)",
        borderRadius: "8px",
        padding: "8px 12px",
        fontSize: "11px",
        color: "#94A3B8",
      }}>
        <div className="font-bold text-indigo-300 mb-0.5">{label}</div>
        <div>Demand: <b className="text-white">{payload[0].value} m³</b></div>
      </div>
    );
  }
  return null;
};

export default function AICopilotPanel({ onCopilotHighlight, activeLocationInfo }: AICopilotPanelProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "copilot",
      text:
        "Hello! I'm your AgriSense GIS Copilot. Ask me queries like:\n" +
        "• \"Show stressed wheat fields\" → map highlights\n" +
        "• \"Which villages need irrigation?\" → priority tables\n" +
        "• \"Forecast next week water demand\" → charts\n\n" +
        "💡 Click any map point or enter your Gemini API key for AI-powered global location analysis!",
      displayType: "text",
    },
  ]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    const userText = query;
    setQuery("");
    setLoading(true);
    setMessages((prev) => [...prev, { sender: "user", text: userText }]);

    const geminiKey =
      typeof window !== "undefined" ? localStorage.getItem("gemini_api_key") : null;

    if (geminiKey) {
      try {
        const locationCtx = activeLocationInfo
          ? `Selected Map Location:
- Address: ${activeLocationInfo.address}
- Coords: ${activeLocationInfo.lat.toFixed(5)}°N, ${activeLocationInfo.lon.toFixed(5)}°E
- Weather: Temp ${activeLocationInfo.weather?.temp}°C, Wind ${activeLocationInfo.weather?.windSpeed} km/h, Rain ${activeLocationInfo.weather?.rainSum} mm, ET₀ ${activeLocationInfo.weather?.et0} mm/day`
          : "No map location selected. Tell user to click the map or search a location.";

        const prompt = `You are AgriSense GIS Assistant — a satellite crop intelligence platform powered by FAO-56 science.
Analyze this query using the real-time geospatial context:

${locationCtx}

User Query: "${userText}"

Provide a concise, structured agricultural or meteorological analysis. Focus on: soil moisture, irrigation scheduling, crop suitability, FAO-56 water deficits. Format clearly for inline display. Be direct and practical.`;

        const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`;
        const response = await fetch(geminiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
        });
        if (!response.ok) throw new Error(`Gemini returned ${response.status}`);
        const data = await response.json();
        const responseText =
          data.candidates?.[0]?.content?.parts?.[0]?.text ??
          "No analysis generated. Please check your API key.";
        setMessages((prev) => [...prev, { sender: "copilot", text: responseText, displayType: "text" }]);
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          { sender: "copilot", text: `Failed to query Gemini API. Error: ${(err as Error).message}` },
        ]);
      } finally {
        setLoading(false);
      }
    } else {
      try {
        const res = await copilotQuery(userText);
        if (res.intent === "show_stressed_wheat" && res.data) {
          onCopilotHighlight(res.data);
        } else {
          onCopilotHighlight(null);
        }
        setMessages((prev) => [
          ...prev,
          { sender: "copilot", text: res.message, displayType: res.display_type, data: res.data },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          { sender: "copilot", text: "Error searching the geospatial index. Please try again." },
        ]);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div
      className="flex flex-col rounded-2xl overflow-hidden"
      style={{
        height: "480px",
        background: "linear-gradient(135deg, rgba(15,32,64,0.9) 0%, rgba(10,22,40,0.85) 100%)",
        border: "1px solid rgba(255,255,255,0.07)",
        boxShadow: "0 4px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05)",
      }}
    >
      {/* Header */}
      <div
        className="px-4 py-3 flex items-center justify-between flex-shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(6,13,24,0.4)" }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #4F46E5, #7C3AED)", boxShadow: "0 0 12px rgba(99,102,241,0.4)" }}
          >
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="text-sm font-bold text-white leading-none">AI GIS Copilot</div>
            <div className="text-[9px] text-slate-500 mt-0.5 font-medium">AgriSense Intelligence</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {activeLocationInfo && (
            <span
              className="flex items-center gap-1.5 text-[9px] font-bold text-emerald-400 px-2 py-1 rounded-lg"
              style={{ background: "rgba(16,185,129,0.1)", border: "1px solid rgba(16,185,129,0.2)" }}
            >
              <CloudSun className="w-3 h-3" />
              Ctx Loaded
            </span>
          )}
          <span
            className="flex items-center gap-1.5 text-[9px] font-bold text-indigo-400 px-2 py-1 rounded-lg"
            style={{ background: "rgba(99,102,241,0.1)", border: "1px solid rgba(99,102,241,0.2)" }}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
            Active
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-2.5 animate-fade-in ${msg.sender === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            {/* Avatar */}
            <div
              className="w-7 h-7 rounded-xl flex-shrink-0 flex items-center justify-center mt-0.5"
              style={
                msg.sender === "user"
                  ? { background: "rgba(99,102,241,0.2)", border: "1px solid rgba(99,102,241,0.3)" }
                  : { background: "rgba(124,58,237,0.2)", border: "1px solid rgba(124,58,237,0.3)" }
              }
            >
              {msg.sender === "user" ? (
                <User className="w-3.5 h-3.5 text-indigo-400" />
              ) : (
                <Bot className="w-3.5 h-3.5 text-violet-400" />
              )}
            </div>

            <div className={`flex flex-col max-w-[82%] ${msg.sender === "user" ? "items-end" : "items-start"}`}>
              <div
                className="px-3.5 py-2.5 rounded-2xl text-[11px] leading-relaxed"
                style={
                  msg.sender === "user"
                    ? {
                        background: "linear-gradient(135deg, #4F46E5, #6366F1)",
                        color: "white",
                        borderBottomRightRadius: "4px",
                        boxShadow: "0 2px 8px rgba(99,102,241,0.3)",
                      }
                    : {
                        background: "rgba(15,32,64,0.8)",
                        border: "1px solid rgba(255,255,255,0.06)",
                        color: "#CBD5E1",
                        borderBottomLeftRadius: "4px",
                        whiteSpace: "pre-line",
                      }
                }
              >
                {msg.text}
              </div>

              {/* Table rendering */}
              {msg.sender === "copilot" && msg.displayType === "table" && msg.data && (
                <div
                  className="w-full mt-2 rounded-xl overflow-hidden text-[10px]"
                  style={{ background: "rgba(6,13,24,0.8)", border: "1px solid rgba(255,255,255,0.06)" }}
                >
                  <table className="min-w-full">
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
                        {["Village", "Plots", "Stressed", "Priority"].map((h) => (
                          <th key={h} className="px-3 py-2 text-left text-[9px] font-bold uppercase tracking-widest text-slate-500">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {msg.data.map((item: any, key: number) => (
                        <tr key={key} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                          <td className="px-3 py-2 font-semibold text-slate-200">{item.village}</td>
                          <td className="px-3 py-2 text-center text-slate-400">{item.total_fields}</td>
                          <td className="px-3 py-2 text-center text-amber-400 font-bold">{item.stressed_fields}</td>
                          <td className="px-3 py-2">
                            <span className={`chip font-bold text-[9px] ${
                              item.advisory_priority === "High"
                                ? "bg-rose-900/40 text-rose-300 border border-rose-700/40"
                                : "bg-amber-900/40 text-amber-300 border border-amber-700/40"
                            }`}>{item.advisory_priority}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Chart rendering */}
              {msg.sender === "copilot" && msg.displayType === "chart" && msg.data && (
                <div
                  className="w-full mt-2 rounded-xl p-3"
                  style={{ background: "rgba(6,13,24,0.8)", border: "1px solid rgba(255,255,255,0.06)", height: "140px" }}
                >
                  <div className="text-[9px] text-slate-400 font-bold uppercase tracking-widest mb-2">
                    Water Demand Forecast
                  </div>
                  <ResponsiveContainer width="100%" height="80%">
                    <BarChart data={msg.data.daily_distribution} margin={{ top: 0, right: 4, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis dataKey="day" stroke="#475569" fontSize={8} tickLine={false} axisLine={false} />
                      <YAxis stroke="#475569" fontSize={8} tickLine={false} axisLine={false} />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="demand_m3" fill="url(#copilotBar)" radius={[3, 3, 0, 0]} />
                      <defs>
                        <linearGradient id="copilotBar" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#818CF8" />
                          <stop offset="100%" stopColor="#4F46E5" stopOpacity={0.8} />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-[11px] text-slate-400 px-1">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
            <span>Generating analysis...</span>
            <span className="flex gap-0.5 ml-1">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1 h-1 rounded-full bg-indigo-400"
                  style={{ animation: `pulse-dot 1.2s ease-in-out ${i * 0.2}s infinite` }}
                />
              ))}
            </span>
          </div>
        )}
      </div>

      {/* Input */}
      <form
        onSubmit={handleSend}
        className="flex gap-2.5 p-3 flex-shrink-0"
        style={{ borderTop: "1px solid rgba(255,255,255,0.06)", background: "rgba(6,13,24,0.3)" }}
      >
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={
            activeLocationInfo
              ? `Ask about ${activeLocationInfo.address?.split(",")[0] ?? "this location"}...`
              : "Ask Copilot, e.g. 'Show stressed wheat fields'..."
          }
          className="flex-1 input-dark px-3.5 py-2 text-[11px]"
        />
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="btn-primary px-3.5 py-2 flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
}
