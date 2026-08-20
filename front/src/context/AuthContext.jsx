import { createContext, useContext, useState, useCallback, useEffect } from "react";
import authService from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  const applySession = useCallback(({ accessToken, user: nextUser }) => {
    localStorage.setItem("pedalup_access_token", accessToken);
    setUser(nextUser);
    setIsAuthenticated(true);
  }, []);

  useEffect(() => {
    const restoreSession = async () => {
      if (!localStorage.getItem("pedalup_access_token")) {
        setIsAuthLoading(false);
        return;
      }
      try {
        const restoredUser = await authService.getMe();
        setUser(restoredUser);
        setIsAuthenticated(true);
      } catch {
        authService.clearLocalSession();
      } finally {
        setIsAuthLoading(false);
      }
    };
    restoreSession();
  }, []);

  const login = useCallback(
    async (credentials) => {
      const session = await authService.login(credentials);
      applySession(session);
      return session;
    },
    [applySession]
  );

  const signup = useCallback(
    async (payload) => {
      const session = await authService.signup(payload);
      applySession(session);
      return session;
    },
    [applySession]
  );

  const loginWithGoogle = useCallback(async () => {
    const session = await authService.loginWithGoogle();
    applySession(session);
    return session;
  }, [applySession]);

  const loginWithKakao = useCallback(async () => {
    const session = await authService.loginWithKakao();
    applySession(session);
    return session;
  }, [applySession]);

  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  const updateProfile = useCallback(async (payload) => {
    const updatedUser = await authService.updateMe(payload);
    setUser(updatedUser);
    return updatedUser;
  }, []);

  const deleteAccount = useCallback(async (password) => {
    await authService.deleteMe(password);
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated, isAuthLoading, login, signup, loginWithGoogle, loginWithKakao, logout, updateProfile, deleteAccount }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
