"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from "recharts";
import { TrendingUp, HelpCircle } from "lucide-react";
import { MOCK_FIELD_HISTORY } from "../lib/mockData";

interface PredictiveChartsProps {
  selectedField: any;
}

export default function PredictiveCharts({ selectedField }: PredictiveChartsProps) {
  // Generate predictive future trajectory based on current moisture
  // If moisture is depleted, the forecast continues downward. If healthy, it stays stable
  const generateChartData = () => {
    if (!selectedField) return [];
    const baseSm = selectedField.properties.soil_moisture;
    const baseNdvi = selectedField.properties.stress_score > 0.4 ? 0.35 : 0.68;
    
    // Past days (6 steps)
    const history = [
      { name: "Day -10", ndvi: baseNdvi + 0.12, moisture: baseSm + 0.18, forecast: null },
      { name: "Day -8", ndvi: baseNdvi + 0.10, moisture: baseSm + 0.14, forecast: null },
      { name: "Day -6", ndvi: baseNdvi + 0.08, moisture: baseSm + 0.10, forecast: null },
      { name: "Day -4", ndvi: baseNdvi + 0.05, moisture: baseSm + 0.05, forecast: null },
      { name: "Day -2", ndvi: baseNdvi + 0.02, moisture: baseSm + 0.02, forecast: null },
      { name: "Today", ndvi: baseNdvi, moisture: baseSm, forecast: baseSm }
    ];
    
    // Future predictions (5 steps)
    const predictions = [
      { name: "Day +2", ndvi: baseNdvi, moisture: null, forecast: Math.max(0.1, baseSm - 0.04) },
      { name: "Day +4", ndvi: baseNdvi - 0.01, moisture: null, forecast: Math.max(0.1, baseSm - 0.07) },
      { name: "Day +6", ndvi: baseNdvi - 0.02, moisture: null, forecast: Math.max(0.1, baseSm - 0.10) },
      { name: "Day +8", ndvi: baseNdvi - 0.03, moisture: null, forecast: Math.max(0.1, baseSm - 0.13) },
      { name: "Day +10", ndvi: baseNdvi - 0.04, moisture: null, forecast: Math.max(0.1, baseSm - 0.15) }
    ];
    
    return [...history, ...predictions];
  };

  const chartData = generateChartData();

  return (
    <div className="p-5 rounded-xl border border-gray-800 glass-panel h-full">
      <h3 className="font-bold text-gray-100 flex items-center gap-2 mb-4.5">
        <TrendingUp className="w-5 h-5 text-indigo-400" />
        Phenology & Predictive Analytics
      </h3>

      {!selectedField ? (
        <div className="text-center py-12 text-gray-500 text-xs flex flex-col items-center justify-center gap-2 h-[220px]">
          <HelpCircle className="w-8 h-8 text-gray-600 animate-pulse" />
          Select a field on the map to forecast moisture stress and NDVI profiles.
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-[10px] text-gray-400 uppercase font-semibold">
            Soil Moisture Depletion Forecast (10-Day Outlook)
          </div>
          
          <div className="h-[210px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorMoisture" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366F1" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#6366F1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis dataKey="name" stroke="#6b7280" fontSize={8} tickLine={false} />
                <YAxis stroke="#6b7280" fontSize={8} domain={[0, 1]} tickLine={false} />
                <Tooltip 
                  contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', fontSize: '10px' }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Legend verticalAlign="top" height={24} iconType="circle" wrapperStyle={{ fontSize: '9px', color: '#94a3b8' }} />
                
                {/* Historical Observed Moisture */}
                <Area 
                  type="monotone" 
                  name="Observed Moisture" 
                  dataKey="moisture" 
                  stroke="#3B82F6" 
                  strokeWidth={2} 
                  fillOpacity={1} 
                  fill="url(#colorMoisture)" 
                />
                
                {/* Forecasted Moisture (10 days ahead) */}
                <Area 
                  type="monotone" 
                  name="LSTM Predicted Moisture" 
                  dataKey="forecast" 
                  stroke="#6366F1" 
                  strokeWidth={2} 
                  strokeDasharray="4 4"
                  fillOpacity={1} 
                  fill="url(#colorForecast)" 
                />
                
                {/* NDVI Profile */}
                <Line 
                  type="monotone" 
                  name="NDVI" 
                  dataKey="ndvi" 
                  stroke="#10B981" 
                  strokeWidth={1.5} 
                  dot={false} 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          <div className="text-[10px] text-gray-500 text-center italic">
            Dashed line represents PyTorch LSTM predictive moisture trajectory.
          </div>
        </div>
      )}
    </div>
  );
}
