import { NavLink } from "react-router-dom";
import { Icon } from "@/components/Icon";
import { useI18n } from "@/i18n";

export function BottomNav() {
  const { t } = useI18n();

  const items = [
    { to: "/", label: t("home:main:home"), icon: <Icon.Home /> },
    { to: "/services", label: t("home:main:services"), icon: <Icon.Plus /> },
    { to: "/submissions", label: t("home:main:my_submissions"), icon: <Icon.History /> },
    { to: "/faq", label: t("home:main:faq"), icon: <Icon.FAQ /> },
    { to: "/profile", label: t("home:main:profile"), icon: <Icon.Profile /> },
  ];

  return (
    <nav className="bottom-nav">
      {items.map((it) => (
        <NavLink key={it.to} to={it.to} end={it.to === "/"}>
          <span className="ico">{it.icon}</span>
          <span>{it.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
