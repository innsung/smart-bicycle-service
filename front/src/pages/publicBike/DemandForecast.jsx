import { useEffect, useMemo, useRef, useState } from "react";
import { AlertTriangle, Check, CheckCircle2, ChevronDown, Search, Sparkles, TrendingUp, Users } from "lucide-react";
import Button from "../../components/common/Button";
import Loading from "../../components/common/Loading";
import publicBikeService from "../../services/publicBikeService";
import { deriveDateFeatures } from "../../utils/forecastFeatures";

const HOUR_OPTIONS = Array.from({ length: 24 }, (_, hour) => hour);
const seoulDate = (offsetDays = 0) => {
  const value = new Date();
  value.setDate(value.getDate() + offsetDays);
  return value.toLocaleDateString("sv-SE", { timeZone: "Asia/Seoul" });
};
const fieldLabel = "mb-2 block text-xs text-gray-400";
const fieldInput = "w-full rounded-lg border border-border bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-white/40";
const LEVEL_STYLES = {
  높음: { text: "text-danger", bar: "bg-danger", border: "border-danger/30", chip: "border-danger/30 bg-danger/10 text-danger" },
  보통: { text: "text-warn", bar: "bg-warn", border: "border-warn/30", chip: "border-warn/30 bg-warn/10 text-warn" },
  낮음: { text: "text-neon", bar: "bg-neon", border: "border-neon/30", chip: "border-neon/30 bg-neon/10 text-neon" },
};

function ReadOnlyField({ label, value }) {
  return <div className="rounded-lg border border-border bg-black/20 px-4 py-3">
    <p className="text-xs text-gray-500">{label}</p><p className="mt-1 text-sm font-semibold text-white">{value}</p>
  </div>;
}

export default function DemandForecast() {
  const [stations, setStations] = useState([]);
  const [stationId, setStationId] = useState("");
  const [date, setDate] = useState(seoulDate());
  const [hour, setHour] = useState(new Date().getHours() + 1 > 23 ? 23 : new Date().getHours() + 1);
  const [loading, setLoading] = useState(false);
  const [stationLoading, setStationLoading] = useState(true);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [stationSearch, setStationSearch] = useState("");
  const [stationMenuOpen, setStationMenuOpen] = useState(false);
  const stationMenuRef = useRef(null);

  const station = stations.find((item) => String(item.id) === String(stationId));
  const filteredStations = useMemo(() => {
    const keyword = stationSearch.trim().toLowerCase();
    if (!keyword) return stations;
    return stations.filter((item) => `${item.name} ${item.id}`.toLowerCase().includes(keyword));
  }, [stations, stationSearch]);
  const dateFeatures = useMemo(() => deriveDateFeatures(date), [date]);
  const dateOptions = useMemo(() => Array.from({ length: 4 }, (_, offset) => ({
    value: seoulDate(offset),
    label: offset === 0 ? `오늘 (${seoulDate(offset)})` : offset === 1 ? `내일 (${seoulDate(offset)})` : `${offset}일 후 (${seoulDate(offset)})`,
  })), []);
  const selectableHours = useMemo(() => {
    if (date !== seoulDate()) return HOUR_OPTIONS;
    const currentSeoulHour = Number(
      new Intl.DateTimeFormat("en-GB", {
        hour: "2-digit",
        hour12: false,
        timeZone: "Asia/Seoul",
      }).format(new Date()),
    );
    return HOUR_OPTIONS.filter((value) => value > currentSeoulHour);
  }, [date]);

  useEffect(() => {
    if (selectableHours.length && !selectableHours.includes(hour)) setHour(selectableHours[0]);
  }, [hour, selectableHours]);

  useEffect(() => {
    publicBikeService.getStations(3000)
      .then((data) => {
        const items = data.stations ?? [];
        setStations(items);
        if (items.length) setStationId(String(items[0].id));
      })
      .catch((error) => setErrorMessage(error.response?.data?.detail ?? "대여소 정보를 불러오지 못했습니다."))
      .finally(() => setStationLoading(false));
  }, []);

  useEffect(() => {
    const closeOnOutsideClick = (event) => {
      if (stationMenuRef.current && !stationMenuRef.current.contains(event.target)) setStationMenuOpen(false);
    };
    document.addEventListener("mousedown", closeOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeOnOutsideClick);
  }, []);

  const handleRun = async () => {
    if (!stationId) return;
    setLoading(true); setResult(null); setErrorMessage("");
    try {
      setResult(await publicBikeService.getForecast({ stationId, date, hour }));
    } catch (error) {
      setErrorMessage(error.response?.data?.detail ?? "수요예측 데이터를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const style = LEVEL_STYLES[result?.demand_level] ?? LEVEL_STYLES.보통;
  const weather = result?.weather;
  const history = result?.historical_features;

  return <div>
    <p className="mb-1 text-sm font-semibold text-bike">AI 예측</p>
    <h2 className="mb-6 text-2xl font-extrabold text-white">수요·자전거 부족 위험도 예측</h2>

    {result && !loading && <div className={`mb-8 overflow-hidden rounded-xl border bg-card ${style.border}`}>
      <div className="flex items-center gap-3 px-6 py-4">
        <CheckCircle2 className={`h-5 w-5 ${style.text}`} /><b className="text-sm text-white">예측 완료</b>
        <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${style.chip}`}>
          {result.predicted_demand}건 · {result.risk_level}
        </span>
      </div>
      <div className="border-t border-border px-6 pb-6 pt-5">
        <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-border bg-black/20 p-5">
            <p className="mb-3 flex items-center gap-2 text-xs text-gray-400"><TrendingUp className="h-4 w-4" />예측 대여 수요</p>
            <p className={`text-4xl font-extrabold ${style.text}`}>{result.predicted_demand}<span className="ml-1 text-lg text-gray-400">건</span></p>
            <p className="mt-2 text-xs text-gray-500">{result.station_name} · {date} {String(hour).padStart(2, "0")}:00</p>
          </div>
          <div className="rounded-lg border border-border bg-black/20 p-5">
            <p className="mb-3 flex items-center justify-end gap-2 text-xs text-gray-400"><Users className="h-4 w-4" />자전거 부족 위험도</p>
            <p className={`text-right text-4xl font-extrabold ${style.text}`}>{result.shortage_risk_percent}<span className="ml-1 text-lg text-gray-400">%</span></p>
            <p className="mb-2 mt-2 text-right text-xs text-gray-500">예측 {result.predicted_demand}건 / 현재 {result.available_bikes}대 · 부족 {result.shortage_count}대</p>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/10"><div className={`h-full ${style.bar}`} style={{ width: `${result.shortage_risk_percent}%` }} /></div>
          </div>
        </div>
        <div className="flex gap-2 rounded-lg border border-border bg-black/20 p-4 text-sm text-gray-300"><AlertTriangle className={`h-4 w-4 shrink-0 ${style.text}`} />{result.message}</div>
      </div>
    </div>}

    {errorMessage && <div className="mb-6 rounded-xl border border-danger/30 bg-danger/10 p-4 text-sm text-danger">{errorMessage}</div>}
    <div className="rounded-xl border border-border bg-card p-6">
      <label className={fieldLabel}>대여소</label>
      <div ref={stationMenuRef} className="relative mb-3">
        <button
          type="button"
          disabled={stationLoading}
          onClick={() => setStationMenuOpen((open) => !open)}
          className={`${fieldInput} flex items-center justify-between text-left disabled:opacity-50`}
        >
          <span className="truncate">{station?.name ?? (stationLoading ? "대여소 불러오는 중..." : "대여소를 선택하세요")}</span>
          <ChevronDown className={`h-4 w-4 shrink-0 text-gray-400 transition-transform ${stationMenuOpen ? "rotate-180" : ""}`} />
        </button>

        {stationMenuOpen && <div className="absolute z-50 mt-2 w-full overflow-hidden rounded-lg border border-border bg-[#151515] shadow-2xl">
          <div className="border-b border-border p-3">
            <div className="flex items-center gap-2 rounded-lg border border-border bg-black/40 px-3">
              <Search className="h-4 w-4 shrink-0 text-gray-500" />
              <input
                autoFocus
                value={stationSearch}
                onChange={(event) => setStationSearch(event.target.value)}
                placeholder="대여소 번호 또는 이름 검색"
                className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-gray-600"
              />
            </div>
          </div>
          <div className="max-h-72 overflow-y-auto py-1">
            {filteredStations.length ? filteredStations.map((item) => {
              const selected = String(item.id) === String(stationId);
              return <button
                type="button"
                key={item.id}
                onClick={() => {
                  setStationId(String(item.id));
                  setStationMenuOpen(false);
                  setStationSearch("");
                  setResult(null);
                }}
                className={`flex w-full items-center justify-between gap-3 px-4 py-2.5 text-left text-sm hover:bg-white/5 ${selected ? "bg-bike/10 text-bike" : "text-white"}`}
              >
                <span className="truncate">{item.name}</span>
                <span className="flex shrink-0 items-center gap-2 text-xs text-gray-500">
                  {item.available}대
                  {selected && <Check className="h-4 w-4 text-bike" />}
                </span>
              </button>;
            }) : <p className="px-4 py-8 text-center text-sm text-gray-500">검색 결과가 없습니다.</p>}
          </div>
          <p className="border-t border-border px-4 py-2 text-xs text-gray-500">검색 결과 {filteredStations.length.toLocaleString()}개</p>
        </div>}
      </div>
      <div className="mb-6 grid grid-cols-2 gap-3">
        <ReadOnlyField label="현재 대여 가능" value={station ? `${station.available}대` : "-"} />
        <ReadOnlyField label="데이터 방식" value="서울시 실시간 API" />
      </div>

      <p className="mb-4 text-sm font-semibold text-white">예측 시점</p>
      <div className="mb-3 grid grid-cols-2 gap-3">
        <div><label className={fieldLabel}>예측 날짜</label><select value={date} onChange={(event) => setDate(event.target.value)} className={fieldInput}>{dateOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></div>
        <div><label className={fieldLabel}>예측 시간</label><select value={hour} onChange={(event) => setHour(Number(event.target.value))} className={fieldInput}>{selectableHours.map((value) => <option key={value} value={value}>{String(value).padStart(2, "0")}:00</option>)}</select></div>
      </div>
      <div className="mb-6 grid grid-cols-2 gap-3"><ReadOnlyField label="요일" value={dateFeatures?.dayOfWeekLabel ?? "-"} /><ReadOnlyField label="휴일 여부" value={dateFeatures?.holidayLabel ?? "-"} /></div>

      <p className="mb-4 text-sm font-semibold text-white">백엔드 자동 조회 데이터</p>
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <ReadOnlyField label="기온" value={weather ? `${weather.temperature}℃` : "예측 후 표시"} />
        <ReadOnlyField label="습도" value={weather ? `${weather.humidity}%` : "예측 후 표시"} />
        <ReadOnlyField label="강수량" value={weather ? `${weather.rainfall}mm` : "예측 후 표시"} />
        <ReadOnlyField label="풍속" value={weather ? `${weather.wind_speed}m/s` : "예측 후 표시"} />
        <ReadOnlyField label="최근 1시간 대여량" value={history ? `${history.recent_1h_rental_count}건` : "자동 조회"} />
        <ReadOnlyField label="전일 동일 시간대" value={history ? `${history.prev_day_same_hour_rental_count}건` : "자동 조회"} />
        <ReadOnlyField label="최근 7일 동일 시간 평균" value={history ? `${Number(history.rolling_7d_same_hour_avg).toFixed(1)}건` : "자동 조회"} />
        <ReadOnlyField label="현재 자전거" value={result ? `${result.available_bikes}대` : "자동 조회"} />
      </div>

      <Button variant="cyan" size="lg" className="w-full" onClick={handleRun} disabled={loading || stationLoading || !stationId}>
        <Sparkles className="h-4 w-4" />수요예측 실행
      </Button>
    </div>
    {(loading || stationLoading) && <Loading label={stationLoading ? "대여소 정보를 불러오는 중..." : "AI가 수요를 예측하는 중..."} />}
  </div>;
}
