import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { api, getToken, setToken } from "@/api/client";
import type { Profile } from "@/api/types";
import { getStartParam, isInsideApp, ready } from "@/max/bridge";
import { useI18n, isLang } from '@/i18n';

interface AuthState {
  profile: Profile | null;
  loading: boolean;
  error: string | null;
  needsRedirect: string | null;
  insideMax: boolean;
  refresh: () => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthState | null>(null);

function readInitDataFromQuery(): string | null {
  const params = new URLSearchParams(window.location.search);
  return params.get("initData") || params.get("WebAppData") || null;
}

function cleanInitDataFromUrl(): void {
  const url = new URL(window.location.href);
  let changed = false;
  for (const key of ["initData", "WebAppData", "system"]) {
    if (url.searchParams.has(key)) {
      url.searchParams.delete(key);
      changed = true;
    }
  }
  if (changed) {
    window.history.replaceState({}, "", url.toString());
  }
}

const WEBAPP_URL: string = import.meta.env.VITE_WEBAPP_URL || "";
const SITE_URL: string = import.meta.env.VITE_SITE_URL || "";;


export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [needsRedirect, setNeedsRedirect] = useState<string | null>(null);
  const systemQuery: string | null = new URLSearchParams(window.location.search).get("system");
  const system: string = systemQuery || "max";
  const {setLang} = useI18n();
  const insideMax = isInsideApp();
  const triedRef = useRef(false);

  const fetchMe = useCallback(async () => {
    if (!getToken()) return false;
    try {
      const me = await api.get<{ role: string; user?: Profile }>("/auth/me");
      if (me?.user) {
        const lang = me.user?.language_code ?? 'ru';
  
        if (isLang(lang)) {
          setLang(lang);
        }
        setProfile(me.user);
        return true;
      }
    } catch {
      // токен невалидный — продолжим попытку авторизации через initData
    }
    setToken(null);
    return false;
  }, []);

  const authenticateWithInitData = useCallback(
    async (initData: string): Promise<boolean> => {
      
      try {
        const res = await api.post<{
          token: { access_token: string };
          user: Profile;
        }>("/auth/init-data/validate", { initData, system });
        setToken(res.token.access_token);
        setProfile(res.user);
        return true;
      } catch (e) {
        setError((e as Error)?.message ?? "Не удалось войти");
        return false;
      }
    },
    [],
  );

  useEffect(() => {
    if (triedRef.current) return;
    triedRef.current = true;
    ready();

    void (async () => {
      try {

        const startParam = getStartParam();
        console.log("Start param:", startParam, "insideMax:", insideMax, "system:", system, SITE_URL);
        if (startParam === "admin_login" && SITE_URL) {
          const initData = window.WebApp?.initData ?? "";
          const target = `${SITE_URL}/login?system=${system}#initData=${encodeURIComponent(initData)}`;
          setNeedsRedirect(target);
          setLoading(false);
          return;
        }

        if (startParam === "student_login" && WEBAPP_URL) {
          const initData = window.WebApp?.initData ?? "";
          const target = new URL(WEBAPP_URL);
          target.searchParams.set("initData", initData);
          target.searchParams.set("system", system);
          window.location.replace(target.toString());
          return;
        }

        if (await fetchMe()) {
          setLoading(false);
          return;
        }

        const fromQuery = readInitDataFromQuery();
        if (fromQuery) {
          const ok = await authenticateWithInitData(fromQuery);
          cleanInitDataFromUrl();
          if (ok) {
            setLoading(false);
            return;
          }
        }

        if (insideMax) {
          const initData = window.WebApp?.initData ?? "";
          const ok = await authenticateWithInitData(initData);
          if (!ok) setError((prev) => prev ?? "Не удалось войти");
          setLoading(false);
          return;
        }

        // 5) Standalone и нет initData — нужен явный логин.
        setLoading(false);
      } catch (e) {
        setError((e as Error)?.message ?? "Ошибка авторизации");
        setLoading(false);
      }
    })();
  }, [authenticateWithInitData, fetchMe, insideMax]);

  const logout = useCallback(() => {
    setToken(null);
    setProfile(null);
  }, [insideMax]);

  const refresh = useCallback(async () => {
    await fetchMe();
  }, [fetchMe]);

  const value = useMemo<AuthState>(
    () => ({ profile, loading, error, insideMax, refresh, logout, needsRedirect }),
    [profile, loading, error, insideMax, refresh, logout, needsRedirect],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth used outside AuthProvider");
  return v;
}
