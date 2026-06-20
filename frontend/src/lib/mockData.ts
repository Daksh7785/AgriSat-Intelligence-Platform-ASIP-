// High fidelity geospatial mock data matching db schema

export const MOCK_FIELDS_GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: 1,
      geometry: {
        type: "Polygon",
        coordinates: [[[75.02, 30.02], [75.05, 30.02], [75.05, 30.05], [75.02, 30.05], [75.02, 30.02]]]
      },
      properties: {
        name: "Harpreet Farm A",
        village: "Bathinda East",
        district: "Bathinda",
        soil_type: "alluvial",
        crop_type: "wheat",
        stress_level: "Severe Stress",
        stress_score: 0.72,
        soil_moisture: 0.22
      }
    },
    {
      type: "Feature",
      id: 2,
      geometry: {
        type: "Polygon",
        coordinates: [[[75.06, 30.02], [75.09, 30.02], [75.09, 30.05], [75.06, 30.05], [75.06, 30.02]]]
      },
      properties: {
        name: "Rajinder Farm B",
        village: "Bathinda East",
        district: "Bathinda",
        soil_type: "alluvial",
        crop_type: "rice",
        stress_level: "No Stress",
        stress_score: 0.08,
        soil_moisture: 0.65
      }
    },
    {
      type: "Feature",
      id: 3,
      geometry: {
        type: "Polygon",
        coordinates: [[[75.11, 30.03], [75.14, 30.03], [75.14, 30.06], [75.11, 30.06], [75.11, 30.03]]]
      },
      properties: {
        name: "Gurcharan Plot",
        village: "Maur Kalan",
        district: "Bathinda",
        soil_type: "black",
        crop_type: "cotton",
        stress_level: "No Stress",
        stress_score: 0.12,
        soil_moisture: 0.58
      }
    },
    {
      type: "Feature",
      id: 4,
      geometry: {
        type: "Polygon",
        coordinates: [[[75.15, 30.04], [75.19, 30.04], [75.19, 30.08], [75.15, 30.08], [75.15, 30.04]]]
      },
      properties: {
        name: "Sandhu Field",
        village: "Maur Kalan",
        district: "Bathinda",
        soil_type: "alluvial",
        crop_type: "cotton",
        stress_level: "Moderate Stress",
        stress_score: 0.51,
        soil_moisture: 0.31
      }
    },
    {
      type: "Feature",
      id: 5,
      geometry: {
        type: "Polygon",
        coordinates: [[[75.02, 30.12], [75.05, 30.12], [75.05, 30.16], [75.02, 30.16], [75.02, 30.12]]]
      },
      properties: {
        name: "Punjab Agri Research Unit",
        village: "Faridkot South",
        district: "Faridkot",
        soil_type: "clay",
        crop_type: "fallow",
        stress_level: "No Stress",
        stress_score: 0.05,
        soil_moisture: 0.45
      }
    },
    {
      type: "Feature",
      id: 6,
      geometry: {
        type: "Polygon",
        coordinates: [[[75.06, 30.12], [75.09, 30.12], [75.09, 30.16], [75.06, 30.16], [75.06, 30.12]]]
      },
      properties: {
        name: "Majha Cooperative Farm",
        village: "Faridkot South",
        district: "Faridkot",
        soil_type: "alluvial",
        crop_type: "wheat",
        stress_level: "No Stress",
        stress_score: 0.10,
        soil_moisture: 0.62
      }
    },
    {
      type: "Feature",
      id: 7,
      geometry: {
        type: "Polygon",
        coordinates: [[[75.12, 30.11], [75.16, 30.11], [75.16, 30.15], [75.12, 30.15], [75.12, 30.11]]]
      },
      properties: {
        name: "Doaba Organic Field",
        village: "Kotkapura North",
        district: "Faridkot",
        soil_type: "black",
        crop_type: "rice",
        stress_level: "No Stress",
        stress_score: 0.09,
        soil_moisture: 0.70
      }
    }
  ]
};

export const MOCK_COMMAND_AREAS_GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: 1,
      geometry: {
        type: "MultiPolygon",
        coordinates: [[[[75.00, 30.00], [75.20, 30.00], [75.20, 30.20], [75.00, 30.20], [75.00, 30.00]]]]
      },
      properties: {
        name: "Sirhind-Bhakra Command Zone",
        capacity_cusec: 1500,
        current_flow_cusec: 1250,
        utilization_pct: 83.3
      }
    }
  ]
};

export const MOCK_CANALS_GEOJSON = {
  type: "FeatureCollection",
  features: [
    {
      type: "Feature",
      id: 1,
      geometry: {
        type: "LineString",
        coordinates: [[75.00, 30.10], [75.10, 30.10], [75.20, 30.15]]
      },
      properties: {
        name: "Sirhind Feeder Canal",
        flow_rate_cusec: 800,
        status: "operational"
      }
    },
    {
      type: "Feature",
      id: 2,
      geometry: {
        type: "LineString",
        coordinates: [[75.10, 30.10], [75.12, 30.02], [75.18, 30.01]]
      },
      properties: {
        name: "Bhakra Distributary Branch",
        flow_rate_cusec: 450,
        status: "operational"
      }
    }
  ]
};

export const MOCK_SUMMARY = {
  total_fields: 7,
  average_stress_score: 0.24,
  total_water_saved_m3: 3840.0,
  active_command_canal_flow_cusec: 1250.0,
  crop_distribution: {
    wheat: 2,
    rice: 2,
    cotton: 2,
    sugarcane: 0,
    fallow: 1
  }
};

export const MOCK_REPORTS = [
  {
    village: "Bathinda East",
    district: "Bathinda",
    total_fields: 2,
    stressed_fields: 1,
    pct_stressed: 50.0,
    average_stress_score: 0.40,
    critical_stress_fields: 1,
    advisory_priority: "High"
  },
  {
    village: "Maur Kalan",
    district: "Bathinda",
    total_fields: 2,
    stressed_fields: 1,
    pct_stressed: 50.0,
    average_stress_score: 0.31,
    critical_stress_fields: 0,
    advisory_priority: "Medium"
  },
  {
    village: "Faridkot South",
    district: "Faridkot",
    total_fields: 2,
    stressed_fields: 0,
    pct_stressed: 0.0,
    average_stress_score: 0.07,
    critical_stress_fields: 0,
    advisory_priority: "Low"
  },
  {
    village: "Kotkapura North",
    district: "Faridkot",
    total_fields: 1,
    stressed_fields: 0,
    pct_stressed: 0.0,
    average_stress_score: 0.09,
    critical_stress_fields: 0,
    advisory_priority: "Low"
  }
];

export const MOCK_ALERTS = [
  {
    id: 101,
    field_id: 1,
    trigger_type: "moisture_stress",
    severity: "critical",
    message: "Alert: Field 'Harpreet Farm A' in village 'Bathinda East' is experiencing 'Severe Stress' (Score: 0.72). Immediate irrigation is recommended.",
    sent_at: "2026-06-20T21:40:00Z",
    status: "unread"
  },
  {
    id: 102,
    field_id: 4,
    trigger_type: "water_deficit",
    severity: "warning",
    message: "Alert: Water deficit on field 'Sandhu Field' has reached 4.5 mm/day. Net crop requirement is 5.0 mm.",
    sent_at: "2026-06-20T21:45:00Z",
    status: "unread"
  }
];

export const MOCK_ADVISORIES = [
  {
    id: 201,
    field_id: 1,
    recommended_action: "Immediate irrigation",
    recommended_depth_mm: 55.0,
    recommended_volume_m3: 825.0,
    water_savings_m3: 300.0,
    advisory_text: "Critical moisture depletion detected in wheat crop during the flowering stage. Apply 55.0 mm of water immediately to avoid yield loss. Expected net water demand is 6.2 mm/day. No significant rainfall is forecast.",
    timestamp: "2026-06-20T21:50:00Z"
  },
  {
    id: 202,
    field_id: 4,
    recommended_action: "Irrigate in 2 days",
    recommended_depth_mm: 40.0,
    recommended_volume_m3: 600.0,
    water_savings_m3: 525.0,
    advisory_text: "Moderate soil moisture depletion in cotton (vegetative stage). Schedule irrigation of 40.0 mm within the next 48 hours. Forecast rainfall is low (2.0 mm).",
    timestamp: "2026-06-20T21:55:00Z"
  }
];

export const MOCK_FORECAST = {
  total_forecast_m3: 8520.0,
  daily_distribution: [
    { day: "Mon", demand_m3: 1050.0 },
    { day: "Tue", demand_m3: 1220.0 },
    { day: "Wed", demand_m3: 1180.0 },
    { day: "Thu", demand_m3: 1390.0 },
    { day: "Fri", demand_m3: 1280.0 },
    { day: "Sat", demand_m3: 1200.0 },
    { day: "Sun", demand_m3: 1200.0 }
  ]
};

export const MOCK_FIELD_HISTORY = [
  { date: "Day -10", ndvi: 0.70, soil_moisture: 0.60, deficit: 0.8 },
  { date: "Day -8", ndvi: 0.68, soil_moisture: 0.55, deficit: 1.2 },
  { date: "Day -6", ndvi: 0.64, soil_moisture: 0.48, deficit: 2.1 },
  { date: "Day -4", ndvi: 0.58, soil_moisture: 0.40, deficit: 3.8 },
  { date: "Day -2", ndvi: 0.45, soil_moisture: 0.30, deficit: 5.0 },
  { date: "Latest", ndvi: 0.35, soil_moisture: 0.22, deficit: 6.2 }
];
