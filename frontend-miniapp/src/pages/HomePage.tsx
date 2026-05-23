import { Link } from "react-router-dom";
import { Icon } from "@/components/Icon";
import { useAuth } from "@/auth/AuthProvider";
import { useI18n } from "@/i18n";

export function HomePage() {
  const { profile } = useAuth();
  const { t } = useI18n();
  const greeting = profile?.first_name ? `${t("home:main:greet")}, ${profile.first_name}!` : `${t("home:main:greeting")}!`;
  
  return (
    <div className="screen">
      <h1 className="screen-title">{greeting}</h1>
      <p className="screen-sub">{t("home:main:subtitle")}</p>

      <div className="tile-grid">
        <Tile to="/submissions" icon={<Icon.History />} title={t("home:main:my_submissions")} sub={t("home:main:my_submissions_sub")} />
        <Tile to="/services" icon={<Icon.Plus />} title={t("home:main:services")} sub={t("home:main:services_sub")} />
        <Tile to="/faq" icon={<Icon.FAQ />} title={t("home:main:faq")} sub={t("home:main:faq_sub")} />
        <Tile to="/profile" icon={<Icon.Profile />} title={t("home:main:profile")} sub={t("home:main:profile_sub")} />
      </div>
    </div>
  );
}

function Tile({
  to,
  icon,
  title,
  sub,
}: {
  to: string;
  icon: React.ReactNode;
  title: string;
  sub: string;
}) {
  return (
    <Link to={to} className="tile">
      <div className="tile-icon">
        <span className="ico" style={{ width: 20, height: 20 }}>
          {icon}
        </span>
      </div>
      <b>{title}</b>
      <small>{sub}</small>
    </Link>
  );
}
