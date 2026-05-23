import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/api/client";
import type {
  FormTemplate,
  MonitoringLookup,
  MonitoringSubscription,
  Profile,
} from "@/api/types";
import { Icon } from "@/components/Icon";
import { useAuth } from "@/auth/AuthProvider";
import { formatDateTime } from "@/lib/status";
import { useI18n } from "@/i18n";

function profileComplete(p: Profile | null | undefined): boolean {
  if (!p) return false;
  return Boolean(
    p.last_name?.trim() &&
      p.first_name?.trim() &&
      p.patronymic?.trim() &&
      p.birth_date &&
      p.study_group?.trim(),
  );
}

export function ServicesPage() {
  const { t } = useI18n();
  const { profile } = useAuth();
  const navigate = useNavigate();
  const [forms, setForms] = useState<FormTemplate[]>([]);

  useEffect(() => {
    void api.get<FormTemplate[]>("/forms").then(setForms).catch(() => setForms([]));
  }, []);

  const isComplete = useMemo(() => profileComplete(profile), [profile]);
  const banForms = profile?.ban_forms ?? false;

  const openForm = (formId: number) => {
    if (banForms) return;
    if (!isComplete) {
      navigate("/profile");
      return;
    }
    navigate(`/submit/${formId}`);
  };

  return (
    <div className="screen">
      <h1 className="screen-title">{t("services:main:services")}</h1>
      <p className="screen-sub">{t("services:main:services_sub")}</p>

      {!isComplete && !banForms && (
        <div
          onClick={() => navigate("/profile")}
          style={{
            cursor: "pointer",
            marginBottom: 12,
            padding: "10px 12px",
            borderRadius: 10,
            background: "var(--st-rej-bg)",
            color: "var(--st-rej-fg)",
            fontSize: 13,
            lineHeight: 1.45,
          }}
        >
          {t("services:main:profile_incomplete")}
        </div>
      )}

      {banForms && (
        <div
          style={{
            marginBottom: 12,
            padding: "10px 12px",
            borderRadius: 10,
            background: "var(--st-rej-bg)",
            color: "var(--st-rej-fg)",
            fontSize: 13,
            lineHeight: 1.45,
          }}
        >
          {t("services:main:ban_forms")} <br />
          {profile?.ban_forms_reason ? `${t("word:reason")}: ${profile.ban_forms_reason}` : ""}
        </div>
      )}

      <h3
        style={{
          margin: "16px 0 10px",
          fontSize: 13,
          color: "var(--ink-500)",
          textTransform: "uppercase",
          letterSpacing: ".06em",
        }}
      >
        {t("services:main:available_forms")}
      </h3>
      {forms.length === 0 && (
        <div className="card" style={{ color: "var(--ink-400)" }}>{t("services:main:no_forms")}</div>
      )}
      {forms.map((f) => (
        <a
          key={f.id}
          href={`/submit/${f.id}`}
          onClick={(e) => {
            e.preventDefault();
            openForm(f.id);
          }}
          className="card"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            textDecoration: "none",
            color: "inherit",
            opacity: banForms ? 0.5 : 1,
            cursor: banForms ? "not-allowed" : "pointer",
          }}
        >
          <div>
            <div style={{ fontWeight: 700, fontSize: 14.5 }}>{f.name}</div>
            {f.description && (
              <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 2 }}>{f.description}</div>
            )}
          </div>
          <span className="ico" style={{ width: 18, height: 18, color: "var(--ink-300)" }}>
            <Icon.ChevronRight />
          </span>
        </a>
      ))}

      <MonitoringBlock />
    </div>
  );
}

function MonitoringBlock() {
  const [number, setNumber] = useState("");
  const [result, setResult] = useState<MonitoringLookup | null>(null);
  const [sub, setSub] = useState<MonitoringSubscription | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {t} = useI18n();
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
      setError((e as Error)?.message ?? t("services:main:status_error"));
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
    <>
      <h3
        style={{
          margin: "22px 0 10px",
          fontSize: 13,
          color: "var(--ink-500)",
          textTransform: "uppercase",
          letterSpacing: ".06em",
        }}
      >
        {t("services:main:check_stats")}
      </h3>
      <div className="card">
        <label className="field-label">{t("services:main:request_number")}</label>
        <input
          className="input"
          placeholder={t("services:main:request_number_placeholder")}
          value={number}
          onChange={(e) => setNumber(e.target.value)}
        />
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button
            className="btn btn-primary"
            disabled={!number.trim() || busy}
            onClick={() => void onSearch()}
          >
            {busy ? t("services:main:searching") : t("services:main:search")}
          </button>
        </div>
        {error && (
          <div style={{ marginTop: 12, color: "var(--st-rej-fg)", fontSize: 13 }}>{error}</div>
        )}
      </div>

      {result && (
        <div className="card">
          <div style={{ fontWeight: 700, fontSize: 15 }}>{t("services:main:request_number")}: {result.request_number}</div>
          <div className="status-box">
            <div className="lbl">{t("services:main:current_status")}</div>
            <div className="val">{result.status ?? t("services:main:no_find")}</div>
            {result.checked_at && (
              <div style={{ marginTop: 8, fontSize: 12, color: "var(--ink-500)" }}>
                {t("services:main:checked_at")}: {formatDateTime(result.checked_at)}
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
                  ? t("services:main:unsubscribe")
                  : t("services:main:subscribe")}
              </button>
              <div style={{ fontSize: 12, color: "var(--ink-400)", marginTop: 8, textAlign: "center" }}>
                {result.is_subscribed
                  ? t("services:main:subscribed_msg")
                  : t("services:main:subscribe_msg")}
              </div>
            </div>
          )}
        </div>
      )}

      {!result && sub?.is_active && (
        <div className="card">
          <div style={{ fontSize: 13, color: "var(--ink-500)" }}>
            {t("services:main:active_subscription")}: <b>{sub.request_number}</b>
          </div>
        </div>
      )}
    </>
  );
}
