import api from "../api/axios";
import { ROUTES_MOCK } from "../constants/mockData";

async function getSummary() {
  const { data } = await api.get("/bike/seoul/summary");
  return data;
}

async function getBikeRoutes() {
  try {
    const { data } = await api.get("/bike/seoul/routes");
    return data;
  } catch {
    return ROUTES_MOCK;
  }
}

async function getStations(limit = 6) {
  const { data } = await api.get("/bike/seoul/stations", { params: { limit } });
  return data;
}

async function getAnalysis() {
  const { data } = await api.get("/ai/bike/analysis");
  return data;
}

async function getForecast({ stationId, date, hour }) {
  const { data } = await api.post("/ai/bike/forecast", {
    station_id: String(stationId),
    date,
    hour: Number(hour),
  });
  return data;
}

const publicBikeService = { getSummary, getBikeRoutes, getStations, getAnalysis, getForecast };
export default publicBikeService;
