"use client";

import React, { useState } from "react";
import { MessageSquare, Send, Sparkles, Key, CloudSun } from "lucide-react";
import { copilotQuery } from "../lib/api";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

interface AICopilotPanelProps {
  onCopilotHighlight: (geojson: any) => void;
  activeLocationInfo: any; // contains lat, lon, address, weather data
}

interface Message {
  sender: "user" | "copilot";
  text: string;
  displayType?: "text" | "table" | "chart" | "map";
  data?: any;
}

export default function AICopilotPanel({ onCopilotHighlight, activeLocationInfo }: AICopilotPanelProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "copilot",
      text: (
        "Hello! I am your AgriSense Geospatial Assistant. Ask me queries like:\n" +
        "• 'Show stressed wheat fields' (triggers map highlighting)\n" +
        "• 'Which villages need irrigation?' (renders priority tables)\n" +
        "• 'Forecast next week's water demand' (visualizes daily requirement charts)\n\n" +
        "💡 Pro tip: Click any point on the map or input a Gemini API Key to ask about any global location!"
      ),
      displayType: "text"
    }
  ]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userText = query;
    setQuery("");
    setLoading(true);

    // Add user message to log
    setMessages(prev => [...prev, { sender: "user", text: userText }]);

    // Read Gemini Key from localStorage
    const geminiKey = typeof window !== 'undefined' ? localStorage.getItem("gemini_api_key") : null;

    if (geminiKey) {
      // ─── Direct Gemini API call with location context ──────────────────
      try {
        const locationContext = activeLocationInfo
          ? `Current Selected Map Location:
- Address: ${activeLocationInfo.address}
- Coordinates: Latitude ${activeLocationInfo.lat.toFixed(5)}, Longitude ${activeLocationInfo.lon.toFixed(5)}
- Weather Info: Temp ${activeLocationInfo.weather?.temp}°C, Wind ${activeLocationInfo.weather?.windSpeed} km/h, Rain Sum ${activeLocationInfo.weather?.rainSum} mm, Reference Evapotranspiration (ET0) ${activeLocationInfo.weather?.et0} mm/day`
          : "No specific map location selected yet. Tell the user they can click anywhere on the map to query specific location parameters.";

        const prompt = `You are the AgriSense GIS Assistant, a satellite crop intelligence platform.
Analyze the following user query with this real-time geospatial context:

${locationContext}

User Query: "${userText}"

Provide a concise, practical agricultural or meteorological analysis. Focus on soil moisture, irrigation suggestions, and crop suitability where appropriate. Be structured and direct. Keep formatting clear and compact for display.`;

        const geminiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${geminiKey}`;
        const response = await fetch(geminiUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            contents: [{ parts: [{ text: prompt }] }]
          })
        });

        if (!response.ok) {
          throw new Error(`Gemini API returned status ${response.status}`);
        }

        const data = await response.json();
        const responseText = data.candidates?.[0]?.content?.parts?.[0]?.text || "No analysis generated. Check your API parameters.";

        setMessages(prev => [
          ...prev,
          {
            sender: "copilot",
            text: responseText,
            displayType: "text"
          }
        ]);
      } catch (err) {
        setMessages(prev => [
          ...prev,
          {
            sender: "copilot",
            text: `Failed to query Gemini API. Verify your API key in the settings panel. Error: ${(err as Error).message}`
          }
        ]);
      } finally {
        setLoading(false);
      }
    } else {
      // ─── Default local mock query parser ──────────────────────────────
      try {
        const res = await copilotQuery(userText);
        
        if (res.intent === "show_stressed_wheat" && res.data) {
          onCopilotHighlight(res.data);
        } else {
          onCopilotHighlight(null);
        }

        setMessages(prev => [
          ...prev,
          {
            sender: "copilot",
            text: res.message,
            displayType: res.display_type,
            data: res.data
          }
        ]);
      } catch (err) {
        setMessages(prev => [
          ...prev,
          {
            sender: "copilot",
            text: "Sorry, I encountered an error searching that geospatial index."
          }
        ]);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="flex flex-col h-[480px] rounded-xl border border-gray-800 glass-panel overflow-hidden">
      {/* Copilot Header */}
      <div className="p-4 border-b border-gray-800 bg-slate-900 bg-opacity-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-450" />
          <h3 className="font-bold text-gray-100 text-sm">AgriSense GIS Copilot</h3>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-gray-400">
          {activeLocationInfo && (
            <span className="flex items-center gap-1 text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-900">
              <CloudSun className="w-3.5 h-3.5" /> Context Synced
            </span>
          )}
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" /> Active
          </span>
        </div>
      </div>

      {/* Messages area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3.5">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex flex-col max-w-[85%] ${
              msg.sender === "user" ? "ml-auto items-end" : "mr-auto items-start"
            }`}
          >
            <div
              className={`p-3 rounded-lg text-xs leading-relaxed ${
                msg.sender === "user"
                  ? "bg-indigo-650 text-white rounded-br-none"
                  : "bg-slate-900 border border-gray-850 text-gray-300 rounded-bl-none whitespace-pre-line"
              }`}
            >
              {msg.text}
            </div>

            {/* Custom display renderings based on Copilot outputs */}
            {msg.sender === "copilot" && msg.displayType === "table" && msg.data && (
              <div className="w-full mt-2 bg-slate-950 border border-gray-850 rounded p-2 overflow-x-auto text-[10px]">
                <table className="min-w-full text-left divide-y divide-gray-800">
                  <thead>
                    <tr className="text-gray-400">
                      <th className="pb-1 pr-2">Village</th>
                      <th className="pb-1 pr-2">Total Plots</th>
                      <th className="pb-1 pr-2">Stressed</th>
                      <th className="pb-1">Priority</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-900 text-gray-300">
                    {msg.data.map((item: any, key: number) => (
                      <tr key={key}>
                        <td className="py-1 pr-2 font-medium">{item.village}</td>
                        <td className="py-1 pr-2 text-center">{item.total_fields}</td>
                        <td className="py-1 pr-2 text-center text-amber-400">{item.stressed_fields}</td>
                        <td className="py-1 font-bold text-rose-450">{item.advisory_priority}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {msg.sender === "copilot" && msg.displayType === "chart" && msg.data && (
              <div className="w-full mt-2 bg-slate-950 border border-gray-850 rounded p-2.5 h-[140px]">
                <div className="text-[10px] text-gray-400 font-bold mb-1">Weekly Water Demand Forecast</div>
                <ResponsiveContainer width="100%" height="85%">
                  <BarChart data={msg.data.daily_distribution}>
                    <XAxis dataKey="day" stroke="#6b7280" fontSize={8} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '4px', fontSize: '9px' }}
                      labelStyle={{ color: '#94a3b8' }}
                    />
                    <Bar dataKey="demand_m3" fill="#4f46e5" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-gray-500 text-xs mt-1">
            <Sparkles className="w-3.5 h-3.5 animate-spin text-indigo-400" />
            Generating AI analysis...
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 border-t border-gray-800 bg-slate-900 bg-opacity-20 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={activeLocationInfo ? "Ask AI about this location..." : "Ask Copilot, e.g. 'Show stressed wheat fields'"}
          className="flex-1 bg-slate-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-slate-650 transition"
        />
        <button
          type="submit"
          className="bg-indigo-600 hover:bg-indigo-700 text-white p-2 rounded-lg transition"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
