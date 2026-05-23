import { useEffect, useState } from "react";
import { api } from "@/api/client";
import { useAuth } from "@/auth/AuthProvider";
import { useI18n } from "@/i18n";
import { Icon } from "@/components/Icon";

type Role = "employee" | "admin";

interface AdminRow {
  id: number;
  max_user_id: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

export function AdminsPage() {
  const { admin } = useAuth();
  const { t } = useI18n();
  const [rows, setRows] = useState<AdminRow[]>([]);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({ max_user_id: "", full_name: "", role: "employee" as Role });
  const [error, setError] = useState<string | null>(null);

  const reload = () => {
    void api.get<AdminRow[]>("/admins").then(setRows).catch((e) => setError((e as Error).message));
  };

  useEffect(reload, []);

  const create = async () => {
    setError(null);
    try {
      await api.post<AdminRow>("/admins", form);
      setForm({ max_user_id: "", full_name: "", role: "employee" });
      setAdding(false);
      reload();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const update = async (row: AdminRow, patch: Partial<AdminRow>) => {
    try {
      const upd = await api.patch<AdminRow>(`/admins/${row.id}`, patch);
      setRows((r) => r.map((x) => (x.id === upd.id ? upd : x)));
    } catch (e) {
      alert((e as Error).message);
    }
  };

  const remove = async (row: AdminRow) => {
    if (!window.confirm(`Удалить сотрудника ${row.full_name}?`)) return;
    try {
      await api.del(`/admins/${row.id}`);
      setRows((r) => r.filter((x) => x.id !== row.id));
    } catch (e) {
      alert((e as Error).message);
    }
  };

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">{t("page.admins.title")}</h1>
          <p className="page-sub">{t("page.admins.sub")}</p>
        </div>
        {!adding && (
          <button className="btn btn-primary" onClick={() => setAdding(true)}>
            <span className="ico">
              <Icon.Plus />
            </span>
            {t("action.add")}
          </button>
        )}
      </div>

      {adding && (
        <div className="card" style={{ padding: 16, marginBottom: 16 }}>
          <div className="grid" style={{ gridTemplateColumns: "1fr 1fr 200px auto", gap: 10 }}>
            <div>
              <label className="field-label">MAX user_id</label>
              <input
                className="input"
                placeholder="например, 12345678"
                value={form.max_user_id}
                onChange={(e) => setForm({ ...form, max_user_id: e.target.value })}
              />
            </div>
            <div>
              <label className="field-label">ФИО</label>
              <input
                className="input"
                placeholder="Иван Иванов"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </div>
            <div>
              <label className="field-label">Роль</label>
              <select
                className="select"
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value as Role })}
              >
                <option value="employee">{t("role.employee")}</option>
                <option value="admin">{t("role.admin")}</option>
              </select>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
              <button className="btn btn-primary" onClick={() => void create()}>
                {t("action.save")}
              </button>
              <button className="btn btn-ghost" onClick={() => setAdding(false)}>
                {t("action.cancel")}
              </button>
            </div>
          </div>
          {error && (
            <div style={{ marginTop: 10, color: "var(--st-rej-fg)", fontSize: 13 }}>{error}</div>
          )}
        </div>
      )}

      <div className="card">
        <table className="tbl">
          <thead>
            <tr>
              <th>ФИО</th>
              <th>MAX user_id</th>
              <th>Роль</th>
              <th>Активен</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const isSelf = admin?.id === r.id;
              return (
                <tr key={r.id}>
                  <td>
                    <input
                      className="input"
                      value={r.full_name}
                      onChange={(e) => setRows((rs) => rs.map((x) => (x.id === r.id ? { ...x, full_name: e.target.value } : x)))}
                      onBlur={() => void update(r, { full_name: r.full_name })}
                    />
                  </td>
                  <td className="mono">{r.max_user_id}</td>
                  <td>
                    <select
                      className="select"
                      value={r.role}
                      onChange={(e) => void update(r, { role: e.target.value as Role })}
                      disabled={isSelf}
                    >
                      <option value="employee">{t("role.employee")}</option>
                      <option value="admin">{t("role.admin")}</option>
                    </select>
                  </td>
                  <td>
                    <input
                      type="checkbox"
                      checked={r.is_active}
                      onChange={(e) => void update(r, { is_active: e.target.checked })}
                      disabled={isSelf}
                    />
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {!isSelf && (
                      <button className="btn btn-danger btn-sm" onClick={() => void remove(r)}>
                        {t("action.delete")}
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
            {rows.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: "center", color: "var(--ink-400)", padding: 32 }}>
                  {t("common.empty")}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
