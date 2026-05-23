import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "@/api/client";
import type { FormField, FormTemplateDetailed, Profile } from "@/api/types";
import { useAuth } from "@/auth/AuthProvider";
import { enableClosingConfirmation } from "@/max/bridge";
import { useI18n } from "@/i18n";

function initialValueForField(field: FormField, profile: Profile | null): unknown {
  if (field.profile_key && profile) {
    const v = (profile as unknown as Record<string, unknown>)[field.profile_key];
    if (v !== null && v !== undefined && v !== "") return v;
  }
  if (field.default_value !== null) {
    if (field.type === "checkbox") {
      return field.default_value === "true";
    }
    if (field.type === "number") {
      const n = Number(field.default_value);
      return Number.isFinite(n) ? n : "";
    }
    return field.default_value;
  }
  return field.type === "checkbox" ? false : "";
}

function validateField(field: FormField, value: unknown, t: any): string | null {

  const empty = value === null || value === undefined || value === "";
  if (field.is_required && empty) return t("submit:error:field_required", { field: field.label });
  if (empty) return null;
  if (field.type === "string" && field.regexp) {
    try {
      const re = new RegExp(`^${field.regexp}$`);
      if (!re.test(String(value))) return t("submit:error:field_format", { field: field.label });
    } catch {
      // невалидный regexp — пропускаем на клиенте, сервер проверит
    }
  }
  if (field.type === "number") {
    const n = Number(value);
    if (!Number.isFinite(n)) return t("submit:error:field_number", { field: field.label });
    if (field.min_value && n < Number(field.min_value)) return t("submit:error:field_min", { field: field.label, min: field.min_value });
    if (field.max_value && n > Number(field.max_value)) return t("submit:error:field_max", { field: field.label, max: field.max_value });
  }
  if (field.type === "date") {
    const s = String(value);
    if (field.min_value && s < field.min_value) return t("submit:error:field_date_min", { field: field.label, min: field.min_value });
    if (field.max_value && s > field.max_value) return t("submit:error:field_date_max", { field: field.label, max: field.max_value });
  }
  return null;
}

function profileMissingFields(p: Profile | null, t: any): string[] {

  if (!p) return [t("word:profile")];
  const out: string[] = [];
  if (!p.last_name?.trim()) out.push(t("services:form:last_name"));
  if (!p.first_name?.trim()) out.push(t("services:form:first_name"));
  if (!p.patronymic?.trim()) out.push(t("services:form:patronymic"));
  if (!p.birth_date) out.push(t("services:form:birth_date"));
  if (!p.study_group?.trim()) out.push(t("services:form:study_group"));
  return out;
}

export function SubmitPage() {
  const { t } = useI18n();
  const { formId } = useParams();
  const navigate = useNavigate();
  const { profile } = useAuth();
  const [tpl, setTpl] = useState<FormTemplateDetailed | null>(null);
  const [values, setValues] = useState<Record<string, unknown>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const missing = profileMissingFields(profile, t);
  const banForms = profile?.ban_forms ?? false;

  useEffect(() => {
    void api
      .get<FormTemplateDetailed>(`/forms/${formId}`)
      .then((t) => {
        setTpl(t);
        const v: Record<string, unknown> = {};
        for (const f of t.fields) v[String(f.id)] = initialValueForField(f, profile);
        setValues(v);
      })
      .catch((e) => setError((e as Error)?.message ?? t("submit:error:loading_form")));
    enableClosingConfirmation();
  }, [formId, profile]);

  const idempotencyKey = useMemo(() => `${formId}:${Date.now()}:${Math.random()}`, [formId]);

  const onSubmit = async () => {
    if (!tpl) return;
    setError(null);
    if (banForms) {
      setError(profile?.ban_forms_reason || t("submit:error:form_ban"));
      return;
    }
    if (missing.length) {
      setError(t("submit:error:profile_empty") + ": " + missing.join(", "));
      return;
    }
    for (const f of tpl.fields.filter((f) => f.is_active)) {
      const err = validateField(f, values[String(f.id)], t);
      if (err) {
        setError(err);
        return;
      }
    }
    setBusy(true);
    try {
      await api.post(`/submissions`, {
        form_template_id: tpl.id,
        values,
        idempotency_key: idempotencyKey,
      });
      navigate("/submissions", { replace: true });
    } catch (e) {
      console.log(e)
      const error = e as Error
      const errorMessage = `${t("submit:error:form_ban")} ${t("word:reason")}: ${error.message || t("submit:error:generic")}`;
      setError(errorMessage);
    } finally {
      setBusy(false);
    }
  };

  if (!tpl) {
    return (
      <div className="screen">
        <h1 className="screen-title">{t("services:form:title")}</h1>
        {error ? <div style={{ color: "var(--st-rej-fg)" }}>{error}</div> : <div className="skeleton" style={{ width: "60%" }} />}
      </div>
    );
  }

  return (
    <div className="screen">
      <h1 className="screen-title">{tpl.name}</h1>
      {tpl.description && <p className="screen-sub">{tpl.description}</p>}

      {(missing.length > 0 || banForms) && (
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
          {banForms
            ? profile?.ban_forms_reason || t("services:main:ban_forms")
            : `${t("services:form:profile_incomplete")}: ${missing.join(", ")}.`}{" "}
          {!banForms && (
            <button
              className="btn btn-sm"
              style={{ marginLeft: 6 }}
              onClick={() => navigate("/profile")}
            >
              {t("services:main:to_profile")}
            </button>
          )}
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {tpl.fields
          .filter((f) => f.is_active)
          .map((f) => (
            <FieldInput
              key={f.id}
              field={f}
              value={values[String(f.id)]}
              onChange={(v) => setValues((prev) => ({ ...prev, [String(f.id)]: v }))}
            />
          ))}
      </div>

      {error && (
        <div
          style={{
            margin: "16px 0",
            padding: "10px 12px",
            borderRadius: 10,
            background: "var(--st-rej-bg)",
            color: "var(--st-rej-fg)",
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}

      <div style={{ marginTop: 18 }}>
        <button
          className="btn btn-primary"
          disabled={busy || banForms || missing.length > 0}
          onClick={() => void onSubmit()}
        >
          {busy ? t("submit:button:loading") : t("submit:button:default")}
        </button>
      </div>
    </div>
  );
}

function FieldInput({
  field,
  value,
  onChange,
}: {
  field: FormField;
  value: unknown;
  onChange: (v: unknown) => void;
}) {
  const label = (
    <label className="field-label">
      {field.label}
      {field.is_required && <span style={{ color: "var(--st-rej-fg)" }}> *</span>}
    </label>
  );

  if (field.type === "checkbox") {
    return (
      <label style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}>
        <input
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(e.target.checked)}
        />
        <span style={{ fontSize: 14 }}>{field.label}</span>
      </label>
    );
  }
  if (field.type === "number") {
    return (
      <div>
        {label}
        <input
          className="input"
          type="number"
          inputMode="numeric"
          min={field.min_value ?? undefined}
          max={field.max_value ?? undefined}
          value={String(value ?? "")}
          onChange={(e) => onChange(e.target.value === "" ? "" : Number(e.target.value))}
        />
      </div>
    );
  }
  if (field.type === "date") {
    return (
      <div>
        {label}
        <input
          className="input"
          type="date"
          min={field.min_value ?? undefined}
          max={field.max_value ?? undefined}
          value={String(value ?? "")}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    );
  }
  return (
    <div>
      {label}
      <input
        className="input"
        type="text"
        pattern={field.regexp ?? undefined}
        value={String(value ?? "")}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
