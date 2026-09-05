"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react";
import { loginUser, registerUser } from "../lib/api";
import {
  saveSession,
  clearSession,
  getStoredEmail,
  getToken,
} from "../lib/auth";

interface AuthContextValue {
  email: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    const token = getToken();
    const storedEmail = getStoredEmail();
    if (token && storedEmail) {
      setEmail(storedEmail);
      setIsAuthenticated(true);
    }
  }, []);

  const login = async (emailInput: string, passwordInput: string) => {
    const data = await loginUser(emailInput, passwordInput);
    saveSession(data.access_token, emailInput);
    setEmail(emailInput);
    setIsAuthenticated(true);
  };

  const register = async (emailInput: string, passwordInput: string) => {
    const data = await registerUser(emailInput, passwordInput);
    saveSession(data.access_token, emailInput);
    setEmail(emailInput);
    setIsAuthenticated(true);
  };

  const logout = () => {
    clearSession();
    setEmail(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{ email, isAuthenticated, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
