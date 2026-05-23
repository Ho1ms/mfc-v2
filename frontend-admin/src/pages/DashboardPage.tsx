import { useEffect, useState } from "react";
import {
  Bar,
  Line,
} from "react-chartjs-2";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { api } from "@/api/client";
import type { StatsOverview } from "@/api/types";
import { formatDuration } from "@/lib/status";
import { useI18n } from "@/i18n";

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Filler,
  Tooltip,
  Legend,
);

export function DashboardPage() {
  const { t } = useI18n();
  const [days, setDays] = useState(30);
  const [data, setData] = useState<StatsOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .get<StatsOverview>(`/stats/overview?days=${days}`)
      .then(setData)
      .finally(() => setLoading(false));
  }, [days]);

  return (
    <div className="page">
      <div className="page-head">
        <div>
          <h1 className="page-title">{t("page.dashboard.title")}</h1>
          <p className="page-sub">{t("page.dashboard.sub")}</p>
        </div>
        <div className="pill-tabs">
          {[7, 30, 90].map((d) => (
            <button key={d} className={days === d ? "active" : ""} onClick={() => setDays(d)}>
              {d === 7 ? t("page.dashboard.week") : d === 30 ? t("page.dashboard.month") : t("page.dashboard.quarter")}
            </button>
          ))}
        </div>
      </div>

      <div className="grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <Kpi
          label={t("page.dashboard.total_submissions")}
          value={data?.kpi.total ?? 0}
          loading={loading}
        />
        <Kpi
          label={t("page.dashboard.avg_time_to_work")}
          value={formatDuration(data?.kpi.avg_new_to_work_seconds ?? 0)}
          loading={loading}
        />
        <Kpi
          label={t("page.dashboard.avg_time_to_done")}
          value={formatDuration(data?.kpi.avg_work_to_done_seconds ?? 0)}
          loading={loading}
        />
        <Kpi
          label={t("page.dashboard.rejected_share")}
          value={`${Math.round((data?.kpi.rejected_share ?? 0) * 100)}%`}
          loading={loading}
        />
      </div>

      <div className="grid" style={{ gridTemplateColumns: "repeat(3, 1fr)", marginTop: 16 }}>
        <Kpi
          label={t("page.dashboard.new_users")}
          value={data?.kpi.users_total ?? 0}
          loading={loading}
          sub={t("page.dashboard.of_n_days", { days: days })}
        />
        <Kpi
          label={t("page.dashboard.users_with_submission")}
          value={data?.kpi.users_with_submission ?? 0}
          loading={loading}
          sub={t("page.dashboard.of_n_days", { days: days })}
        />
        <Kpi
          label={t("page.dashboard.conversion_rate")}
          value={`${Math.round((data?.kpi.conversion_rate ?? 0) * 100)}%`}
          loading={loading}
          sub={t("page.dashboard.conversion_rate_sub")}
        />
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1.6fr 1fr", marginTop: 16 }}>
        <div className="card">
          <div className="card-head">
            <h3 className="card-title">{t("page.dashboard.tickets_by_days")}</h3>
            <p className="card-sub">{t("page.dashboard.of_n_days", { days: days })}</p>
          </div>
          <div className="card-body" style={{ height: 320 }}>
            {data && (
              <Line
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
                }}
                data={{
                  labels: data.timeseries.map((p) => p.day ?? ""),
                  datasets: [
                    {
                      data: data.timeseries.map((p) => p.count),
                      borderColor: "#1B365D",
                      backgroundColor: "rgba(27,54,93,.12)",
                      fill: true,
                      tension: 0.3,
                      pointRadius: 3,
                    },
                  ],
                }}
              />
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-head">
            <h3 className="card-title">{t("page.dashboard.tickets_by_type")}</h3>
            <p className="card-sub">{t("page.dashboard.of_n_days", { days: days })}</p>
          </div>
          <div className="card-body" style={{ height: 320 }}>
            {data && (
              <Bar
                options={{
                  indexAxis: "y",
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
                }}
                data={{
                  labels: data.bar.map((b) => b.name),
                  datasets: [
                    {
                      data: data.bar.map((b) => b.count),
                      backgroundColor: "#3E6BAA",
                      borderRadius: 6,
                    },
                  ],
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Kpi({
  label,
  value,
  loading,
  sub,
}: {
  label: string;
  value: number | string;
  loading?: boolean;
  sub?: string;
}) {
  return (
    <div className="card" style={{ padding: 18 }}>
      <div
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: "var(--ink-500)",
          letterSpacing: ".04em",
          textTransform: "uppercase",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 28,
          fontWeight: 700,
          letterSpacing: "-.02em",
          color: "var(--ink-900)",
          lineHeight: 1.1,
          marginTop: 6,
        }}
      >
        {loading ? "…" : value}
      </div>
      {sub && (
        <div style={{ fontSize: 11.5, color: "var(--ink-400)", marginTop: 4 }}>{sub}</div>
      )}
    </div>
  );
}
