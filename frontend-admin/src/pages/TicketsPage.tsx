import { useCallback, useEffect, useRef, useState } from "react";
import { api, getCurrentAdminId, getToken } from "@/api/client";
import type { ConversationItem, MessageItem } from "@/api/types";
import { Avatar } from "@/components/Avatar";
import { Icon } from "@/components/Icon";
import { formatDateTime } from "@/lib/status";
import { type UploadedFile, formatBytes, isImageMime, uploadFile } from "@/api/files";
import {
  disableNotify,
  isNotifyEnabled,
  isNotifySupported,
  notify,
  requestNotifyPermission,
} from "@/lib/notify";
import { useI18n } from "@/i18n";

export function TicketsPage() {
  const [convs, setConvs] = useState<ConversationItem[]>([]);
  const [onlyOpen, setOnlyOpen] = useState(false);
  const [activeUser, setActiveUser] = useState<ConversationItem | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [pending, setPending] = useState<UploadedFile[]>([]);
  const [uploading, setUploading] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const messagesRef = useRef<HTMLDivElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [notifyOn, setNotifyOn] = useState<boolean>(() => isNotifyEnabled());
  const { t } = useI18n();
  const currentAdminId = getCurrentAdminId();

  const reloadConvs = useCallback(() => {
    api
      .get<ConversationItem[]>(`/tickets/conversations?only_open=${onlyOpen}`)
      .then(setConvs)
      .catch(() => setConvs([]));
  }, [onlyOpen]);

  useEffect(() => {
    reloadConvs();
  }, [reloadConvs]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;
    const url = new URL(`${import.meta.env.VITE_API_URL}/api/ws/chat`, window.location.origin);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.searchParams.set("token", token);
    if (activeUser) url.searchParams.set("user_pk", String(activeUser.user_id));
    const ws = new WebSocket(url.toString());
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data);
        if (ev.type === "message" && activeUser && ev.data.user_id === activeUser.user_id) {
         
          const isMyOutgoing =
            ev.data.direction === "out" &&
            currentAdminId !== null &&
            ev.data.replied_by_admin_id === currentAdminId;
          if (!isMyOutgoing) {
            setMessages((prev) => {
              if (prev.some((m) => m.id === ev.data.id)) return prev;
              return [...prev, ev.data];
            });
          }
        }
        if (ev.type === "new_ticket") {
          reloadConvs();
          const text = ev?.data?.text ?? "";
          notify(t("push.title"), text);
        }
        if (ev.type === "ticket_answered") {
          reloadConvs();
        }
      } catch {}
    };
    return () => ws.close();
  }, [activeUser, reloadConvs, currentAdminId, t]);

  useEffect(() => {
    if (!activeUser) {
      setMessages([]);
      return;
    }
    api
      .get<MessageItem[]>(`/messages?user_id=${activeUser.user_id}`)
      .then(setMessages)
      .catch(() => setMessages([]));
  }, [activeUser]);

  useEffect(() => {
    setTimeout(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, 0);
  }, [messages]);

  const send = async () => {
    if (!activeUser) return;
    const trimmed = text.trim();
    if (!trimmed && pending.length === 0) return;
    setSending(true);
    try {
      const msg = await api.post<MessageItem>(`/messages/to-user/${activeUser.user_id}`, {
        text: trimmed || null,
        attachment_ids: pending.map((p) => p.id),
      });
      setMessages((prev) => [...prev, msg]);
      setText("");
      setPending([]);
      reloadConvs();
    } finally {
      setSending(false);
    }
  };

  const onPickFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    setUploading(true);
    try {
      const uploaded = await uploadFile(f);
      setPending((prev) => [...prev, uploaded]);
    } catch (err) {
      alert((err as Error).message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">{t("page.tickets.title")}</h1>
          <p className="page-sub">{t("page.tickets.sub")}</p>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          {isNotifySupported() && (
            <button
              className={`btn btn-sm ${notifyOn ? "btn-secondary" : "btn-primary"}`}
              onClick={async () => {
                if (notifyOn) {
                  disableNotify();
                  setNotifyOn(false);
                } else {
                  const ok = await requestNotifyPermission();
                  setNotifyOn(ok);
                }
              }}
            >
              <span className="ico" style={{ width: 14, height: 14 }}>
                <Icon.Bell />
              </span>
              {notifyOn ? t("push.disable") : t("push.enable")}
            </button>
          )}
          <div className="pill-tabs">
            <button className={onlyOpen ? "active" : ""} onClick={() => setOnlyOpen(true)}>
              Без ответа
            </button>
            <button className={!onlyOpen ? "active" : ""} onClick={() => setOnlyOpen(false)}>
              Все
            </button>
          </div>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "320px 1fr", height: "calc(100vh - 200px)" }}>
        <div className="card" style={{ overflow: "auto" }}>
          {convs.map((c) => {
            const name = `${c.last_name ?? ""} ${c.first_name ?? ""}`.trim() || c.username || "—";
            const active = activeUser?.user_id === c.user_id;
            return (
              <div
                key={c.user_id}
                onClick={() => setActiveUser(c)}
                style={{
                  display: "flex",
                  gap: 10,
                  padding: "12px 16px",
                  borderBottom: "1px solid var(--line)",
                  cursor: "pointer",
                  background: active ? "var(--brand-50)" : undefined,
                }}
              >
                <Avatar name={name} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{name}</div>
                    {c.has_open_ticket && (
                      <span
                        style={{
                          background: "var(--st-rej-bg)",
                          color: "var(--st-rej-fg)",
                          fontSize: 10.5,
                          padding: "2px 6px",
                          borderRadius: 10,
                          fontWeight: 700,
                        }}
                      >
                        НОВ
                      </span>
                    )}
                  </div>
                  <div
                    style={{
                      fontSize: 12,
                      color: "var(--ink-400)",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {c.last_message_text || "—"}
                  </div>
                  <div style={{ fontSize: 10.5, color: "var(--ink-300)", marginTop: 2 }}>
                    {c.last_message_at ? formatDateTime(c.last_message_at) : ""}
                  </div>
                </div>
              </div>
            );
          })}
          {convs.length === 0 && (
            <div style={{ padding: 32, textAlign: "center", color: "var(--ink-400)" }}>Нет обращений</div>
          )}
        </div>

        <div className="card" style={{ display: "flex", flexDirection: "column" }}>
          {!activeUser ? (
            <div style={{ flex: 1, display: "grid", placeItems: "center", color: "var(--ink-400)" }}>
              Выберите обращение слева
            </div>
          ) : (
            <>
              <div
                ref={messagesRef}
                style={{ flex: 1, overflow: "auto", padding: 20, display: "flex", flexDirection: "column", gap: 10 }}
              >
                {messages.map((m) => (
                  <ChatBubble key={m.id} msg={m} currentAdminId={currentAdminId} />
                ))}
                <div ref={bottomRef} />
              </div>
              <div
                style={{
                  padding: 16,
                  borderTop: "1px solid var(--line)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                }}
              >
                {pending.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {pending.map((p) => (
                      <span key={p.id} className="tag outline" style={{ paddingRight: 4 }}>
                        {p.name} · {formatBytes(p.size_bytes)}
                        <button
                          onClick={() => setPending((prev) => prev.filter((x) => x.id !== p.id))}
                          style={{
                            background: "transparent",
                            border: 0,
                            cursor: "pointer",
                            marginLeft: 4,
                            color: "var(--ink-400)",
                          }}
                          title="Убрать вложение"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
                <div style={{ display: "flex", gap: 8 }}>
                  <input
                    ref={fileInputRef}
                    type="file"
                    hidden
                    onChange={(e) => void onPickFile(e)}
                  />
                  <button
                    className="btn btn-secondary btn-icon"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    title="Прикрепить файл"
                  >
                    <span className="ico">
                      <Icon.Paperclip />
                    </span>
                  </button>
                  <textarea
                    className="textarea"
                    rows={1}
                    placeholder="Сообщение студенту…"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        void send();
                      }
                    }}
                    style={{ resize: "none" }}
                  />
                  <button
                    className="btn btn-primary"
                    disabled={sending || (!text.trim() && pending.length === 0)}
                    onClick={() => void send()}
                  >
                    Отправить
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function ChatBubble({ msg, currentAdminId }: { msg: MessageItem; currentAdminId: number | null }) {
  const isOut = msg.direction === "out";
  const attachments = msg.attachments ?? [];
  const authorLabel = isOut && msg.replied_by_admin_name
    ? msg.replied_by_admin_id === currentAdminId
      ? `${msg.replied_by_admin_name} (вы)`
      : msg.replied_by_admin_name
    : null;
  return (
    <div
      style={{
        alignSelf: isOut ? "flex-end" : "flex-start",
        maxWidth: "75%",
        background: isOut ? "var(--brand)" : "var(--ink-50)",
        color: isOut ? "#fff" : "var(--ink-900)",
        padding: "10px 14px",
        borderRadius: 12,
        fontSize: 13,
        lineHeight: 1.4,
      }}
    >
      {authorLabel && (
        <div style={{ fontSize: 11.5, fontWeight: 700, marginBottom: 4, opacity: 0.9 }}>
          {authorLabel}
        </div>
      )}
      {msg.text && <div style={{ whiteSpace: "pre-wrap" }}>{msg.text}</div>}

      {attachments.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: msg.text ? 8 : 0 }}>
          {attachments.map((a, i) =>
            isImageMime(a.mime) ? (
              <a key={i} href={a.url.startsWith("http") ? a.url : import.meta.env.VITE_API_URL + a.url} target="_blank" rel="noopener noreferrer">
                <img
                  src={a.url.startsWith("http") ? a.url : import.meta.env.VITE_API_URL + a.url}
                  alt={a.name ?? ""}
                  style={{ maxWidth: 240, maxHeight: 240, borderRadius: 8, display: "block" }}
                />
              </a>
            ) : (
              <a
                key={i}
                href={a.url.startsWith("http") ? a.url : import.meta.env.VITE_API_URL + a.url}
                download={a.name ?? "file"}
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "6px 10px",
                  borderRadius: 8,
                  background: isOut ? "rgba(255,255,255,.15)" : "#fff",
                  color: isOut ? "#fff" : "var(--ink-900)",
                  textDecoration: "none",
                  fontSize: 12.5,
                }}
              >
                <span className="ico" style={{ width: 14, height: 14 }}>
                  <Icon.Download />
                </span>
                <span>{a.name ?? "файл"}</span>
                {a.size ? (
                  <span style={{ opacity: 0.6 }}>· {formatBytes(a.size)}</span>
                ) : null}
              </a>
            ),
          )}
        </div>
      )}

      {msg.is_ai_answered && !isOut && (
        <div style={{ fontSize: 10.5, opacity: 0.6, marginTop: 4 }}>авто-ответ</div>
      )}
      <div style={{ fontSize: 10.5, marginTop: 4, opacity: 0.6 }}>{formatDateTime(msg.created_at)}</div>
    </div>
  );
}
