import api from "../api/axios";
import {
  ROUTES_MOCK,
} from "../constants/mockData";

// 향후 FastAPI: GET /api/bike/seoul/summary
async function getSummary() {
  const { data } = await api.get("/bike/seoul/summary");
  return data;
}

// 향후 FastAPI: GET /api/bike/seoul/routes
async function getBikeRoutes() {
  try {
    const { data } = await api.get("/bike/seoul/routes");
    return data;
  } catch {
    return ROUTES_MOCK.filter((r) => r.bikeType === "따릉이");
  }
}

// 향후 FastAPI: GET /api/bike/seoul/stations
async function getStations() {
  const { data } = await api.get("/bike/seoul/stations");
  return data;
}

// 향후 FastAPI: GET /api/ai/bike/analysis
async function getAnalysis() {
  const { data } = await api.get("/ai/bike/analysis");
  return data;
}

const publicBikeService = { getSummary, getBikeRoutes, getStations, getAnalysis };
export default publicBikeService;
