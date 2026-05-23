import { useEffect, useState } from "react";
import { api } from "@/api/client";
import { useI18n } from "@/i18n";

interface SettingOut {
  key: string;
  value: string | null;
}

const KEYS = ["bot_start_message_ru", "bot_start_message_en"] as const;

export function BotSettingsPage() {
  const { t } = useI18n();
  const [values, setValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all(KEYS.map((k) => api.get<SettingOut>(`/settings/${k}`))).then((rows) => {
      const v: Record<string, string> = {};
      for (const r of rows) v[r.key] = r.value ?? "";
      setValues(v);
    });
  }, []);

  const save = async (key: string) => {
    setSaving(key);
    try {
      await api.put(`/settings/${key}`, { value: values[key] || null });
      setSavedAt(new Date().toLocaleTimeString());
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">{t("page.bot_settings.title")}</h1>
          <p className="page-sub">{t("page.bot_settings.sub")}</p>
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
        {KEYS.map((key) => (
          <div key={key} className="card">
            <div className="card-head">
              <h3 className="card-title">
                {key === "bot_start_message_ru" ? "Текст /start (RU)" : "/start message (EN)"}
              </h3>
              <p className="card-sub">{key}</p>
            </div>
            <div className="card-body">
              <textarea
                className="textarea"
                style={{ minHeight: 180, resize: "vertical" }}
                value={values[key] ?? ""}
                onChange={(e) => setValues((prev) => ({ ...prev, [key]: e.target.value }))}
                placeholder={
                  key === "bot_start_message_ru"
                    ? "Привет! Это бот МФЦ…"
                    : "Hello! This is the MFC bot…"
                }
              />
              <div style={{ marginTop: 12, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 12, color: "var(--ink-400)" }}>
                  {savedAt ? `Сохранено в ${savedAt}` : "Изменения применятся к следующему /start"}
                </span>
                <button
                  className="btn btn-primary"
                  disabled={saving === key}
                  onClick={() => void save(key)}
                >
                  {saving === key ? t("common.loading") : t("action.save")}
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
