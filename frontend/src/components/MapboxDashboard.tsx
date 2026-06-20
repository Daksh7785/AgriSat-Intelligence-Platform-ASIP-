"use client";

import { useEffect, useState, useRef } from "react";
import { MapContainer, TileLayer, Polygon, Polyline, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Helper component to auto-focus map on fields
function MapController({ bounds }: { bounds: L.LatLngBounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [20, 20] });
    }
  }, [bounds, map]);
  return null;
}

interface MapboxDashboardProps {
  fieldsGeojson: any;
  canalsGeojson: any;
  commandGeojson: any;
  activeLayer: "crops" | "stress" | "moisture";
  timeStep: number; // 0 to 5 represent temporal indices
  selectedFieldId: number | null;
  onSelectField: (id: number) => void;
  onTriggerClassification: (id: number) => void;
  onTriggerAdvisory: (id: number) => void;
  copilotHighlightGeojson: any;
}

export default function MapboxDashboard({
  fieldsGeojson,
  canalsGeojson,
  commandGeojson,
  activeLayer,
  timeStep,
  selectedFieldId,
  onSelectField,
  onTriggerClassification,
  onTriggerAdvisory,
  copilotHighlightGeojson
}: MapboxDashboardProps) {
  const [mounted, setMounted] = useState(false);
  const [mapBounds, setMapBounds] = useState<L.LatLngBounds | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Compute map bounds once fields load
  useEffect(() => {
    if (fieldsGeojson?.features?.length > 0) {
      const coords: L.LatLngTuple[] = [];
      fieldsGeojson.features.forEach((feat: any) => {
        if (feat.geometry.type === "Polygon") {
          feat.geometry.coordinates[0].forEach((pt: any) => {
            coords.push([pt[1], pt[0]]);
          });
        }
      });
      if (coords.length > 0) {
        setMapBounds(L.latLngBounds(coords));
      }
    }
  }, [fieldsGeojson]);

  if (!mounted) {
    return (
      <div className="h-[450px] w-full flex items-center justify-center bg-gray-900 border border-gray-800 rounded-lg">
        <div className="text-gray-400 animate-pulse">Initializing Geospatial Engine...</div>
      </div>
    );
  }

  // Styling helper for fields based on active layers and temporal changes
  const getFieldStyle = (feature: any) => {
    const isSelected = feature.id === selectedFieldId;
    const isCopilotHighlighted = copilotHighlightGeojson?.features?.some((f: any) => f.id === feature.id);
    
    let fillColor = "#10B981"; // Default green
    let fillOpacity = 0.5;
    
    // Simulate temporal variations: Day -10 to Latest
    // Earlier steps have lower vegetation and less stress. Latest steps show full signatures
    const baseStressScore = feature.properties.stress_score;
    const temporalStressScore = Math.min(1.0, Math.max(0.0, baseStressScore * (timeStep / 5)));
    
    if (activeLayer === "crops") {
      const crop = feature.properties.crop_type;
      if (crop === "wheat") fillColor = "#FBBF24"; // Amber
      else if (crop === "rice") fillColor = "#10B981"; // Emerald
      else if (crop === "cotton") fillColor = "#22D3EE"; // Cyan
      else if (crop === "sugarcane") fillColor = "#A7F3D0"; // Soft emerald
      else fillColor = "#78716C"; // Gray/Fallow
    } else if (activeLayer === "stress") {
      // High stress score maps to red, low to green
      if (temporalStressScore > 0.6) fillColor = "#EF4444"; // Red
      else if (temporalStressScore > 0.4) fillColor = "#F59E0B"; // Orange
      else if (temporalStressScore > 0.2) fillColor = "#FBBF24"; // Yellow
      else fillColor = "#10B981"; // Green
      fillOpacity = 0.25 + temporalStressScore * 0.45;
    } else { // Soil Moisture Layer
      const baseSm = feature.properties.soil_moisture;
      // Over time, soil moisture depletes if stress goes up
      const temporalSm = Math.max(0.1, baseSm - (temporalStressScore * 0.3));
      fillColor = "#3B82F6"; // Blue
      fillOpacity = temporalSm * 0.8;
    }

    return {
      fillColor: fillColor,
      fillOpacity: fillOpacity,
      color: isSelected ? "#3B82F6" : (isCopilotHighlighted ? "#F59E0B" : "rgba(255,255,255,0.2)"),
      weight: isSelected ? 4 : (isCopilotHighlighted ? 3 : 1),
      dashArray: isCopilotHighlighted ? "4" : undefined
    };
  };

  return (
    <div className="relative w-full h-[480px] rounded-xl overflow-hidden border border-gray-800 glass-panel">
      {/* Map Control overlay for layer info */}
      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-1 text-xs bg-slate-900 bg-opacity-90 border border-slate-700 p-2.5 rounded-lg max-w-[200px] text-gray-200">
        <div className="font-semibold border-b border-gray-700 pb-1 mb-1">Active Visual Layer</div>
        <div className="flex items-center gap-1.5 capitalize">
          <span
            className="w-2.5 h-2.5 rounded-full"
            style={{
              backgroundColor:
                activeLayer === "crops" ? "#FBBF24" : activeLayer === "stress" ? "#EF4444" : "#3B82F6"
            }}
          />
          {activeLayer} Viewer
        </div>
        <div className="text-[10px] text-gray-400 mt-1">
          {activeLayer === "crops" && "Golden = Wheat | Emerald = Rice | Cyan = Cotton | Gray = Fallow"}
          {activeLayer === "stress" && "Red = Critical | Orange = Severe | Yellow = Moderate | Green = Safe"}
          {activeLayer === "moisture" && "Opacity indicates soil water content (FAO-56)"}
        </div>
      </div>

      <MapContainer
        center={[30.08, 75.10]}
        zoom={11}
        scrollWheelZoom={false}
        className="w-full h-full"
        style={{ background: "#0D1322" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* 1. Command Area Boundary */}
        {commandGeojson?.features?.map((feat: any, idx: number) => {
          if (feat.geometry.type === "MultiPolygon") {
            const positions = feat.geometry.coordinates[0][0].map((coord: any) => [coord[1], coord[0]]);
            return (
              <Polygon
                key={`command-${idx}`}
                positions={positions}
                pathOptions={{
                  fillColor: "#1E3A8A",
                  fillOpacity: 0.08,
                  color: "#3B82F6",
                  weight: 1.5,
                  dashArray: "5, 5"
                }}
              />
            );
          }
          return null;
        })}

        {/* 2. Canals network */}
        {canalsGeojson?.features?.map((feat: any, idx: number) => {
          if (feat.geometry.type === "LineString") {
            const positions = feat.geometry.coordinates.map((coord: any) => [coord[1], coord[0]]);
            return (
              <Polyline
                key={`canal-${idx}`}
                positions={positions}
                pathOptions={{
                  color: "#0284C7",
                  weight: 3.5,
                  opacity: 0.8
                }}
              >
                <Popup>
                  <div className="text-xs p-1 text-gray-200">
                    <div className="font-bold text-sky-400">{feat.properties.name}</div>
                    <div>Flow Rate: {feat.properties.flow_rate_cusec} Cusec</div>
                    <div>Status: {feat.properties.status}</div>
                  </div>
                </Popup>
              </Polyline>
            );
          }
          return null;
        })}

        {/* 3. Farm Fields */}
        {fieldsGeojson?.features?.map((feat: any) => {
          if (feat.geometry.type === "Polygon") {
            const positions = feat.geometry.coordinates[0].map((coord: any) => [coord[1], coord[0]]);
            
            return (
              <Polygon
                key={`field-${feat.id}`}
                positions={positions}
                pathOptions={getFieldStyle(feat)}
                eventHandlers={{
                  click: () => onSelectField(feat.id)
                }}
              >
                <Popup>
                  <div className="text-xs font-sans text-gray-200 p-2 min-w-[200px]">
                    <div className="font-bold text-emerald-400 text-sm border-b border-gray-700 pb-1 mb-1.5">
                      {feat.properties.name}
                    </div>
                    <div className="grid grid-cols-2 gap-y-1 gap-x-2 text-[11px] mb-2.5 text-gray-300">
                      <div>Village:</div>
                      <div className="font-semibold text-right">{feat.properties.village}</div>
                      
                      <div>Crop Type:</div>
                      <span className="font-semibold text-right capitalize text-amber-300">
                        {feat.properties.crop_type}
                      </span>
                      
                      <div>Stress Level:</div>
                      <span className={`font-semibold text-right ${feat.properties.stress_score > 0.4 ? 'text-rose-400' : 'text-emerald-400'}`}>
                        {feat.properties.stress_level}
                      </span>
                      
                      <div>Soil Moisture:</div>
                      <div className="font-semibold text-right">{Math.round(feat.properties.soil_moisture * 100)}%</div>
                    </div>
                    
                    <div className="flex gap-2.5 mt-2 border-t border-gray-700 pt-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onTriggerClassification(feat.id);
                        }}
                        className="flex-1 bg-amber-600 hover:bg-amber-700 text-white font-medium text-[10px] py-1 px-1.5 rounded text-center transition"
                      >
                        AutoML Classify
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onTriggerAdvisory(feat.id);
                        }}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium text-[10px] py-1 px-1.5 rounded text-center transition"
                      >
                        Advisory AI
                      </button>
                    </div>
                  </div>
                </Popup>
              </Polygon>
            );
          }
          return null;
        })}

        {/* Set default map views */}
        {mapBounds && <MapController bounds={mapBounds} />}
      </MapContainer>
    </div>
  );
}
