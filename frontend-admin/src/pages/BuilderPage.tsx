import { useCallback, useEffect, useState } from "react";
import { api } from "@/api/client";
import type {
  FieldType,
  FormField,
  FormTemplate,
  FormTemplateDetailed,
} from "@/api/types";
import { Icon } from "@/components/Icon";

const FIELD_TYPES: { value: FieldType; label: string }[] = [
  { value: "string", label: "Строка" },
  { value: "number", label: "Число" },
  { value: "date", label: "Дата" },
  { value: "checkbox", label: "Чекбокс" },
];

export function BuilderPage() {
  const [forms, setForms] = useState<FormTemplate[]>([]);
  const [active, setActive] = useState<FormTemplateDetailed | null>(null);

  const reload = useCallback(async () => {
    const list = await api.get<FormTemplate[]>("/forms");
    setForms(list);
    if (list.length && !active) {
      const f = await api.get<FormTemplateDetailed>(`/forms/${list[0].id}`);
      setActive(f);
    }
  }, [active]);

  useEffect(() => {
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const select = async (id: number) => {
    const f = await api.get<FormTemplateDetailed>(`/forms/${id}`);
    setActive(f);
  };

  const createForm = async () => {
    const name = window.prompt("Название новой формы");
    if (!name) return;
    const tpl = await api.post<FormTemplate>("/forms", { name, is_active: false, order: forms.length });
    await reload();
    void select(tpl.id);
  };

  const patchForm = async (patch: Partial<FormTemplate>) => {
    if (!active) return;
    const updated = await api.patch<FormTemplate>(`/forms/${active.id}`, patch);
    setActive({ ...active, ...updated });
    setForms((rows) => rows.map((r) => (r.id === updated.id ? updated : r)));
  };

  const deleteForm = async () => {
    if (!active) return;
    if (!window.confirm(`Удалить форму «${active.name}»? Все связанные заявки сохранятся.`)) return;
    await api.del(`/forms/${active.id}`);
    setActive(null);
    await reload();
  };

  const addField = async () => {
    if (!active) return;
    const label = window.prompt("Название поля") ?? "";
    if (!label) return;
    const f = await api.post<FormField>(`/forms/${active.id}/fields`, {
      label,
      type: "string",
      order: active.fields.length,
      is_required: false,
    });
    setActive({ ...active, fields: [...active.fields, f] });
  };

  const patchField = async (field: FormField, patch: Partial<FormField>) => {
    if (!active) return;
    const updated = await api.patch<FormField>(`/forms/${active.id}/fields/${field.id}`, patch);
    setActive({
      ...active,
      fields: active.fields.map((f) => (f.id === updated.id ? updated : f)),
    });
  };

  const deleteField = async (field: FormField) => {
    if (!active) return;
    if (!window.confirm(`Удалить поле «${field.label}»?`)) return;
    await api.del(`/forms/${active.id}/fields/${field.id}`);
    setActive({ ...active, fields: active.fields.filter((f) => f.id !== field.id) });
  };

  const [replyText, setReplyText] = useState(active?.reply_on_accept ?? "");

useEffect(() => {
  setReplyText(active?.reply_on_accept ?? "");
}, [active?.id]);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">Конструктор форм</h1>
          <p className="page-sub">Создание и настройка шаблонов справок</p>
        </div>
        <button className="btn btn-primary" onClick={createForm}>
          <span className="ico">
            <Icon.Plus />
          </span>
          Новая форма
        </button>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "300px 1fr" }}>
        <div className="card">
          <div className="card-head">
            <h3 className="card-title">Формы</h3>
          </div>
          <div style={{ padding: 8 }}>
            {forms.map((f) => (
              <div
                key={f.id}
                onClick={() => select(f.id)}
                style={{
                  padding: "10px 12px",
                  borderRadius: 8,
                  cursor: "pointer",
                  background: active?.id === f.id ? "var(--brand-50)" : undefined,
                  color: active?.id === f.id ? "var(--brand-900)" : "var(--ink-700)",
                  fontWeight: active?.id === f.id ? 600 : 500,
                  fontSize: 13,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <span>{f.name}</span>
                {!f.is_active && <span className="tag neutral">скрыта</span>}
              </div>
            ))}
          </div>
        </div>

        {!active ? (
          <div className="card">
            <div className="card-body" style={{ textAlign: "center", color: "var(--ink-400)", padding: 64 }}>
              Выберите форму слева или создайте новую
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="card-head">
              <div>
                <h3 className="card-title">{active.name}</h3>
                <p className="card-sub">{active.description || "Описание отсутствует"}</p>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-secondary" onClick={() => {
                  const newName = window.prompt("Название формы", active.name);
                  if (newName) void patchForm({ name: newName });
                }}>
                  Переименовать
                </button>
                <label
                  className="btn btn-secondary"
                  style={{ display: "inline-flex", alignItems: "center", gap: 8, cursor: "pointer" }}
                >
                  <input
                    type="checkbox"
                    checked={active.is_active}
                    onChange={(e) => void patchForm({ is_active: e.target.checked })}
                  />
                  Доступна студентам
                </label>
                <button className="btn btn-danger" onClick={deleteForm}>
                  Удалить
                </button>
              </div>
            </div>
            <div className="card-body">
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                <h4 style={{ margin: 0, fontSize: 13, color: "var(--ink-500)", textTransform: "uppercase", letterSpacing: ".06em" }}>
                  Поля ({active.fields.length})
                </h4>
                <button className="btn btn-primary btn-sm" onClick={addField}>
                  <span className="ico">
                    <Icon.Plus />
                  </span>
                  Добавить поле
                </button>
              </div>

              {active.fields.length === 0 && (
                <div style={{ textAlign: "center", color: "var(--ink-400)", padding: 32 }}>
                  Пока нет полей. Добавьте первое — оно станет частью формы для студентов.
                </div>
              )}

              <div style={{ display: "grid", gap: 10 }}>
                {active.fields.map((f) => (
                  <FieldRow
                    key={f.id}
                    field={f}
                    onChange={(p) => patchField(f, p)}
                    onDelete={() => deleteField(f)}
                  />
                ))}
              </div>
              <div style={{ marginTop: 24 }}>
  <h4 style={{ margin: "0 0 8px", fontSize: 13, color: "var(--ink-500)", textTransform: "uppercase", letterSpacing: ".06em" }}>
    Ответ при принятии заявки
  </h4>
  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
    <div>
      <label className="field-label">Текст (поддерживается HTML)</label>
      <textarea
  className="textarea"
  rows={6}
  value={replyText}
  onChange={(e) => setReplyText(e.target.value)}
  style={{ fontFamily: "var(--mono)", fontSize: 12, resize: "vertical" }}
/>

<button
  className="btn btn-primary btn-sm"
  style={{ marginTop: 8 }}
  onClick={() => void patchForm({ reply_on_accept: replyText || null })}
>
  Сохранить
</button>
    </div>
    <div>
      <label className="field-label">Предпросмотр</label>
      <div
        className="draft-preview"
        style={{
          border: "1px solid var(--line-strong)",
          borderRadius: 8,
          padding: "9px 12px",
          minHeight: 120,
          fontSize: 13,
          lineHeight: 1.5,
          background: "#fff",
          color: "var(--ink-900)",
          whiteSpace: "pre-wrap"
        }}
        dangerouslySetInnerHTML={{ __html: replyText ?? "<span style='color:var(--ink-300)'>Предпросмотр появится здесь…</span>" }}
      />
    </div>
  </div>
</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function FieldRow({
  field,
  onChange,
  onDelete,
}: {
  field: FormField;
  onChange: (patch: Partial<FormField>) => void;
  onDelete: () => void;
}) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "2fr 1fr 1fr 1fr auto auto auto",
        gap: 10,
        alignItems: "center",
        padding: "10px 12px",
        border: "1px solid var(--line)",
        borderRadius: 10,
        background: field.is_active ? "#fff" : "var(--ink-50)",
      }}
    >
      <input
        className="input"
        value={field.label}
        onChange={(e) => onChange({ label: e.target.value })}
      />
      <select
        className="select"
        value={field.type}
        onChange={(e) => onChange({ type: e.target.value as FieldType })}
      >
        {FIELD_TYPES.map((t) => (
          <option key={t.value} value={t.value}>
            {t.label}
          </option>
        ))}
      </select>
      <input
        className="input"
        placeholder={field.type === "string" ? "regexp…" : field.type === "checkbox" ? "" : "min"}
        value={field.type === "string" ? field.regexp ?? "" : field.min_value ?? ""}
        onChange={(e) => {
          if (field.type === "string") onChange({ regexp: e.target.value || null });
          else onChange({ min_value: e.target.value || null });
        }}
        disabled={field.type === "checkbox"}
      />
      <input
        className="input"
        placeholder={field.type === "checkbox" ? "" : "max / default"}
        value={field.type === "string" || field.type === "checkbox" ? field.default_value ?? "" : field.max_value ?? ""}
        onChange={(e) => {
          if (field.type === "string" || field.type === "checkbox") onChange({ default_value: e.target.value || null });
          else onChange({ max_value: e.target.value || null });
        }}
      />
      <label style={{ display: "inline-flex", gap: 6, fontSize: 12, alignItems: "center" }}>
        <input
          type="checkbox"
          checked={field.is_required}
          onChange={(e) => onChange({ is_required: e.target.checked })}
        />
        обязат.
      </label>
      <label style={{ display: "inline-flex", gap: 6, fontSize: 12, alignItems: "center" }}>
        <input
          type="checkbox"
          checked={field.is_active}
          onChange={(e) => onChange({ is_active: e.target.checked })}
        />
        активно
      </label>
      <button className="btn btn-ghost btn-icon" onClick={onDelete} title="Удалить поле">
        <span className="ico">
          <Icon.Trash />
        </span>
      </button>
    </div>
  );
}
