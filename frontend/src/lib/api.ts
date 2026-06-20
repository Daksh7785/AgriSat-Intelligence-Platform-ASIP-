import * as mock from "./mockData";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// In mock mode, we simulate server lag
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

async function fetchJson(endpoint: string, options: RequestInit = {}): Promise<any> {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });
    if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`Fetch to ${url} failed. Falling back to local data. Error: ${err}`);
    throw err;
  }
}

export async function getSummary() {
  try {
    return await fetchJson("/dashboard/summary");
  } catch (e) {
    return mock.MOCK_SUMMARY;
  }
}

export async function getFieldsGeoJSON() {
  try {
    return await fetchJson("/dashboard/fields/geojson");
  } catch (e) {
    return mock.MOCK_FIELDS_GEOJSON;
  }
}

export async function getCommandAreasGeoJSON() {
  try {
    return await fetchJson("/dashboard/command-areas/geojson");
  } catch (e) {
    return mock.MOCK_COMMAND_AREAS_GEOJSON;
  }
}

export async function getCanalsGeoJSON() {
  try {
    return await fetchJson("/dashboard/canals/geojson");
  } catch (e) {
    return mock.MOCK_CANALS_GEOJSON;
  }
}

export async function getVillageReports() {
  try {
    return await fetchJson("/stress/reports");
  } catch (e) {
    return mock.MOCK_REPORTS;
  }
}

export async function getAlerts() {
  try {
    return await fetchJson("/alerts/list");
  } catch (e) {
    return mock.MOCK_ALERTS;
  }
}

export async function markAlertRead(alertId: number) {
  try {
    return await fetchJson(`/alerts/read/${alertId}`, { method: "POST" });
  } catch (e) {
    return { status: "success" };
  }
}

export async function getAdvisories(fieldId: number) {
  try {
    return await fetchJson(`/advisory/list/${fieldId}`);
  } catch (e) {
    // Return mock advisory for field id
    return mock.MOCK_ADVISORIES.filter(a => a.field_id === fieldId);
  }
}

export async function triggerClassification(fieldId: number) {
  try {
    return await fetchJson("/classification/predict", {
      method: "POST",
      body: JSON.stringify({ field_id: fieldId })
    });
  } catch (e) {
    await delay(600);
    const field = mock.MOCK_FIELDS_GEOJSON.features.find(f => f.id === fieldId);
    return {
      field_id: fieldId,
      crop_type: field?.properties.crop_type || "wheat",
      probability: 0.94,
      uncertainty: 0.03,
      classification_date: new Date().toISOString().split('T')[0]
    };
  }
}

export async function triggerAdvisory(fieldId: number) {
  try {
    return await fetchJson("/advisory/generate", {
      method: "POST",
      body: JSON.stringify({ field_id: fieldId })
    });
  } catch (e) {
    await delay(500);
    const advice = mock.MOCK_ADVISORIES.find(a => a.field_id === fieldId);
    return advice || {
      id: Math.floor(Math.random() * 1000),
      field_id: fieldId,
      recommended_action: "No irrigation required",
      recommended_depth_mm: 0.0,
      recommended_volume_m3: 0.0,
      water_savings_m3: 0.0,
      advisory_text: "Soil moisture is optimal. No action needed.",
      timestamp: new Date().toISOString()
    };
  }
}

export async function copilotQuery(message: string) {
  try {
    return await fetchJson("/copilot/query", {
      method: "POST",
      body: JSON.stringify({ message })
    });
  } catch (e) {
    await delay(800);
    const query = message.toLowerCase();
    
    if (query.includes("stress") && query.includes("wheat")) {
      const wheatStressed = {
        type: "FeatureCollection",
        features: mock.MOCK_FIELDS_GEOJSON.features.filter(
          f => f.properties.crop_type === "wheat" && f.properties.stress_score > 0.15
        )
      };
      return {
        intent: "show_stressed_wheat",
        message: `Found ${wheatStressed.features.length} wheat fields experiencing moisture stress.`,
        data: wheatStressed,
        display_type: "map"
      };
    } else if (query.includes("village") && (query.includes("irrigation") || query.includes("need"))) {
      const needy = mock.MOCK_REPORTS.filter(r => r.advisory_priority !== "Low");
      return {
        intent: "villages_needing_irrigation",
        message: `Identified ${needy.length} villages with high or medium irrigation priorities.`,
        data: needy,
        display_type: "table"
      };
    } else if (query.includes("forecast") || query.includes("demand")) {
      return {
        intent: "forecast_water_demand",
        message: "Command Area forecast predicts a cumulative water requirement of 8,520 m³ over the next week.",
        data: mock.MOCK_FORECAST,
        display_type: "chart"
      };
    } else {
      return {
        intent: "unknown",
        message: (
          "I am the AgriSense GIS Copilot. You can ask me questions like:\n" +
          "- 'Show stressed wheat fields' (renders geospatial layers)\n" +
          "- 'Which villages need irrigation?' (shows priority tables)\n" +
          "- 'Forecast next week's water demand' (visualizes daily requirement charts)"
        ),
        data: null,
        display_type: "text"
      };
    }
  }
}
