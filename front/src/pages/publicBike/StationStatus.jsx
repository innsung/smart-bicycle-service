import { useEffect, useState } from "react";
import StationCard from "../../components/cards/StationCard";
import AreaChartCard from "../../components/charts/AreaChartCard";
import Loading from "../../components/common/Loading";
import publicBikeService from "../../services/publicBikeService";

const LEGEND = [
  { label: "충분", color: "bg-neon" },
  { label: "부족", color: "bg-warn" },
  { label: "없음", color: "bg-danger" },
];

export default function StationStatus() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    publicBikeService.getStations()
      .then(setData)
      .catch((requestError) => setError(requestError.response?.data?.detail || "대여소 현황을 불러오지 못했습니다."));
  }, []);

  if (error) return <div className="rounded-xl border border-danger/30 bg-danger/10 p-5 text-danger">{error}</div>;
  if (!data) return <Loading />;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-bike">실시간 현황</p>
          <h2 className="mt-1 text-2xl font-extrabold text-white">내 주변 대여소</h2>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-400">
          {LEGEND.map((item) => (
            <span key={item.label} className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${item.color}`} />
              {item.label}
            </span>
          ))}
        </div>
      </div>

      <div className="mb-12 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.stations.map((station) => (
          <StationCard key={station.id} station={station} />
        ))}
      </div>

      <p className="mb-1 text-sm font-semibold text-bike">시간대 분석</p>
      <h2 className="mb-4 text-2xl font-extrabold text-white">오늘의 시간대별 이용량</h2>
      {data.hourlyUsage.length > 0 ? (
        <AreaChartCard data={data.hourlyUsage} xKey="hour" yKey="count" color="#38BDF8" />
      ) : (
        <p className="rounded-xl border border-border bg-card p-5 text-sm text-gray-400">
          시간대별 이용정보 CSV를 연결하면 이 차트가 표시됩니다.
        </p>
      )}
    </div>
  );
}
