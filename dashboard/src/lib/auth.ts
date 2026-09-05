export function saveSession(token: string, email: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("curovex_access_token", token);
    localStorage.setItem("curovex_user_email", email);
  }
}

export function clearSession(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("curovex_access_token");
    localStorage.removeItem("curovex_user_email");
  }
}

export function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("curovex_access_token");
  }
  return null;
}

export function getStoredEmail(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("curovex_user_email");
  }
  return null;
}
