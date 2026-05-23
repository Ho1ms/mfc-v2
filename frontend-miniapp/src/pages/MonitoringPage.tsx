import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { MonitoringLookup, MonitoringSubscription } from "@/api/types";
import { formatDateTime } from "@/lib/status";

export function MonitoringPage() {
  const [number, setNumber] = useState("");
  const [result, setResult] = useState<MonitoringLookup | null>(null);
  const [sub, setSub] = useState<MonitoringSubscription | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void api
      .get<MonitoringSubscription>("/monitoring/subscription")
      .then((s) => {
        setSub(s);
        if (s.is_active && s.request_number) {
          setNumber(s.request_number);
          setResult({
            request_number: s.request_number,
            status: s.last_status,
            checked_at: s.checked_at,
            is_subscribed: true,
          });
        }
      })
      .catch(() => undefined);
  }, []);

  const onSearch = async () => {
    if (!number.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const r = await api.get<MonitoringLookup>(
        `/monitoring/lookup?request_number=${encodeURIComponent(number.trim())}`,
      );
      setResult(r);
    } catch (e) {
      setError((e as Error)?.message ?? "Не удалось получить статус");
    } finally {
      setBusy(false);
    }
  };

  const toggleSubscribe = async () => {
    if (!result) return;
    setBusy(true);
    try {
      if (result.is_subscribed) {
        await api.post("/monitoring/unsubscribe", { request_number: result.request_number });
        setResult({ ...result, is_subscribed: false });
      } else {
        await api.post("/monitoring/subscribe", { request_number: result.request_number });
        setResult({ ...result, is_subscribed: true });
      }
      setSub(await api.get<MonitoringSubscription>("/monitoring/subscription"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="screen">
      <h1 className="screen-title">Статус заявки</h1>
      <p className="screen-sub">Отслеживание по номеру из общего реестра</p>

      <div className="card">
        <label className="field-label">Номер заявки</label>
        <input
          className="input"
          placeholder="Например, REQ-2024-0001"
          value={number}
          onChange={(e) => setNumber(e.target.value)}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button
            className="btn btn-primary"
            disabled={!number.trim() || busy}
            onClick={() => void onSearch()}
          >
            {busy ? "Ищем…" : "Поиск"}
          </button>
        </div>
        {error && (
          <div style={{ marginTop: 12, color: "var(--st-rej-fg)", fontSize: 13 }}>{error}</div>
        )}
      </div>

      {result && (
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 15 }}>Заявка {result.request_number}</div>
          <div className="status-box">
            <div className="lbl">Текущий статус</div>
            <div className="val">{result.status ?? "не найдено"}</div>
            {result.checked_at && (
              <div style={{ marginTop: 8, fontSize: 12, color: "var(--ink-500)" }}>
                Обновлено: {formatDateTime(result.checked_at)}
              </div>
            )}
          </div>

          {result.status && (
            <div style={{ marginTop: 14 }}>
              <button
                className={`btn ${result.is_subscribed ? "btn-danger" : "btn-primary"}`}
                disabled={busy}
                onClick={() => void toggleSubscribe()}
              >
                {result.is_subscribed
                  ? "Отписаться от уведомлений"
                  : "Подписаться на изменения"}
              </button>
              <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 8, textAlign: "center" }}>
                {result.is_subscribed
                  ? "Мы пришлём уведомление в MAX, как только статус изменится."
                  : "Подписавшись, вы будете получать уведомления о смене статуса."}
              </div>
            </div>
          )}
        </div>
      )}

      {!result && sub?.is_active && (
        <div className="card">
          <div style={{ fontSize: 13, color: "var(--ink-500)" }}>
            Активная подписка: <b>{sub.request_number}</b>
          </div>
        </div>
      )}
    </div>
  );
}
