import { NavLink, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { Icon } from "@/components/Icon";
import { Avatar } from "@/components/Avatar";
import { useAuth } from "@/auth/AuthProvider";
import { api } from "@/api/client";
import type { TicketsOverview } from "@/api/types";
import { useI18n } from "@/i18n";

export function Layout({ children }: { children: React.ReactNode }) {
  const { admin, logout } = useAuth();
  const navigate = useNavigate();
  const [ticketsCount, setTicketsCount] = useState(0);
  const { t, lang, setLang } = useI18n();

  useEffect(() => {
    if (!admin) return;
    let timer: ReturnType<typeof setInterval> | null = null;
    const load = () => {
      api
        .get<TicketsOverview>("/tickets/overview")
        .then((r) => setTicketsCount(r.open_count))
        .catch(() => setTicketsCount(0));
    };
    load();
    timer = setInterval(load, 20_000);
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [admin]);

  if (!admin) return <>{children}</>;

  const items = [
    { to: "/dashboard", label: t("nav.dashboard"), icon: <Icon.Dashboard /> },
    { to: "/submissions", label: t("nav.submissions"), icon: <Icon.Forms /> },
    {
      to: "/tickets",
      label: t("nav.tickets"),
      icon: <Icon.Tickets />,
      badge: ticketsCount || undefined,
    },
    { to: "/users", label: t("nav.users"), icon: <Icon.Users /> },
    ...(admin.role === "admin"
      ? [
          { to: "/builder", label: t("nav.builder"), icon: <Icon.Builder /> },
          { to: "/faq", label: t("nav.faq"), icon: <Icon.Forms /> },
          { to: "/kb", label: t("nav.kb"), icon: <Icon.Forms /> },
          { to: "/admins", label: t("nav.admins"), icon: <Icon.Users /> },
          { to: "/bot-settings", label: t("nav.bot_settings"), icon: <Icon.Settings /> },
        ]
      : []),
  ];

  const onLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app">
      <nav className="navbar">
        <div className="brand">
          <div>
            <div className="name">
               <img src="logo-miit-white.png" alt="" style={{ maxHeight: "50px", objectFit: "contain" }} />
            </div>
          </div>
        </div>

        <div className="navlinks">
          {items.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              className={({ isActive }) => `navlink ${isActive ? "active" : ""}`}
            >
              <span className="ico" style={{ width: 16, height: 16 }}>
                {n.icon}
              </span>
              <span>{n.label}</span>
              {n.badge ? <span className="badge">{n.badge}</span> : null}
            </NavLink>
          ))}
        </div>

        <div className="nav-right">
          <button
            className="icon-btn"
            title={lang === "ru" ? "Switch to English" : "Переключить на русский"}
            onClick={() => setLang(lang === "ru" ? "en" : "ru")}
            style={{ fontSize: 12, fontWeight: 700, width: "auto", padding: "0 10px" }}
          >
            {lang.toUpperCase()}
          </button>
          <button className="icon-btn" title={t("action.logout")} onClick={onLogout}>
            <span className="ico">
              <Icon.Logout />
            </span>
          </button>
          <div className="me">
            <Avatar name={admin.full_name} />
            <div className="who">
              <b>{shortName(admin.full_name)}</b>
              <span>{admin.role === "admin" ? t("role.admin") : t("role.employee")}</span>
            </div>
          </div>
        </div>
      </nav>
      <main>{children}</main>
    </div>
  );
}

function shortName(full: string): string {
  const parts = full.split(" ");
  if (parts.length < 2) return full;
  return `${parts[0][0]}. ${parts[1]}`;
}
