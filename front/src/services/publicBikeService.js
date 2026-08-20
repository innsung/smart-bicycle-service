import api from "../api/axios";

async function getSummary() {
  const { data } = await api.get("/bike/seoul/summary");
  return data;
}

async function getBikeRoutes() {
  const { data } = await api.get("/bike/seoul/routes");
  return data;
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

async function getForecastHistory(limit = 20) {
  const { data } = await api.get("/ai/bike/forecast/history", { params: { limit } });
  return data;
}

const publicBikeService = { getSummary, getBikeRoutes, getStations, getAnalysis, getForecast, getForecastHistory };
export default publicBikeService;
