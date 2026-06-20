"use client";

import React, { useState } from "react";
import { MessageSquare, Send, Sparkles, AlertTriangle } from "lucide-react";
import { copilotQuery } from "../lib/api";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

interface AICopilotPanelProps {
  onCopilotHighlight: (geojson: any) => void;
}

interface Message {
  sender: "user" | "copilot";
  text: string;
  displayType?: "text" | "table" | "chart" | "map";
  data?: any;
}

export default function AICopilotPanel({ onCopilotHighlight }: AICopilotPanelProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "copilot",
      text: (
        "Hello! I am your AgriSense Geospatial Assistant. Ask me queries like:\n" +
        "• 'Show stressed wheat fields' (triggers map highlighting)\n" +
        "• 'Which villages need irrigation?' (renders priority tables)\n" +
        "• 'Forecast next week's water demand' (visualizes daily requirement charts)"
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

    try {
      const res = await copilotQuery(userText);
      
      // If intent is showing map layers, send highlight to parent map
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
  };

  return (
    <div className="flex flex-col h-[480px] rounded-xl border border-gray-800 glass-panel overflow-hidden">
      {/* Copilot Header */}
      <div className="p-4 border-b border-gray-800 bg-slate-900 bg-opacity-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-400" />
          <h3 className="font-bold text-gray-100 text-sm">AgriSense GIS Copilot</h3>
        </div>
        <span className="text-[10px] text-gray-400 flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" /> Online
        </span>
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
                  ? "bg-blue-600 text-white rounded-br-none"
                  : "bg-slate-900 border border-gray-800 text-gray-300 rounded-bl-none whitespace-pre-line"
              }`}
            >
              {msg.text}
            </div>

            {/* Custom display renderings based on Copilot outputs */}
            {msg.sender === "copilot" && msg.displayType === "table" && msg.data && (
              <div className="w-full mt-2 bg-slate-950 border border-gray-800 rounded p-2 overflow-x-auto text-[10px]">
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
                        <td className="py-1 font-bold text-rose-400">{item.advisory_priority}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {msg.sender === "copilot" && msg.displayType === "chart" && msg.data && (
              <div className="w-full mt-2 bg-slate-950 border border-gray-800 rounded p-2.5 h-[140px]">
                <div className="text-[10px] text-gray-400 font-bold mb-1">Weekly Water Demand Forecast</div>
                <ResponsiveContainer width="100%" height="85%">
                  <BarChart data={msg.data.daily_distribution}>
                    <XAxis dataKey="day" stroke="#6b7280" fontSize={8} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '4px', fontSize: '9px' }}
                      labelStyle={{ color: '#94a3b8' }}
                    />
                    <Bar dataKey="demand_m3" fill="#3b82f6" radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-2 text-gray-500 text-xs mt-1">
            <Sparkles className="w-3.5 h-3.5 animate-spin text-amber-400" />
            Analyzing spatial boundaries...
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 border-t border-gray-800 bg-slate-900 bg-opacity-20 flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask Copilot, e.g. 'Show stressed wheat fields'"
          className="flex-1 bg-slate-950 border border-gray-800 rounded-lg px-3 py-2 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-slate-600 transition"
        />
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-lg transition"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}
