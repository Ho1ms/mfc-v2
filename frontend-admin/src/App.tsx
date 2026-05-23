import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "@/auth/AuthProvider";
import { Layout } from "@/components/Layout";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { SubmissionsPage } from "@/pages/SubmissionsPage";
import { TicketsPage } from "@/pages/TicketsPage";
import { UsersPage } from "@/pages/UsersPage";
import { BuilderPage } from "@/pages/BuilderPage";
import { AdminsPage } from "@/pages/AdminsPage";
import { BotSettingsPage } from "@/pages/BotSettingsPage";
import { FaqPage } from "@/pages/FaqPage";
import { KbPage } from "@/pages/KbPage";

function Guard({ children }: { children: React.ReactNode }) {
  const { admin, loading } = useAuth();
  if (loading) {
    return (
      <div style={{ padding: 32, color: "var(--ink-400)" }}>
        Загрузка… / Loading…
      </div>
    );
  }
  if (!admin) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AdminOnly({ children }: { children: React.ReactNode }) {
  const { admin } = useAuth();
  if (admin?.role !== "admin") return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <Guard>
            <Layout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/submissions" element={<SubmissionsPage />} />
                <Route path="/tickets" element={<TicketsPage />} />
                <Route path="/users" element={<UsersPage />} />
                <Route
                  path="/builder"
                  element={
                    <AdminOnly>
                      <BuilderPage />
                    </AdminOnly>
                  }
                />
                <Route
                  path="/admins"
                  element={
                    <AdminOnly>
                      <AdminsPage />
                    </AdminOnly>
                  }
                />
                <Route
                  path="/bot-settings"
                  element={
                    <AdminOnly>
                      <BotSettingsPage />
                    </AdminOnly>
                  }
                />
                <Route
                  path="/faq"
                  element={
                    <AdminOnly>
                      <FaqPage />
                    </AdminOnly>
                  }
                />
                <Route
                  path="/kb"
                  element={
                    <AdminOnly>
                      <KbPage />
                    </AdminOnly>
                  }
                />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </Layout>
          </Guard>
        }
      />
    </Routes>
  );
}
