import { useEffect, useState } from "react";
import { api } from "@/api/client";
import type { Profile } from "@/api/types";
import { useAuth } from "@/auth/AuthProvider";
import { requestContact } from "@/max/bridge";
import { useI18n } from "@/i18n";


export function ProfilePage() {
  const { profile, refresh, insideMax } = useAuth();
  const [form, setForm] = useState<Partial<Profile>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const { t } = useI18n();

  useEffect(() => {
    if (profile) setForm(profile);
  }, [profile]);

  if (!profile) return null;

  const save = async () => {
    setBusy(true);
    setMessage(null);
    try {
      await api.put("/profile", {
        first_name: form.first_name,
        last_name: form.last_name,
        patronymic: form.patronymic,
        birth_date: form.birth_date || null,
        study_group: form.study_group,
        email: form.email,
      });
      await refresh();
      setMessage("Сохранено ✓");
    } catch (e) {
      setMessage((e as Error)?.message ?? "Не удалось сохранить");
    } finally {
      setBusy(false);
    }
  };

  const verifyPhone = async () => {
    try {
      const r = await requestContact();
      await api.post("/auth/phone/verify", {
        phone: r.phone,
        authDate: r.authDate,
        hash: r.hash,
        system: profile.system,
      });
      await refresh();
      setMessage("Телефон подтверждён ✓");
    } catch (e) {
      setMessage((e as Error)?.message ?? "Не удалось подтвердить телефон");
    }
  };

  const linkRut = async () => {
    try {
      const r = await api.post<{ status: string; message: string }>("/profile/rut/link", {});
      setMessage(r.message);
    } catch (e) {
      setMessage((e as Error)?.message ?? "Не получилось");
    }
  };

  const requiredFilled = Boolean(
    profile.last_name?.trim() &&
      profile.first_name?.trim() &&
      profile.patronymic?.trim() &&
      profile.birth_date &&
      profile.study_group?.trim(),
  );

  return (
    <div className="screen">
      <h1 className="screen-title">{t("profile:main:title")}</h1>
      <p className="screen-sub">{t("profile:main:subtitle")}</p>

      {!requiredFilled && (
        <div
          style={{
            margin: "0 0 14px",
            padding: "10px 12px",
            borderRadius: 10,
            background: "var(--st-rej-bg)",
            color: "var(--st-rej-fg)",
            fontSize: 13,
            lineHeight: 1.45,
          }}
        >
          {t("profile:main:incomplete")}
        </div>
      )}

      <div className="card">
        <label className="field-label">{t("services:form:last_name")} *</label>
        <input
          className="input"
          value={form.last_name ?? ""}
          onChange={(e) => setForm({ ...form, last_name: e.target.value })}
        />
        <label className="field-label" style={{ marginTop: 10 }}>{t("services:form:first_name")} *</label>
        <input
          className="input"
          value={form.first_name ?? ""}
          onChange={(e) => setForm({ ...form, first_name: e.target.value })}
        />
        <label className="field-label" style={{ marginTop: 10 }}>{t("services:form:patronymic")} *</label>
        <input
          className="input"
          value={form.patronymic ?? ""}
          onChange={(e) => setForm({ ...form, patronymic: e.target.value })}
        />
        <label className="field-label" style={{ marginTop: 10 }}>{t("services:form:birth_date")} *</label>
        <input
          className="input"
          type="date"
          value={form.birth_date ?? ""}
          onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
        />
        <label className="field-label" style={{ marginTop: 10 }}>{t("services:form:study_group")} *</label>
        <input
          className="input"
          value={form.study_group ?? ""}
          onChange={(e) => setForm({ ...form, study_group: e.target.value })}
        />
        <label className="field-label" style={{ marginTop: 10 }}>{t("services:form:email")}</label>
        <input
          className="input"
          type="email"
          value={form.email ?? ""}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <div style={{ marginTop: 14 }}>
          <button className="btn btn-primary" disabled={busy} onClick={() => void save()}>
            {busy ? t("profile:main:saving") : t("profile:main:save")}
          </button>
        </div>
        {message && (
          <div style={{ marginTop: 10, fontSize: 13, color: "var(--ink-500)" }}>{message}</div>
        )}
      </div>

      <div className="card">
        <div className="row">
          <span className="lbl">{t("profile:main:phone")}</span>
          <span className="val">
            {profile.phone ? (
              <>
                {profile.phone}{" "}
                {profile.phone_verified ? (
                  <span style={{ color: "var(--brand)", marginLeft: 4 }}>✓</span>
                ) : (
                  <span style={{ color: "var(--ink-400)", fontSize: 12 }}>({t("profile:main:phone_unverified")})</span>
                )}
              </>
            ) : (
              t("profile:main:phone_unverified")
            )}
          </span>
        </div>
        {!profile.phone_verified && insideMax && (
          <button className="btn btn-secondary" onClick={() => void verifyPhone()}>
            {t("profile:main:verify_phone")}
          </button>
        )}
        {!profile.phone_verified && !insideMax && (
          <div style={{ fontSize: 12, color: "var(--ink-400)", lineHeight: 1.5 }}>
            {t("profile:main:phone_verification_not_available")}
          </div>
        )}
      </div>

      <div className="card">
        <div className="row">
          <span className="lbl">{t("profile:main:personnel_number")}</span>
          <span className="val">
            {profile.rut_personnel_number ?? (
              <em style={{ color: "var(--ink-400)", fontStyle: "italic", fontWeight: 400 }}>в разработке</em>
            )}
          </span>
        </div>
        
      </div>
    </div>
  );
}
