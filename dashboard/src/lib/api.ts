import axios from "axios";
import {
  PredictionRun,
  ExplanationResponse,
  ValidationResult,
  TokenResponse,
} from "./types";
import { getToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const getPredictions = async (
  diseaseId: string,
  topK: number = 10,
): Promise<PredictionRun> => {
  const response = await api.get(`/predictions/${diseaseId}?top_k=${topK}`);
  return response.data;
};

export const getExplanations = async (
  predictionId: string,
): Promise<ExplanationResponse> => {
  const response = await api.get(`/explanations/${predictionId}`);
  return response.data;
};

export const getValidation = async (
  predictionId: string,
): Promise<ValidationResult> => {
  const response = await api.get(`/validation/${predictionId}`);
  return response.data;
};

export const registerUser = async (
  email: string,
  password: string,
): Promise<TokenResponse> => {
  const { data } = await api.post<TokenResponse>("/auth/register", {
    email,
    password,
  });
  return data;
};

export const loginUser = async (
  email: string,
  password: string,
): Promise<TokenResponse> => {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);
  const { data } = await api.post<TokenResponse>("/auth/login", formData, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
};

export default api;
