import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, getCurrentAdminId, getToken } from "@/api/client";
import type {
  FormField,
  FormTemplate,
  FormTemplateDetailed,
  StatusHistoryItem,
  Submission,
  SubmissionStatus,
  Submitter,
} from "@/api/types";
import { StatusTag } from "@/components/StatusTag";
import { Avatar } from "@/components/Avatar";
import { UserCardPanel } from "@/components/UserCardPanel";
import { formatDateTime, statusLabel } from "@/lib/status";
import { notify } from "@/lib/notify";

const STATUSES: SubmissionStatus[] = ["new", "in_work", "done", "rejected"];

const NEXT_STATUSES: Record<SubmissionStatus, SubmissionStatus[]> = {
  new: ["in_work", "rejected"],
  in_work: ["done", "rejected"],
  rejected: [],
  done: [],
};

function submitterFullName(s: Submitter | null | undefined): string {
  if (!s) return "—";
  const parts = [s.last_name, s.first_name, s.patronymic].filter(Boolean) as string[];
  if (parts.length) return parts.join(" ");
  return s.username ?? "—";
}

function formatBirthDate(d: string | null | undefined): string {
  if (!d) return "—";
  try {
    return new Date(d).toLocaleDateString("ru-RU");
  } catch {
    return d;
  }
}

export function SubmissionsPage() {
  const [forms, setForms] = useState<FormTemplate[]>([]);
  const [activeForm, setActiveForm] = useState<FormTemplateDetailed | null>(null);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [statusFilter, setStatusFilter] = useState<SubmissionStatus | "all">("all");
  const [fieldFilters, setFieldFilters] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<Submission | null>(null);
  const [openUserId, setOpenUserId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const currentAdminId = getCurrentAdminId();

  useEffect(() => {
    void api.get<FormTemplate[]>("/forms").then((rows) => {
      setForms(rows);
      if (rows.length) {
        void loadForm(rows[0].id);
      }
    });
  }, []);

  const loadForm = useCallback(async (formId: number) => {
    const tpl = await api.get<FormTemplateDetailed>(`/forms/${formId}`);
    setActiveForm(tpl);
  }, []);

  const reload = useCallback(async () => {
    if (!activeForm) return;
    setLoading(true);
    const params = new URLSearchParams();
    params.set("form_id", String(activeForm.id));
    if (statusFilter !== "all") params.set("status", statusFilter);
    for (const [k, v] of Object.entries(fieldFilters)) {
      if (v) params.set(k, v);
    }
    try {
      const rows = await api.get<Submission[]>(`/submissions?${params.toString()}`);
      setSubmissions(rows);
    } finally {
      setLoading(false);
    }
  }, [activeForm, statusFilter, fieldFilters]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const changeStatus = async (sub: Submission, status: SubmissionStatus) => {
    let comment: string | undefined = undefined;
    if (status === "rejected") {
      const result = window.prompt("Комментарий к отклонению (необязательно)");
      if (result === null) return; 
      comment = result || undefined;
    }
    const updated = await api.patch<Submission>(`/submissions/${sub.id}/status`, { status, comment });
   
    setSubmissions((rows) => rows.map((r) => (r.id === sub.id ? { ...r, ...updated } : r)));
    if (selected?.id === sub.id) setSelected({ ...selected, ...updated });
  };

  const openCard = async (sub: Submission) => {
    const fresh = await api.get<Submission>(`/submissions/${sub.id}`);
    setSelected(fresh);
  };

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
        if (ev.type === "new_submission") {
          const fresh = ev.data as Submission;
          if (activeForm && fresh.form_template_id === activeForm.id) {
            if (statusFilter === "all" || statusFilter === fresh.status) {
              setSubmissions((prev) => {
                if (prev.some((p) => p.id === fresh.id)) return prev;
                return [fresh, ...prev];
              });
            }
          }
          const who = fresh.submitter
            ? `${fresh.submitter.last_name ?? ""} ${fresh.submitter.first_name ?? ""}`.trim()
            : "";
          notify("Новая заявка", `${fresh.form_name ?? "Заявка"} от ${who}`);
        }
        if (ev.type === "submission_updated") {
          const fresh = ev.data as Submission;
          setSubmissions((rows) => rows.map((r) => (r.id === fresh.id ? { ...r, ...fresh } : r)));
        }
        if (ev.type === "forms_changed") {
          void api.get<FormTemplate[]>("/forms").then(setForms);
          if (activeForm) {
            void loadForm(activeForm.id);
          }
        }
      } catch {}
    };
    return () => ws.close();
  }, [activeForm, statusFilter, loadForm]);

  const fieldsForFilter = activeForm?.fields ?? [];
  const tableFields: FormField[] = useMemo(
    () => (activeForm?.fields ?? []).filter((f) => f.is_active).slice(0, 4),
    [activeForm],
  );

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">Заявки</h1>
          <p className="page-sub">Заполненные формы студентов</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "260px 1fr", gap: 16 }}>
        <div className="card">
          <div className="card-head">
            <h3 className="card-title">Шаблоны форм</h3>
          </div>
          <div style={{ padding: 8 }}>
            {forms.map((f) => (
              <div
                key={f.id}
                onClick={() => loadForm(f.id)}
                className={activeForm?.id === f.id ? "selected" : ""}
                style={{
                  padding: "10px 12px",
                  borderRadius: 8,
                  cursor: "pointer",
                  background: activeForm?.id === f.id ? "var(--brand-50)" : undefined,
                  color: activeForm?.id === f.id ? "var(--brand-900)" : "var(--ink-700)",
                  fontWeight: activeForm?.id === f.id ? 600 : 500,
                  fontSize: 13,
                }}
              >
                {f.name}
                {!f.is_active && (
                  <span className="tag neutral" style={{ marginLeft: 8 }}>
                    скрыта
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-body" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <div className="pill-tabs">
                <button
                  className={statusFilter === "all" ? "active" : ""}
                  onClick={() => setStatusFilter("all")}
                >
                  Все
                </button>
                {STATUSES.map((s) => (
                  <button
                    key={s}
                    className={statusFilter === s ? "active" : ""}
                    onClick={() => setStatusFilter(s)}
                  >
                    {statusLabel(s)}
                  </button>
                ))}
              </div>

              {fieldsForFilter
                .filter((f) => f.type === "string")
                .slice(0, 4)
                .map((f) => (
                  <input
                    key={f.id}
                    className="input"
                    style={{ maxWidth: 200 }}
                    placeholder={`${f.label}…`}
                    value={fieldFilters[`f_${f.id}`] ?? ""}
                    onChange={(e) =>
                      setFieldFilters((prev) => ({ ...prev, [`f_${f.id}`]: e.target.value }))
                    }
                  />
                ))}
            </div>
          </div>

          <div className="card">
            <div style={{ overflowX: "auto" }}>
              <table className="tbl">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>ФИО</th>
                    <th>Дата рождения</th>
                    <th>Группа</th>
                    {tableFields.map((f) => (
                      <th key={f.id}>{f.label}</th>
                    ))}
                    <th>Статус</th>
                    <th>Создана</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map((s) => (
                    <tr key={s.id}>
                      <td className="mono" onClick={() => openCard(s)} style={{ cursor: "pointer" }}>
                        {s.id}
                      </td>
                      <td
                        onClick={() => {
                          if (s.submitter) setOpenUserId(s.submitter.id);
                        }}
                        style={{ cursor: s.submitter ? "pointer" : "default" }}
                      >
                        <SubmitterCell sub={s} />
                      </td>
                      <td>{formatBirthDate(s.submitter?.birth_date)}</td>
                      <td>{s.submitter?.study_group ?? <span className="muted">—</span>}</td>
                      {tableFields.map((f) => (
                        <td key={f.id}>{renderValue(s.values?.[String(f.id)])}</td>
                      ))}
                      <td>
                        <StatusTag status={s.status} />
                      </td>
                      <td className="num">{formatDateTime(s.created_at)}</td>
                      <td>
                        <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                          {NEXT_STATUSES[s.status].map((next) => (
                            <button
                              key={next}
                              className={`btn btn-sm ${next === "rejected" ? "btn-danger" : "btn-secondary"}`}
                              onClick={() => changeStatus(s, next)}
                            >
                              {statusLabel(next)}
                            </button>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {!loading && submissions.length === 0 && (
                    <tr>
                      <td colSpan={7 + tableFields.length} style={{ textAlign: "center", padding: 32, color: "var(--ink-400)" }}>
                        Заявок нет
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {selected && (
        <SubmissionDrawer
          submission={selected}
          form={activeForm}
          onClose={() => setSelected(null)}
          onOpenUser={(id) => {
            setSelected(null);
            setOpenUserId(id);
          }}
        />
      )}

      {openUserId != null && (
        <UserCardPanel
          userId={openUserId}
          currentAdminId={currentAdminId}
          onClose={() => setOpenUserId(null)}
        />
      )}
    </div>
  );
}

function SubmitterCell({ sub }: { sub: Submission }) {
  const s = sub.submitter;
  const name = submitterFullName(s);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <Avatar size="sm" name={name} />
      <div>
        <div style={{ fontWeight: 600 }}>{name}</div>
        {s?.username && <div style={{ fontSize: 11.5, color: "var(--ink-400)" }}>@{s.username}</div>}
      </div>
    </div>
  );
}

function renderValue(v: unknown): React.ReactNode {
  if (v === null || v === undefined || v === "") return <span className="muted">—</span>;
  if (typeof v === "boolean") return v ? "Да" : "Нет";
  return String(v);
}

function SubmissionDrawer({
  submission,
  form,
  onClose,
  onOpenUser,
}: {
  submission: Submission;
  form: FormTemplateDetailed | null;
  onClose: () => void;
  onOpenUser: (id: number) => void;
}) {
  // Snapshot названий полей из самой заявки имеет приоритет над текущей формой —
  // даже если форма потом отредактирована, в карточке видны те названия, что были на момент подачи.
  const labelFor = useMemo(() => {
    const snapshot = submission.field_labels ?? {};
    const byCurrentForm = Object.fromEntries((form?.fields ?? []).map((f) => [String(f.id), f.label]));
    return (fid: string): string => snapshot[fid] ?? byCurrentForm[fid] ?? `Поле ${fid}`;
  }, [submission.field_labels, form]);

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 50,
        display: "flex",
        justifyContent: "flex-end",
      }}
    >
      <div
        onClick={onClose}
        style={{ position: "absolute", inset: 0, background: "rgba(11,23,41,.32)" }}
      />
      <div
        style={{
          position: "relative",
          width: 520,
          maxWidth: "100vw",
          height: "100%",
          background: "#fff",
          borderLeft: "1px solid var(--line)",
          boxShadow: "var(--shadow-lg)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            padding: "18px 22px",
            borderBottom: "1px solid var(--line)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>Заявка #{submission.id}</div>
            <div style={{ fontSize: 12.5, color: "var(--ink-400)" }}>{submission.form_name ?? ""}</div>
          </div>
          <button className="btn btn-ghost btn-icon" onClick={onClose}>
            ×
          </button>
        </div>
        <div style={{ padding: "16px 22px", overflow: "auto" }}>
          {submission.submitter && (
            <div
              style={{
                marginBottom: 16,
                padding: 10,
                border: "1px solid var(--line)",
                borderRadius: 10,
                cursor: "pointer",
              }}
              onClick={() => onOpenUser(submission.submitter!.id)}
              title="Открыть карточку пользователя"
            >
              <div style={{ fontSize: 11.5, color: "var(--ink-400)", textTransform: "uppercase", letterSpacing: ".06em" }}>
                Заявитель
              </div>
              <div style={{ fontWeight: 600, fontSize: 14, marginTop: 4 }}>
                {submitterFullName(submission.submitter)}
              </div>
              <div style={{ fontSize: 12, color: "var(--ink-500)", marginTop: 2 }}>
                {formatBirthDate(submission.submitter.birth_date)} ·{" "}
                {submission.submitter.study_group ?? "—"}
              </div>
            </div>
          )}

          <div style={{ marginBottom: 16 }}>
            <StatusTag status={submission.status} />
            <div style={{ fontSize: 12.5, color: "var(--ink-400)", marginTop: 8 }}>
              Создана: {formatDateTime(submission.created_at)}
            </div>
          </div>

          <h4 style={{ fontSize: 12, color: "var(--ink-500)", textTransform: "uppercase", letterSpacing: ".06em" }}>
            Данные формы
          </h4>
          <div style={{ display: "grid", gap: 8, marginTop: 8 }}>
            {Object.entries(submission.values).map(([fid, val]) => (
              <div key={fid} style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <span style={{ color: "var(--ink-500)", fontSize: 13 }}>{labelFor(fid)}</span>
                <span style={{ fontWeight: 600, fontSize: 13, textAlign: "right" }}>{renderValue(val)}</span>
              </div>
            ))}
          </div>

          <h4
            style={{
              fontSize: 12,
              color: "var(--ink-500)",
              textTransform: "uppercase",
              letterSpacing: ".06em",
              marginTop: 22,
            }}
          >
            История статусов
          </h4>
          <div style={{ marginTop: 8 }}>
            {(submission.history ?? []).map((h: StatusHistoryItem) => (
              <div
                key={h.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "8px 0",
                  borderBottom: "1px solid var(--line)",
                  fontSize: 13,
                }}
              >
                <div>
                  {h.from_status ? `${statusLabel(h.from_status)} → ` : ""}
                  <b>{statusLabel(h.to_status)}</b>
                  {h.comment && <div style={{ color: "var(--ink-400)", fontSize: 12 }}>{h.comment}</div>}
                </div>
                <span style={{ color: "var(--ink-400)" }}>{formatDateTime(h.changed_at)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
