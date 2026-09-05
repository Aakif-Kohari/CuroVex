"use client";

import Link from "next/link";
import { useAuth } from "../context/AuthContext";
import { useRouter } from "next/navigation";

export default function AuthNav() {
  const { isAuthenticated, email, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  if (isAuthenticated) {
    return (
      <div className="flex items-center space-x-4">
        <span className="text-sm text-slate-400">{email}</span>
        <button
          onClick={handleLogout}
          className="text-sm text-slate-300 hover:text-white transition-colors"
        >
          Logout
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-4 ml-4">
      <Link
        href="/login"
        className="text-sm text-slate-300 hover:text-white transition-colors"
      >
        Login
      </Link>
      <Link
        href="/register"
        className="text-sm text-slate-300 hover:text-white transition-colors"
      >
        Register
      </Link>
    </div>
  );
}
