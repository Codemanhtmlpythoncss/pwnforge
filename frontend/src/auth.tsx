import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api, User } from "./api";

interface AuthState {
  user: User | null;
  loading: boolean;
  initialised: boolean;
  registrationOpen: boolean;
  refresh: () => Promise<void>;
  login: (u: string, p: string) => Promise<void>;
  bootstrap: (u: string, p: string, name?: string) => Promise<void>;
  logout: () => Promise<void>;
}

const Ctx = createContext<AuthState>(null as any);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [initialised, setInit] = useState(true);
  const [registrationOpen, setReg] = useState(false);

  async function refresh() {
    try {
      const s = await api.get("/api/auth/status");
      setInit(s.initialised);
      setReg(s.registration_open);
      if (s.initialised) {
        try { setUser((await api.get("/api/auth/me")).user); }
        catch { setUser(null); }
      }
    } finally { setLoading(false); }
  }
  useEffect(() => { refresh(); }, []);

  const login = async (u: string, p: string) => {
    const r = await api.post("/api/auth/login", { username: u, password: p });
    setUser(r.user);
  };
  const bootstrap = async (u: string, p: string, name?: string) => {
    const r = await api.post("/api/auth/bootstrap", { username: u, password: p, display_name: name });
    setUser(r.user); setInit(true);
  };
  const logout = async () => { await api.post("/api/auth/logout"); setUser(null); };

  return (
    <Ctx.Provider value={{ user, loading, initialised, registrationOpen, refresh, login, bootstrap, logout }}>
      {children}
    </Ctx.Provider>
  );
}
