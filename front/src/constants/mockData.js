export const HOME_STATS = [
  { label: "활성 라이더", value: "50,000+" },
  { label: "등록 루트", value: "12,800+" },
  { label: "앱 평점", value: "4.9", suffix: "★" },
];

export const FEATURES = [
  {
    icon: "Map",
    tag: "AI 추천",
    title: "스마트 루트 탐색",
    description: "AI가 실력, 선호 지형, 현재 날씨를 분석해 최적의 루트를 추천합니다.",
  },
  {
    icon: "Users",
    tag: "소셜",
    title: "라이더 커뮤니티",
    description: "지역 라이더들과 단체 라이딩을 기획하고, 실시간으로 소통하세요.",
  },
  {
    icon: "Activity",
    tag: "실시간",
    title: "라이딩 트래킹",
    description: "GPS 기반 속도·거리·고도 데이터를 자동 기록하고 통계로 분석해보세요.",
  },
  {
    icon: "Trophy",
    tag: "게이미피케이션",
    title: "챌린지 & 리워드",
    description: "매달 새로운 챌린지에 도전하고 포인트와 뱃지를 획득하세요.",
  },
];

export const REVIEWS = [
  {
    name: "김민준",
    handle: "@minjun_rides",
    rating: 5,
    likes: 214,
    text: "루트 추천 기능이 정말 뛰어나요. 매번 새로운 코스를 찾아주는 재미가 있어서 라이딩이 더 즐거워졌어요.",
  },
  {
    name: "박서연",
    handle: "@seoyeon.cycling",
    rating: 5,
    likes: 87,
    text: "커뮤니티를 통해 지역 라이더들을 만났는데 지금은 함께 달리는 절친이 됐어요. 최고의 앱입니다.",
  },
  {
    name: "이재혁",
    handle: "@jaehyuk_mtb",
    rating: 5,
    likes: 341,
    text: "트래킹 데이터 분석이 정말해서 제 라이딩 실력이 눈에 띄게 향상됐어요. 데이터 덕후에겐 강추!",
  },
];

export const COMMUNITY_STATS = [
  { label: "추천 단체 라이딩", value: "200+" },
  { label: "지역 라이딩 클럽", value: "83개" },
  { label: "챌린지 완주율", value: "98%" },
  { label: "전국 광역시도 지원", value: "전국" },
];

export const BIKE_HERO_STATS = [
  { label: "오늘 총 이용", value: "142,800", unit: "건", trend: "+8.4%" },
  { label: "운영 대여소", value: "2,692", unit: "개소", trend: "+2.1%" },
  { label: "현재 이용 중", value: "4,318", unit: "대", trend: "+12.3%" },
  { label: "평균 이용 시간", value: "17.4", unit: "분", trend: "-1.8%" },
];

export const STATIONS_MOCK = [
  { id: 1, name: "여의나루역 1번출구", distance: "120m", available: 14, total: 20, status: "GOOD" },
  { id: 2, name: "여의도공원 북측", distance: "340m", available: 3, total: 15, status: "LOW" },
  { id: 3, name: "국회의사당역 앞", distance: "580m", available: 0, total: 18, status: "EMPTY" },
  { id: 4, name: "마포대교 남단", distance: "820m", available: 8, total: 12, status: "GOOD" },
  { id: 5, name: "합정역 6번출구", distance: "1.1km", available: 2, total: 20, status: "LOW" },
  { id: 6, name: "당인리문화창작소", distance: "1.4km", available: 6, total: 10, status: "GOOD" },
];

export const HOURLY_USAGE = [
  { hour: "0시", count: 1200 }, { hour: "1시", count: 800 }, { hour: "2시", count: 500 },
  { hour: "3시", count: 400 }, { hour: "4시", count: 600 }, { hour: "5시", count: 1500 },
  { hour: "6시", count: 4000 }, { hour: "7시", count: 12000 }, { hour: "8시", count: 24500 },
  { hour: "9시", count: 16000 }, { hour: "10시", count: 10000 }, { hour: "11시", count: 9500 },
  { hour: "12시", count: 13500 }, { hour: "13시", count: 10500 }, { hour: "14시", count: 9800 },
  { hour: "15시", count: 10200 }, { hour: "16시", count: 12500 }, { hour: "17시", count: 21000 },
  { hour: "18시", count: 29500 }, { hour: "19시", count: 24000 }, { hour: "20시", count: 16000 },
  { hour: "21시", count: 11000 }, { hour: "22시", count: 7000 }, { hour: "23시", count: 3000 },
];

export const MONTHLY_USAGE = [
  { month: "1월", count: 1500000 }, { month: "2월", count: 1700000 }, { month: "3월", count: 2600000 },
  { month: "4월", count: 3800000 }, { month: "5월", count: 4200000 }, { month: "6월", count: 3600000 },
  { month: "7월", count: 3000000 }, { month: "8월", count: 2800000 }, { month: "9월", count: 3900000 },
  { month: "10월", count: 4300000 }, { month: "11월", count: 3100000 }, { month: "12월", count: 1600000 },
];

export const TOP_STATIONS = [
  { name: "여의나루역 1번출구", count: 4600 },
  { name: "뚝섬유원지", count: 3900 },
  { name: "합정역 6번출구", count: 3700 },
  { name: "홍대입구역 9번출구", count: 3400 },
  { name: "반포한강공원", count: 3200 },
  { name: "이태원역 4번출구", count: 3000 },
];

export const AGE_DISTRIBUTION = [
  { age: "10대", percent: 8 },
  { age: "20대", percent: 34.1 },
  { age: "30대", percent: 28.4 },
  { age: "40대", percent: 18 },
  { age: "50대", percent: 9 },
  { age: "60대+", percent: 2.5 },
];

export const AI_INSIGHTS = [
  {
    tag: "패턴",
    icon: "TrendingUp",
    title: "퇴근 시간 수요가 출근보다 23% 높음",
    description: "17~19시 이용량이 7~9시 대비 평균 23.4% 높습니다. 귀가 시 자전거 이용 선호도가 뚜렷하게 증가하는 추세입니다.",
    metricLabel: "퇴근 vs 출근",
    metricValue: "+23.4%",
    tone: "up",
  },
  {
    tag: "날씨",
    icon: "CloudRain",
    title: "강수 시 이용률 67% 급감",
    description: "비 오는 날 이용량이 맑은 날 대비 67% 감소합니다. 날씨 예보 연동 실시간 재고 분산 전략이 필요합니다.",
    metricLabel: "비 vs 맑음",
    metricValue: "-67%",
    tone: "down",
  },
  {
    tag: "이용자",
    icon: "Users",
    title: "20~30대가 전체 이용의 62% 점유",
    description: "핵심 이용층은 20대(34.1%)와 30대(28.4%)입니다. 40~50대 유입 확대를 위한 생활형 루트 콘텐츠 강화가 효과적입니다.",
    metricLabel: "20~30대 비중",
    metricValue: "62%",
    tone: "neutral",
  },
  {
    tag: "패턴",
    icon: "Zap",
    title: "평균 이동 거리 2.8km, 10분 미만 68%",
    description: "전체 대여의 68%가 10분 미만 단거리 이용입니다. 지하철역 반경 500m 내 대여소 밀도 확충이 핵심 과제입니다.",
    metricLabel: "평균 이동 거리",
    metricValue: "2.8km",
    tone: "neutral",
  },
  {
    tag: "경로",
    icon: "MapPin",
    title: "여의나루-합정 구간 반복 이용률 1위",
    description: "동일 구간 재이용률이 78%에 달하는 여의나루-합정 코스. 한강변 인기 코스 우선 정비 및 실시간 알림 강화를 권장합니다.",
    metricLabel: "재이용률",
    metricValue: "78%",
    tone: "up",
  },
  {
    tag: "예측",
    icon: "Sparkles",
    title: "봄 성수기 수요 조기 포화 예측",
    description: "4~5월 한강변 대여소는 오후 4시부터 재고 소진율 92%에 도달. AI 모델은 2주 전부터 해당 구간 집중 보충을 권장합니다.",
    metricLabel: "성수기 소진율",
    metricValue: "92%",
    tone: "up",
  },
];

// 수요예측 입력 폼의 대여소 목록. district/rackCount는 대여소 선택 시 자동 표시되는 값이고,
// recentHourlyRentals는 "최근 1시간 대여량" 과거 이용 이력 입력값의 초기 표시값입니다.
export const DASHBOARD_STATS = {
  user: {
    name: "김민준",
    handle: "@minzun_rides",
    level: "중급 라이더",
    joinedDays: 142,
    streak: 7,
  },
  totals: [
    { label: "총 라이딩", value: "214", unit: "회", icon: "Map" },
    { label: "누적 거리", value: "3,842", unit: "km", icon: "TrendingUp" },
    { label: "총 라이딩 시간", value: "186", unit: "h", icon: "Clock" },
    { label: "연속 라이딩", value: "7", unit: "일", icon: "Flame" },
  ],
  activity: {
    badges: 12,
    challenges: 8,
    followers: 34,
    savedRoutes: 27,
  },
};

export const QUICK_MENU = [
  { icon: "Map", label: "루트 탐색", path: "/riding/start" },
  { icon: "Bike", label: "따릉이", path: "/bike/seoul" },
  { icon: "Users", label: "커뮤니티", path: "/community" },
  { icon: "Trophy", label: "챌린지", path: "/challenges" },
];

export const COMMUNITY_FEED = [
  { name: "박서연", initial: "박", text: "님이 북한산 루트 완주 인증", time: "5분 전", likes: 24 },
  { name: "이재혁", initial: "이", text: "님이 제주 환상길 D-7 모집 중", time: "22분 전", likes: 41 },
  { name: "최지현", initial: "최", text: "님이 한강 종주 신기록 달성", time: "1시간 전", likes: 87 },
];

export const CHATBOT_QUICK_QUESTIONS = ["루트 추천해줘", "따릉이 정보", "요금이 궁금해", "앱 다운로드"];

// 실제 답변은 FastAPI/OpenAI에서 받고, 프론트에는 최초 안내 문구만 둡니다.
export const CHATBOT_WELCOME_MESSAGE =
  "안녕하세요! 페달업 AI 도우미입니다 🚴 루트 추천, 따릉이 정보, 라이딩 팁 등 무엇이든 물어보세요.";
