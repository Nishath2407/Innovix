import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    return api.me()
      .then((data) => { setUser(data.user); return data.user; })
      .catch(() => { setUser(null); return null; });
  }, []);

  useEffect(() => { refresh().finally(() => setLoading(false)); }, [refresh]);

  const login = async (email, password, portal = "user") => {
    const data = await api.login({ email, password, portal });
    setUser(data.user);
    return data.user;
  };

  const register = (payload) => api.register(payload);

  const logout = async () => {
    await api.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
