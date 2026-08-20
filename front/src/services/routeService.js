import api from "../api/axios";

async function getRoutes() {
  const { data } = await api.get("/routes");
  return data;
}

async function getRouteDetail(id) {
  const { data } = await api.get(`/routes/${id}`);
  return data;
}

async function getPersonalRoutes() {
  const { data } = await api.get("/routes", { params: { type: "personal" } });
  return data;
}

const routeService = { getRoutes, getRouteDetail, getPersonalRoutes };
export default routeService;
