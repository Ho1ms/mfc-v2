import { useEffect, useState, useRef } from "react";
import { api } from "@/api/client";
import type { Submission } from "@/api/types";
import { formatDateTime, statusClass, statusLabel } from "@/lib/status";
import { useAuth } from "@/auth/AuthProvider";
import { getToken } from "@/api/client";
import { useI18n } from "@/i18n";

export function SubmissionsPage() {
  const { profile } = useAuth();
  const [items, setItems] = useState<Submission[]>([]);
  const [selected, setSelected] = useState<Submission | null>(null);
  const { t } = useI18n();

  const wsRef = useRef<WebSocket | null>(null);
  useEffect(() => {
    const token = getToken();
    if (!token) return;
    const url = new URL(`${import.meta.env.VITE_API_URL}/api/ws/chat`, window.location.origin);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.searchParams.set("token", token);
    const ws = new WebSocket(url.toString());
    wsRef.current = ws;
    ws.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data);
        console.log("WS event", ev);
        if (ev.type === "submission_updated") {
          const submission = ev.data; // ← было ev.submission

          setItems((prev) =>
            prev.map((s) => s.id === submission.id ? submission : s)
          );
          setSelected((prev) => prev?.id === submission.id ? submission : prev);
}
      } catch {}
    };
    return () => ws.close();
  }, []);

  useEffect(() => {
    void api.get<Submission[]>("/submissions").then(setItems).catch(() => setItems([]));
  }, []);

  const open = async (s: Submission) => {
    const fresh = await api.get<Submission>(`/submissions/${s.id}`);
    setSelected(fresh);
  };

  return (
    <div className="screen">
      <h1 className="screen-title">{t("history:main:title")}</h1>
      <p className="screen-sub">{t("history:main:subtitle")}</p>

      {items.length === 0 && (
        <div className="card" style={{ textAlign: "center", color: "var(--ink-400)", padding: 24 }}>
          {t("history:main:no_submissions")}
        </div>
      )}

      {items.map((s) => (
        <div key={s.id} className="sub-card" onClick={() => open(s)}>
          <div>
            <div className="name">{`${s.form_name ?? t("word:submission")} #${s.id}`}</div>
            <div className="meta">{t("word:create_at")} {formatDateTime(s.created_at)}</div>
          </div>
          <span className={`tag ${statusClass(s.status)}`}>
            <span className="dot" />
            {statusLabel(s.status, profile?.language_code)}
          </span>
        </div>
      ))}

      {selected && (
        <SubmissionSheet
          submission={selected}
          lang={profile?.language_code}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}

function SubmissionSheet({
  submission,
  lang,
  onClose,
}: {
  submission: Submission;
  lang: string | null | undefined;
  onClose: () => void;
}) {
  const { t } = useI18n();
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        display: "flex",
        flexDirection: "column",
        justifyContent: "flex-end",
      }}
    >
      <div
        onClick={onClose}
        style={{ position: "absolute", inset: 0, background: "rgba(11,23,41,.4)" }}
      />
      <div
        style={{
          position: "relative",
          background: "#fff",
          borderTopLeftRadius: 22,
          borderTopRightRadius: 22,
          maxHeight: "90dvh",
          overflow: "auto",
          padding: 18,
          paddingBottom: "calc(18px + env(safe-area-inset-bottom))",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{`${submission.form_name ?? t("word:submission")} #${submission.id}`}</div>
            <div style={{ fontSize: 12.5, color: "var(--ink-400)" }}>
              {t("word:create_at")} {formatDateTime(submission.created_at)}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ border: "none", background: "transparent", fontSize: 22, lineHeight: 1, cursor: "pointer" }}
          >
            ×
          </button>
        </div>

        <span className={`tag ${statusClass(submission.status)}`}>
          <span className="dot" />
          {statusLabel(submission.status, lang)}
        </span>

        <h4 style={{ fontSize: 12, color: "var(--ink-500)", textTransform: "uppercase", letterSpacing: ".06em", margin: "18px 0 8px" }}>
          {t("word:form_data")}
        </h4>
        {Object.entries(submission.values).map(([k, v]) => (
          <div key={k} className="row">
            <span className="lbl">{submission.field_labels?.[k] ?? `${t("word:field")} #${k}`}</span>
            <span className="val">{renderValue(v)}</span>
          </div>
        ))}

        <h4 style={{ fontSize: 12, color: "var(--ink-500)", textTransform: "uppercase", letterSpacing: ".06em", margin: "18px 0 8px" }}>
          {t("history:main:status_history")}
        </h4>
        {(submission.history ?? []).map((h) => (
          <div key={h.id} className="row">
            <div>
              {h.from_status ? `${statusLabel(h.from_status, lang)} → ` : ""}
              <b>{statusLabel(h.to_status, lang)}</b>
              {h.comment && <div style={{ fontSize: 12, color: "var(--ink-400)" }}>{h.comment}</div>}
            </div>
            <span style={{ color: "var(--ink-400)", fontSize: 12 }}>{formatDateTime(h.changed_at)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function renderValue(v: unknown): React.ReactNode {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "boolean") return v ? "Да" : "Нет";
  return String(v);
}
