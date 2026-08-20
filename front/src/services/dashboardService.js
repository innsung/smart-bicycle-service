import api from "../api/axios";
import { DASHBOARD_STATS, QUICK_MENU, COMMUNITY_FEED } from "../constants/mockData";
import routeService from "./routeService";

// 향후 FastAPI: GET /api/dashboard
async function getDashboard() {
  try {
    const { data } = await api.get("/dashboard");
    return data;
  } catch {
    const routes = await routeService.getRoutes();
    return {
      ...DASHBOARD_STATS,
      recommendedRoute: routes.find((route) => route.id === "hangang-yeouinaru-hapjeong") ?? routes[0],
      quickMenu: QUICK_MENU,
      communityFeed: COMMUNITY_FEED,
    };
  }
}

const dashboardService = { getDashboard };
export default dashboardService;
