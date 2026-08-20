import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import { useAuth } from "../../context/AuthContext";
import publicBikeService from "../../services/publicBikeService";
import { ROUTES } from "../../constants/routes";

const RIDING_STYLES = ["로드", "MTB", "그래벨", "투어링", "도심 라이딩"];
const inputClass = "w-full rounded-lg border border-border bg-black/30 px-4 py-3 text-sm text-white outline-none focus:border-white/40";

export default function Account() {
  const navigate = useNavigate();
  const { user, isAuthenticated, isAuthLoading, updateProfile, deleteAccount } = useAuth();
  const [form, setForm] = useState({ nickname: "", ridingStyles: [], marketingConsent: false });
  const [history, setHistory] = useState([]);
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    setForm({
      nickname: user.nickname,
      ridingStyles: user.ridingStyles ?? [],
      marketingConsent: Boolean(user.marketingConsent),
    });
    publicBikeService.getForecastHistory(10).then(setHistory).catch(() => setHistory([]));
  }, [user]);

  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) navigate(ROUTES.LOGIN, { replace: true });
  }, [isAuthenticated, isAuthLoading, navigate]);

  const toggleStyle = (style) => setForm((current) => ({
    ...current,
    ridingStyles: current.ridingStyles.includes(style)
      ? current.ridingStyles.filter((item) => item !== style)
      : [...current.ridingStyles, style],
  }));

  const save = async (event) => {
    event.preventDefault();
    setError(""); setMessage("");
    try {
      await updateProfile(form);
      setMessage("회원정보가 수정되었습니다.");
    } catch (requestError) {
      setError(requestError.response?.data?.detail ?? "회원정보를 수정하지 못했습니다.");
    }
  };

  const withdraw = async () => {
    if (!password || !window.confirm("정말 탈퇴하시겠습니까? 계정이 비활성화됩니다.")) return;
    setError("");
    try {
      await deleteAccount(password);
      navigate(ROUTES.HOME);
    } catch (requestError) {
      setError(requestError.response?.data?.detail ?? "회원 탈퇴를 처리하지 못했습니다.");
    }
  };

  return <div className="space-y-8">
    <section className="rounded-xl border border-border bg-card p-6">
      <h1 className="mb-6 text-2xl font-extrabold">내 정보 수정</h1>
      {message && <p className="mb-4 rounded-lg border border-neon/30 bg-neon/10 p-3 text-sm text-neon">{message}</p>}
      {error && <p className="mb-4 rounded-lg border border-danger/30 bg-danger/10 p-3 text-sm text-danger">{error}</p>}
      <form onSubmit={save} className="space-y-5">
        <div><label className="mb-2 block text-xs text-gray-400">이메일</label><input className={inputClass} value={user?.email ?? ""} disabled /></div>
        <div><label className="mb-2 block text-xs text-gray-400">닉네임</label><input className={inputClass} value={form.nickname} minLength={2} maxLength={50} required onChange={(event) => setForm((current) => ({ ...current, nickname: event.target.value }))} /></div>
        <div><p className="mb-2 text-xs text-gray-400">라이딩 스타일</p><div className="flex flex-wrap gap-2">{RIDING_STYLES.map((style) => <button key={style} type="button" onClick={() => toggleStyle(style)} className={`rounded-lg border px-4 py-2 text-sm ${form.ridingStyles.includes(style) ? "border-neon text-neon" : "border-border text-gray-400"}`}>{style}</button>)}</div></div>
        <label className="flex items-center gap-2 text-sm text-gray-300"><input type="checkbox" checked={form.marketingConsent} onChange={(event) => setForm((current) => ({ ...current, marketingConsent: event.target.checked }))} />마케팅 정보 수신 동의</label>
        <Button type="submit">회원정보 저장</Button>
      </form>
    </section>

    <section className="rounded-xl border border-border bg-card p-6">
      <h2 className="mb-4 text-xl font-bold">내 수요예측 이력</h2>
      {history.length ? <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-gray-500"><tr><th className="py-2">대여소</th><th>예측 시점</th><th>수요</th><th>부족</th><th>위험도</th></tr></thead><tbody>{history.map((item) => <tr key={item.prediction_id} className="border-t border-border"><td className="py-3">{item.station_name}</td><td>{new Date(item.prediction_datetime).toLocaleString("ko-KR")}</td><td>{item.predicted_demand}건</td><td>{item.shortage_count}대</td><td>{item.risk_level} ({item.shortage_risk_percent}%)</td></tr>)}</tbody></table></div> : <p className="text-sm text-gray-500">로그인 상태에서 수요예측을 실행하면 여기에 저장됩니다.</p>}
    </section>

    <section className="rounded-xl border border-danger/30 bg-danger/5 p-6">
      <h2 className="mb-2 text-xl font-bold text-danger">회원 탈퇴</h2>
      <p className="mb-4 text-sm text-gray-400">비밀번호 확인 후 계정을 비활성화합니다.</p>
      <div className="flex max-w-lg gap-3"><input type="password" className={inputClass} value={password} placeholder="현재 비밀번호" onChange={(event) => setPassword(event.target.value)} /><Button type="button" variant="outline" onClick={withdraw}>탈퇴</Button></div>
    </section>
  </div>;
}
