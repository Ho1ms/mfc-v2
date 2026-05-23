import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "@/auth/AuthProvider";
import { Topbar } from "@/components/Topbar";
import { BottomNav } from "@/components/BottomNav";
import { HomePage } from "@/pages/HomePage";
import { SubmissionsPage } from "@/pages/SubmissionsPage";
import { SubmitPage } from "@/pages/SubmitPage";
import { ServicesPage } from "@/pages/ServicesPage";
import { FaqPage } from "@/pages/FaqPage";
import { ProfilePage } from "@/pages/ProfilePage";
import { openLink, setupBackButton, getWebApp } from "@/max/bridge";

export function App() {
  const { profile, loading, error, insideMax, needsRedirect } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const onRoot = location.pathname === "/";
    setupBackButton(!onRoot, () => navigate(-1));
  }, [location.pathname, navigate]);

  if (needsRedirect) {
    return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 16,
        background: "linear-gradient(180deg, var(--brand-50) 0%, var(--bg) 100%)",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 380,
          background: "var(--card)",
          border: "1px solid var(--line)",
          borderRadius: 20,
          boxShadow: "var(--shadow)",
          padding: "36px 24px 28px",
          textAlign: "center",
        }}
      >
        <img src="logo-miit.png" style={{ width: "100%", height: "100%", objectFit: "contain" }} />
       
        <p style={{ margin: "0 0 24px", color: "var(--ink-400)", fontSize: 13 }}>
          Подтвердите вход в админ-панель МФЦ.
        </p>
        <button className="btn btn-primary"  onClick={() => {
          openLink(needsRedirect);
          getWebApp()?.close?.();
        }}>
          Авторизоваться в панели
        </button>
        
      </div>
    </div>
  );
  }

  if (loading) {
    return (
      <>
        <Topbar />
        <div className="screen">
          <div className="skeleton" style={{ width: "60%", height: 28 }} />
          <div style={{ marginTop: 12 }}>
            <div className="skeleton" style={{ width: "100%", height: 80 }} />
          </div>
        </div>
      </>
    );
  }


  if (error || !profile) {
    return (
      <>
        <Topbar />
        <div className="screen" style={{ textAlign: "center", padding: 32 }}>
          <h1 className="screen-title" style={{ marginTop: 32 }}>
            Не удалось войти
          </h1>
          <p style={{ color: "var(--ink-500)", fontSize: 14 }}>
            {error ??
              (insideMax
                ? "Авторизация недоступна. Откройте мини-приложение из чата MAX."
                : "Авторизация недоступна. Попробуйте обновить страницу.")}
          </p>
        </div>
      </>
    );
  }

  if (profile.ban_app) {
    return (
      <div
        style={{
          minHeight: "100vh",
          background: "#b91c1c",
          color: "#fff",
          display: "grid",
          placeItems: "center",
          padding: 24,
          textAlign: "center",
        }}
      >
        <div style={{ maxWidth: 420 }}>
          <h1 style={{ fontSize: 24, margin: "0 0 12px" }}>Доступ к приложению заблокирован</h1>
          <p style={{ fontSize: 14, lineHeight: 1.5, opacity: 0.95 }}>
            {profile.ban_app_reason ||
              "Если вы считаете это ошибкой — обратитесь в МФЦ РУТ МИИТ лично."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <Topbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/services" element={<ServicesPage />} />
        <Route path="/submissions" element={<SubmissionsPage />} />
        <Route path="/submit/:formId" element={<SubmitPage />} />
        {/* /monitoring оставляем как alias на /services для совместимости со старыми пушами */}
        <Route path="/monitoring" element={<Navigate to="/services" replace />} />
        <Route path="/faq" element={<FaqPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <BottomNav />
    </>
  );
}
